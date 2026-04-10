"""
Local API that bridges the Chrome extension to the Claude /run pipeline.

POST /run            -> writes tasks/{date}/{id}/inputs.md and triggers `claude -p "/run {id}"`
GET  /run/status/<id>-> returns running/done/error + parsed deliverables
DELETE /task/<id>    -> removes the task folder
"""
import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # code-review/
TASKS_DIR = PROJECT_ROOT / "tasks"
REVIEWS_DIR = PROJECT_ROOT / "reviews"

jobs = {}  # task_id -> {"status": running|done|error, "error": ..., "deliverables": ...}

VARS = [
    "pull_request_url", "nwo", "head_sha", "comment_id", "body",
    "file_path", "diff_line", "discussion_url", "repo_url", "coding_language",
]


# ---------- Helpers ----------

def date_folder():
    return datetime.now().strftime("%Y-%m-%d")


def find_task_dir(task_id):
    if not TASKS_DIR.is_dir():
        return None
    for date_dir in sorted(TASKS_DIR.iterdir(), reverse=True):
        candidate = date_dir / task_id
        if candidate.is_dir():
            return candidate
    return None


def find_review_dir(task_id):
    """Find a /review workspace under reviews/. Reviews never live under tasks/."""
    if REVIEWS_DIR.is_dir():
        for date_dir in sorted(REVIEWS_DIR.iterdir(), reverse=True):
            candidate = date_dir / task_id
            if candidate.is_dir():
                return candidate
    return None


def write_inputs_md(task_dir, data):
    """Write inputs.md in the format that the /run skill (step-01-parse-inputs) expects."""
    lines = ["# Task Inputs", "", "## Task Variables", ""]
    for v in VARS:
        lines.append(f"- **{v}:** {data.get(v, '')}")
    lines.append("")
    (task_dir / "inputs.md").write_text("\n".join(lines), encoding="utf-8")


DEFAULT_MODEL = "claude-opus-4-6"


def run_claude(task_id, label="RUN", command="run", mode="auto", model=None):
    clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    model = model or DEFAULT_MODEL
    cmd = [
        "claude", "-p", f"/{command} {task_id} {mode}",
        "--model", model,
        "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep",
    ]
    print(f"[{label}] {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True,
            timeout=900, env=clean_env,
        )
    except subprocess.TimeoutExpired:
        return False, {"error": f"{label} timed out (15 min)"}
    except FileNotFoundError:
        return False, {"error": "claude CLI not found in PATH"}
    if result.returncode != 0:
        return False, {"error": f"{label} failed", "stderr": (result.stderr or "")[:2000]}
    return True, result


def parse_quality_or_severity_or_advanced(text, axis_num):
    """Extract {label, reasoning} from a deliverable .md (Axis 1, 2 or 4)."""
    if not text:
        return {"label": "", "reasoning": ""}
    # Find a line that is just one of the known labels
    lines = [l.strip() for l in text.splitlines()]
    label_sets = {
        1: {"helpful", "unhelpful", "wrong"},
        2: {"nit", "moderate", "critical"},
        4: {"repo-specific conventions", "context outside changed files",
            "recent language/library updates", "better implementation approach", "false"},
    }
    labels = label_sets.get(axis_num, set())
    label = ""
    label_idx = -1
    for i, l in enumerate(lines):
        clean = l.strip().strip("*_`").strip().lower()
        if clean in labels:
            label = clean
            label_idx = i
            break
    # Reasoning = everything after a "Reasoning" or "Justification" heading
    reasoning = ""
    for i in range(label_idx + 1, len(lines)):
        low = lines[i].lower()
        if "reasoning" in low or "justification" in low:
            reasoning = "\n".join(lines[i + 1:]).strip()
            break
    return {"label": label, "reasoning": reasoning}


def parse_context_scope(text):
    """Extract {label, entries[]} from context_scope.md."""
    if not text:
        return {"label": "", "entries": []}
    lines = [l.rstrip() for l in text.splitlines()]
    labels = {"diff", "file", "repo", "external"}
    label = ""
    table_start = -1
    for i, l in enumerate(lines):
        clean = l.strip().strip("*_`").strip().lower()
        if not label and clean in labels:
            label = clean
        s = l.strip().lower()
        if "diff_line" in s and "file_path" in s and "why" in s:
            table_start = i
            break

    entries = []
    if table_start >= 0:
        i = table_start + 1
        # Skip markdown separator lines like |---|---|---|
        while i < len(lines) and re.match(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", lines[i]):
            i += 1

        # Detect format: pipe-table vs platform copy-paste (tabs / one cell per line)
        first_row = next((lines[j].strip() for j in range(i, len(lines)) if lines[j].strip()), "")
        if first_row.startswith("|"):
            # Pipe-table format: | diff_line | file_path | why |
            while i < len(lines):
                row = lines[i].strip()
                if not row or not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip("|").split("|")]
                if len(cells) >= 3:
                    entries.append({
                        "diff_line": cells[0],
                        "file_path": cells[1],
                        "why": "|".join(cells[2:]).strip(),
                    })
                i += 1
        else:
            # Platform copy-paste format: each row is 4 consecutive non-empty
            # lines (row#, diff_line, file_path, why). Group them.
            buf = []
            while i < len(lines):
                row = lines[i].strip()
                if not row:
                    i += 1
                    continue
                # New entry starts with a numeric row index
                if re.match(r"^\d+$", row) and len(buf) == 0:
                    buf.append(row)
                elif buf:
                    buf.append(row)
                if len(buf) == 4:
                    _, diff_line, file_path, why = buf
                    entries.append({
                        "diff_line": diff_line,
                        "file_path": file_path,
                        "why": why,
                    })
                    buf = []
                i += 1
    return {"label": label, "entries": entries}


def read_deliverables(task_dir):
    d = task_dir / "deliverables"
    if not d.is_dir():
        return None
    files = {
        "quality": d / "quality.md",
        "severity": d / "severity.md",
        "context_scope": d / "context_scope.md",
        "advanced": d / "advanced.md",
    }
    if not all(p.is_file() and p.stat().st_size > 0 for p in files.values()):
        return None
    return {
        "quality": parse_quality_or_severity_or_advanced(files["quality"].read_text(encoding="utf-8"), 1),
        "severity": parse_quality_or_severity_or_advanced(files["severity"].read_text(encoding="utf-8"), 2),
        "context_scope": parse_context_scope(files["context_scope"].read_text(encoding="utf-8")),
        "advanced": parse_quality_or_severity_or_advanced(files["advanced"].read_text(encoding="utf-8"), 4),
    }


# ---------- Routes ----------

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"ok": True})


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    # Already labeled?
    existing = find_task_dir(task_id)
    if existing:
        deliv = read_deliverables(existing)
        if deliv:
            return jsonify({"status": "done", "deliverables": deliv})

    # Already running?
    if task_id in jobs and jobs[task_id]["status"] == "running":
        return jsonify({"status": "running"})

    # Create task dir + inputs.md
    task_dir = existing or (TASKS_DIR / date_folder() / task_id)
    (task_dir / "deliverables").mkdir(parents=True, exist_ok=True)
    (task_dir / "work").mkdir(parents=True, exist_ok=True)
    write_inputs_md(task_dir, data)

    model = data.get("model")
    jobs[task_id] = {"status": "running", "error": None, "deliverables": None}
    threading.Thread(target=_worker, args=(task_id, task_dir, model), daemon=True).start()
    return jsonify({"status": "running"})


def _worker(task_id, task_dir, model=None):
    try:
        ok, result = run_claude(task_id, model=model)
        if not ok:
            jobs[task_id] = {"status": "error", "error": result.get("error"), "deliverables": None}
            return
        deliv = read_deliverables(task_dir)
        if not deliv:
            jobs[task_id] = {
                "status": "error",
                "error": "Pipeline finished but deliverables are missing or empty",
                "deliverables": None,
            }
            return
        jobs[task_id] = {"status": "done", "error": None, "deliverables": deliv}
        print(f"[RUN] Done: {task_id}")
    except Exception as e:
        jobs[task_id] = {"status": "error", "error": str(e), "deliverables": None}
        print(f"[RUN] CRASH {task_id}: {e}")


@app.route("/run/status/<task_id>", methods=["GET"])
def run_status(task_id):
    # Filesystem wins over the in-memory cache.
    task_dir = find_task_dir(task_id)
    if task_dir:
        deliv = read_deliverables(task_dir)
        if deliv:
            jobs.pop(task_id, None)
            return jsonify({"status": "done", "deliverables": deliv})
    if task_id in jobs:
        job = jobs[task_id]
        if job["status"] == "running":
            return jsonify({"status": "running"})
        if job["status"] == "error":
            return jsonify({"status": "error", "error": job["error"]})
    return jsonify({"status": "not_found"})


@app.route("/task/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_dir = find_task_dir(task_id)
    if not task_dir:
        return jsonify({"error": "not found"}), 404
    shutil.rmtree(task_dir)
    jobs.pop(task_id, None)
    return jsonify({"ok": True})


# ---------- Review ----------

review_jobs = {}  # task_id -> {"status": running|done|error, "error": ..., "result": ...}


def _platform_axis_md(label, reasoning, axis_title, justification_label):
    return f"{label}\n{axis_title}\n{reasoning}\n"


def write_review_workspace(review_dir, data):
    """Materialize inputs.md + deliverables/*.md from scraped page data."""
    (review_dir / "deliverables").mkdir(parents=True, exist_ok=True)
    (review_dir / "work").mkdir(parents=True, exist_ok=True)
    write_inputs_md(review_dir, data)

    deliv = data.get("current") or {}
    q = deliv.get("quality") or {}
    s = deliv.get("severity") or {}
    c = deliv.get("context_scope") or {}
    a = deliv.get("advanced") or {}

    (review_dir / "deliverables" / "quality.md").write_text(
        f"{q.get('label','')}\nAxis 1: Quality Justification *\n{q.get('reasoning','')}\n",
        encoding="utf-8")
    (review_dir / "deliverables" / "severity.md").write_text(
        f"{s.get('label','')}\nAxis 2: Severity Justification *\n{s.get('reasoning','')}\n",
        encoding="utf-8")

    rows = "\n".join(
        f"{i+1}\n{e.get('diff_line','')}\n{e.get('file_path','')}\n{e.get('why','')}"
        for i, e in enumerate(c.get("entries") or [])
    )
    (review_dir / "deliverables" / "context_scope.md").write_text(
        f"{c.get('label','')}\nAxis 3: Context\n\n#\tdiff_line\tfile_path\twhy\n{rows}\n",
        encoding="utf-8")

    (review_dir / "deliverables" / "advanced.md").write_text(
        f"{a.get('label','')}\nAxis 4: Advanced Justification\n{a.get('reasoning','')}\n",
        encoding="utf-8")


def _parse_platform_axis_md(text, axis_num):
    """Parse a platform-format file (label on line 1, then heading, then reasoning)."""
    if not text:
        return {"label": "", "reasoning": ""}
    lines = text.splitlines()
    label = lines[0].strip().strip("*_`").strip() if lines else ""
    reasoning = ""
    for i in range(1, len(lines)):
        if "justification" in lines[i].lower() or "reasoning" in lines[i].lower():
            reasoning = "\n".join(lines[i + 1:]).strip()
            break
    return {"label": label, "reasoning": reasoning}


def read_fixed_deliverables(review_dir):
    """Read fixed_deliverables/*.md (platform format) if present."""
    fd = review_dir / "fixed_deliverables"
    if not fd.is_dir():
        return {}
    out = {}
    if (fd / "quality.md").is_file():
        out["quality"] = _parse_platform_axis_md((fd / "quality.md").read_text(encoding="utf-8"), 1)
    if (fd / "severity.md").is_file():
        out["severity"] = _parse_platform_axis_md((fd / "severity.md").read_text(encoding="utf-8"), 2)
    if (fd / "advanced.md").is_file():
        out["advanced"] = _parse_platform_axis_md((fd / "advanced.md").read_text(encoding="utf-8"), 4)
    if (fd / "context_scope.md").is_file():
        out["context_scope"] = parse_context_scope((fd / "context_scope.md").read_text(encoding="utf-8"))
    return out


def read_review_outputs(review_dir):
    """Return {feedback, fixed, quality_score, feedback_text} or None if review hasn't finished."""
    fb = review_dir / "feedback_to_cb.md"
    if not fb.is_file() or fb.stat().st_size == 0:
        return None
    feedback_md = fb.read_text(encoding="utf-8")
    quality_score = None
    feedback_text = feedback_md
    meta_path = review_dir / "review_meta.json"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            quality_score = meta.get("quality_score")
            if meta.get("feedback_text"):
                feedback_text = meta["feedback_text"]
        except Exception:
            pass
    # Strip markdown so the textarea gets plain prose:
    #   - drop heading lines (#, ##, ###)
    #   - unwrap blockquote prefixes ("> " -> "")
    #   - collapse 3+ consecutive blank lines
    cleaned = []
    for line in feedback_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith("> "):
            line = stripped[2:]
        elif stripped == ">":
            line = ""
        cleaned.append(line)
    feedback_text = "\n".join(cleaned).strip()
    feedback_text = re.sub(r"\n{3,}", "\n\n", feedback_text)
    # Single source of truth: `feedback` is the cleaned plain-text version
    # that the extension both displays and pastes into the platform textarea.
    return {
        "feedback": feedback_text,
        "fixed": read_fixed_deliverables(review_dir),
        "quality_score": quality_score,
    }


@app.route("/review", methods=["POST"])
def review():
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    reevaluate = bool(data.get("reevaluate"))
    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    existing = find_review_dir(task_id)

    model = data.get("model")

    if reevaluate:
        if not existing or not read_review_outputs(existing):
            return jsonify({"error": "no existing review to reevaluate"}), 400
        review_jobs.pop(task_id, None)
        review_jobs[task_id] = {"status": "running", "error": None, "result": None}
        threading.Thread(target=_review_worker, args=(task_id, existing, "reevaluate", model), daemon=True).start()
        return jsonify({"status": "running"})

    # Idempotency: feedback already exists?
    if existing:
        out = read_review_outputs(existing)
        if out:
            return jsonify({"status": "done", **out})

    if task_id in review_jobs and review_jobs[task_id]["status"] == "running":
        return jsonify({"status": "running"})

    review_dir = existing or (REVIEWS_DIR / date_folder() / task_id)
    write_review_workspace(review_dir, data)

    review_jobs[task_id] = {"status": "running", "error": None, "result": None}
    threading.Thread(target=_review_worker, args=(task_id, review_dir, "auto", model), daemon=True).start()
    return jsonify({"status": "running"})


def _review_worker(task_id, review_dir, mode="auto", model=None):
    try:
        ok, result = run_claude(task_id, label="REVIEW", command="review", mode=mode, model=model)
        if not ok:
            review_jobs[task_id] = {"status": "error", "error": result.get("error"), "result": None}
            return
        out = read_review_outputs(review_dir)
        if not out:
            review_jobs[task_id] = {
                "status": "error",
                "error": "Review finished but feedback_to_cb.md is missing or empty",
                "result": None,
            }
            return
        review_jobs[task_id] = {"status": "done", "error": None, "result": out}
        print(f"[REVIEW] Done: {task_id}")
    except Exception as e:
        review_jobs[task_id] = {"status": "error", "error": str(e), "result": None}
        print(f"[REVIEW] CRASH {task_id}: {e}")


@app.route("/review/status/<task_id>", methods=["GET"])
def review_status(task_id):
    # Filesystem wins over the in-memory cache: if the artifacts are on disk
    # the review is done, regardless of any stale "error" job state.
    review_dir = find_review_dir(task_id)
    if review_dir:
        out = read_review_outputs(review_dir)
        if out:
            review_jobs.pop(task_id, None)
            return jsonify({"status": "done", **out})
    if task_id in review_jobs:
        job = review_jobs[task_id]
        if job["status"] == "running":
            return jsonify({"status": "running"})
        if job["status"] == "error":
            return jsonify({"status": "error", "error": job["error"]})
    return jsonify({"status": "not_found"})


@app.route("/state/<task_id>", methods=["GET"])
def state(task_id):
    """Combined snapshot for the extension's Status panel."""
    out = {"task_id": task_id, "run": None, "review": None}

    # /run state
    run_dir = find_task_dir(task_id)
    run_block = {"present": bool(run_dir), "status": "not_found", "progress": None}
    if run_dir:
        prog = run_dir / "progress.md"
        if prog.is_file():
            run_block["progress"] = prog.read_text(encoding="utf-8")
        deliv = read_deliverables(run_dir)
        if deliv:
            run_block["status"] = "done"
        elif task_id in jobs and jobs[task_id]["status"] == "running":
            run_block["status"] = "running"
        elif task_id in jobs and jobs[task_id]["status"] == "error":
            run_block["status"] = "error"
            run_block["error"] = jobs[task_id]["error"]
        else:
            run_block["status"] = "incomplete"
    elif task_id in jobs and jobs[task_id]["status"] == "running":
        run_block["status"] = "running"
    out["run"] = run_block

    # /review state
    review_dir = None
    if REVIEWS_DIR.is_dir():
        for d in sorted(REVIEWS_DIR.iterdir(), reverse=True):
            cand = d / task_id
            if cand.is_dir():
                review_dir = cand
                break
    review_block = {"present": bool(review_dir), "status": "not_found", "progress": None}
    if review_dir:
        rprog = review_dir / "review_progress.md"
        if rprog.is_file():
            review_block["progress"] = rprog.read_text(encoding="utf-8")
        if (review_dir / "feedback_to_cb.md").is_file() and (review_dir / "feedback_to_cb.md").stat().st_size > 0:
            review_block["status"] = "done"
        elif task_id in review_jobs and review_jobs[task_id]["status"] == "running":
            review_block["status"] = "running"
        elif task_id in review_jobs and review_jobs[task_id]["status"] == "error":
            review_block["status"] = "error"
            review_block["error"] = review_jobs[task_id]["error"]
        else:
            review_block["status"] = "incomplete"
    elif task_id in review_jobs and review_jobs[task_id]["status"] == "running":
        review_block["status"] = "running"
    out["review"] = review_block

    return jsonify(out)


# ---------- Recheck ----------

recheck_jobs = {}  # task_id -> {"status": running|done|error, "error": ..., "report": ...}


@app.route("/recheck", methods=["POST"])
def recheck():
    data = request.get_json(force=True) or {}
    task_id = data.get("task_id", "").strip()
    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    if task_id in recheck_jobs and recheck_jobs[task_id]["status"] == "running":
        return jsonify({"status": "running"})

    # Determine mode: review-mode if fixed_deliverables/ exist, run-mode otherwise
    task_dir = find_task_dir(task_id)
    review_dir = find_review_dir(task_id)
    mode = "auto"
    if review_dir and (review_dir / "fixed_deliverables").is_dir():
        mode = "review auto"
    elif task_dir and (task_dir / "fixed_deliverables").is_dir():
        mode = "review auto"

    model = data.get("model")
    recheck_jobs[task_id] = {"status": "running", "error": None, "report": None}
    threading.Thread(
        target=_recheck_worker, args=(task_id, mode, model), daemon=True
    ).start()
    return jsonify({"status": "running"})


def _recheck_worker(task_id, mode, model=None):
    try:
        ok, result = run_claude(
            task_id, label="RECHECK", command="step-09-recheck", mode=mode, model=model
        )
        if not ok:
            recheck_jobs[task_id] = {
                "status": "error",
                "error": result.get("error"),
                "report": None,
            }
            return
        # Read recheck_report.md
        report = None
        for base in [find_task_dir(task_id), find_review_dir(task_id)]:
            if base and (base / "recheck_report.md").is_file():
                report = (base / "recheck_report.md").read_text(encoding="utf-8")
                break
        passed = result.stdout and "RECHECK_PASSED" in result.stdout
        recheck_jobs[task_id] = {
            "status": "done",
            "error": None,
            "report": report,
            "passed": passed,
        }
        print(f"[RECHECK] Done: {task_id} — {'PASSED' if passed else 'FAILED'}")
    except Exception as e:
        recheck_jobs[task_id] = {"status": "error", "error": str(e), "report": None}
        print(f"[RECHECK] CRASH {task_id}: {e}")


@app.route("/recheck/status/<task_id>", methods=["GET"])
def recheck_status(task_id):
    if task_id in recheck_jobs:
        job = recheck_jobs[task_id]
        return jsonify(job)
    # Check for an existing report on disk
    for base in [find_task_dir(task_id), find_review_dir(task_id)]:
        if base and (base / "recheck_report.md").is_file():
            report = (base / "recheck_report.md").read_text(encoding="utf-8")
            passed = "0 failures" in report
            return jsonify({"status": "done", "report": report, "passed": passed})
    return jsonify({"status": "not_found"})


if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"TASKS_DIR:    {TASKS_DIR}")
    app.run(host="127.0.0.1", port=5002, debug=True)
