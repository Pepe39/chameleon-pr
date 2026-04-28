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

_state_lock = threading.Lock()  # guards jobs / review_jobs / recheck_jobs
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
            timeout=1200, env=clean_env,
        )
    except subprocess.TimeoutExpired:
        return False, {"error": f"{label} timed out (20 min)"}
    except FileNotFoundError:
        return False, {"error": "claude CLI not found in PATH"}
    if result.returncode != 0:
        return False, {"error": f"{label} failed", "stderr": (result.stderr or "")[:2000]}
    return True, result


def parse_axis_md(text, axis_kind):
    """Extract {label, reasoning} from a deliverable .md.

    `axis_kind` is one of 'quality', 'addressed', 'severity', 'advanced'.
    Each kind has its own enum of valid labels. The function tolerates both
    forms of the Advanced enum slash spacing because some platform copies use
    "Recent language/library updates" while the canonical form has spaces.
    """
    if not text:
        return {"label": "", "reasoning": ""}
    lines = [l.strip() for l in text.splitlines()]
    label_sets = {
        "quality":   {"helpful", "unhelpful", "wrong"},
        "addressed": {"empty", "addressed", "ignored", "false_positive"},
        "severity":  {"nit", "moderate", "critical"},
        "advanced":  {"repo-specific conventions", "context outside changed files",
                      "recent language / library updates", "recent language/library updates",
                      "better implementation approach", "false"},
    }
    # Canonical-case map. Platform validator is case-sensitive. FALSE is all
    # uppercase per dataset convention, the four beyond-diff values are mixed
    # case starting with capital. Recent language/library updates uses NO
    # spaces around the slash. The lowercase set above is for matching only.
    advanced_canonical = {
        "false": "FALSE",
        "repo-specific conventions": "Repo-specific conventions",
        "context outside changed files": "Context outside changed files",
        "recent language/library updates": "Recent language/library updates",
        "recent language / library updates": "Recent language/library updates",
        "better implementation approach": "Better implementation approach",
    }
    labels = label_sets.get(axis_kind, set())
    label = ""
    label_idx = -1
    for i, l in enumerate(lines):
        clean = l.strip().strip("*_`").strip().lower()
        if clean in labels:
            label = clean
            label_idx = i
            break
    # Map matched lowercase form to the platform's canonical case for Advanced
    if axis_kind == "advanced" and label in advanced_canonical:
        label = advanced_canonical[label]
    # Reasoning = everything after a "Reasoning" or "Justification" heading
    reasoning = ""
    for i in range(label_idx + 1, len(lines)):
        low = lines[i].lower()
        if "reasoning" in low or "justification" in low:
            reasoning = "\n".join(lines[i + 1:]).strip()
            break
    return {"label": label, "reasoning": reasoning}


# Back-compat shim. Old call sites used axis numbers (1, 2, 4) under the old
# 4-axis layout where Severity was Axis 2 and Advanced was Axis 4. The new
# layout adds Addressed at Axis 2 and shifts Severity to 3, Context to 4,
# Advanced to 5. Keep the shim so external callers do not break.
def parse_quality_or_severity_or_advanced(text, axis_num):
    kind_map = {1: "quality", 2: "severity", 4: "advanced", 3: "severity", 5: "advanced"}
    return parse_axis_md(text, kind_map.get(axis_num, "quality"))


def parse_context_scope(text):
    """Extract {label, entries[]} from context_scope.md.

    Accepts three formats for the entries block:

    1. Markdown pipe-table.       `| diff_line | file_path | why |`
    2. Platform copy-paste.       Each row laid out as 4 plain lines
       (row index, diff_line, file_path, why).
    3. JSON code block.           Fenced ```json containing an array
       of {diff_line, file_path, why} objects.

    The parser tries the JSON form first (cheapest and unambiguous when
    present), then falls back to the table-header search used by formats
    1 and 2.
    """
    if not text:
        return {"label": "", "entries": []}
    lines = [l.rstrip() for l in text.splitlines()]
    labels = {"diff", "file", "repo", "external"}
    label = ""
    for i, l in enumerate(lines):
        clean = l.strip().strip("*_`").strip().lower()
        if not label and clean in labels:
            label = clean
            break

    # Format 3: ```json ... ``` block holding an array of context entries.
    json_block = re.search(r"```(?:json)?\s*\n(\[[\s\S]*?\])\s*\n```", text)
    if json_block:
        try:
            arr = json.loads(json_block.group(1))
            entries = []
            for e in arr:
                if not isinstance(e, dict):
                    continue
                dl = e.get("diff_line")
                fp = e.get("file_path", "")
                wy = e.get("why", "")
                if dl is None:
                    dl_str = ""
                else:
                    dl_str = str(dl)
                if dl_str or fp or wy:
                    entries.append({
                        "diff_line": dl_str,
                        "file_path": str(fp) if fp is not None else "",
                        "why": str(wy) if wy is not None else "",
                    })
            if entries:
                return {"label": label, "entries": entries}
        except (json.JSONDecodeError, ValueError):
            pass

    # Formats 1 and 2: locate the `diff_line file_path why` header row.
    table_start = -1
    for i, l in enumerate(lines):
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
            # Platform copy-paste format: each row is exactly 4 lines
            # (row_index, diff_line, file_path, why). diff_line may be blank
            # for files NOT in the PR diff. Blank lines must NOT be skipped
            # (they carry the empty diff_line slot). Once a row_index line
            # is found, consume the next 3 lines as the entry's fields
            # verbatim; do not treat subsequent lines as new row_index
            # candidates, since a diff_line like "4" also looks like one.
            while i < len(lines):
                if re.match(r"^\d+$", lines[i].strip()):
                    diff_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    file_path = lines[i + 2].strip() if i + 2 < len(lines) else ""
                    why = lines[i + 3].strip() if i + 3 < len(lines) else ""
                    # Guard: if all three fields are empty, the row_index was
                    # likely a stray number, not a real entry.
                    if diff_line or file_path or why:
                        entries.append({
                            "diff_line": diff_line,
                            "file_path": file_path,
                            "why": why,
                        })
                    i += 4
                else:
                    i += 1
    return {"label": label, "entries": entries}


def read_skip_flag(task_dir):
    """Return {"reason": str} if skip_flag.md exists, else None.

    Contract: step-02 section 2d writes skip_flag.md at the task root when the
    comment references another comment (not code). The file is the signal that
    the pipeline deliberately stopped. The API surfaces this as a "skipped"
    status so the extension can tell the attempter to release the task on the
    platform.

    The extracted `reason` is the plain-text content of the `Reason:` line for
    the extension banner. If the marker is missing, fall back to the first
    non-heading, non-empty line of the file.
    """
    p = task_dir / "skip_flag.md"
    if not p.is_file():
        return None
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return None
    reason = ""
    for line in text.splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith("**reason:**") or low.startswith("reason:"):
            reason = re.sub(r"(?i)^\*{0,2}reason:\*{0,2}\s*", "", s).strip()
            break
    if not reason:
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                reason = s
                break
    return {"reason": reason or text.strip()}


def read_deliverables(task_dir):
    """Read all axis deliverables. Addressed is only included when the
    pipeline produced `addressed.md`, which only happens on merged PRs."""
    d = task_dir / "deliverables"
    if not d.is_dir():
        return None
    required = {
        "quality": d / "quality.md",
        "severity": d / "severity.md",
        "context_scope": d / "context_scope.md",
        "advanced": d / "advanced.md",
    }
    if not all(p.is_file() and p.stat().st_size > 0 for p in required.values()):
        return None
    out = {
        "quality": parse_axis_md(required["quality"].read_text(encoding="utf-8"), "quality"),
        "severity": parse_axis_md(required["severity"].read_text(encoding="utf-8"), "severity"),
        "context_scope": parse_context_scope(required["context_scope"].read_text(encoding="utf-8")),
        "advanced": parse_axis_md(required["advanced"].read_text(encoding="utf-8"), "advanced"),
    }
    addressed_path = d / "addressed.md"
    if addressed_path.is_file() and addressed_path.stat().st_size > 0:
        out["addressed"] = parse_axis_md(addressed_path.read_text(encoding="utf-8"), "addressed")
    return out


# ---------- Routes ----------

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"ok": True})


@app.route("/thread-check", methods=["GET"])
def thread_check():
    """Given nwo + comment_id, walk the in_reply_to_id chain and report nesting.

    Returns {is_nested: bool, ancestor_count: int}. Used by the extension to flag
    nested-reply tasks before running the pipeline.
    """
    nwo = (request.args.get("nwo") or "").strip()
    comment_id = (request.args.get("comment_id") or "").strip()
    if not nwo or not comment_id:
        return jsonify({"error": "nwo and comment_id required"}), 400

    ancestor_count = 0
    current_id = comment_id
    seen = set()
    try:
        while True:
            if current_id in seen:
                break
            seen.add(current_id)
            proc = subprocess.run(
                ["gh", "api", f"repos/{nwo}/pulls/comments/{current_id}",
                 "--jq", ".in_reply_to_id // empty"],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode != 0:
                if ancestor_count == 0:
                    return jsonify({
                        "error": "gh api failed",
                        "stderr": (proc.stderr or "")[:500],
                    }), 502
                break
            parent = (proc.stdout or "").strip()
            if not parent or parent == "null":
                break
            ancestor_count += 1
            current_id = parent
            if ancestor_count > 50:
                break
    except subprocess.TimeoutExpired:
        return jsonify({"error": "gh api timeout"}), 504
    except FileNotFoundError:
        return jsonify({"error": "gh CLI not available"}), 500

    return jsonify({
        "is_nested": ancestor_count > 0,
        "ancestor_count": ancestor_count,
    })


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    # Already labeled or already flagged?
    existing = find_task_dir(task_id)
    if existing:
        skip = read_skip_flag(existing)
        if skip:
            return jsonify({"status": "skipped", "reason": skip["reason"]})
        deliv = read_deliverables(existing)
        if deliv:
            return jsonify({"status": "done", "deliverables": deliv})

    # Already running? (check-and-set inside lock to avoid racing duplicates)
    with _state_lock:
        if task_id in jobs and jobs[task_id]["status"] == "running":
            return jsonify({"status": "running"})
        jobs[task_id] = {"status": "running", "error": None, "deliverables": None}

    # Create task dir + inputs.md
    task_dir = existing or (TASKS_DIR / date_folder() / task_id)
    (task_dir / "deliverables").mkdir(parents=True, exist_ok=True)
    (task_dir / "work").mkdir(parents=True, exist_ok=True)
    write_inputs_md(task_dir, data)

    model = data.get("model")
    threading.Thread(target=_worker, args=(task_id, task_dir, model), daemon=True).start()
    return jsonify({"status": "running"})


def _worker(task_id, task_dir, model=None):
    try:
        ok, result = run_claude(task_id, model=model)
        if not ok:
            with _state_lock:
                jobs[task_id] = {"status": "error", "error": result.get("error"), "deliverables": None}
            return
        # Skip flag wins over deliverables: the pipeline deliberately stopped
        # and the attempter needs to release the task on the platform.
        skip = read_skip_flag(task_dir)
        if skip:
            with _state_lock:
                jobs[task_id] = {
                    "status": "skipped",
                    "error": None,
                    "deliverables": None,
                    "reason": skip["reason"],
                }
            print(f"[RUN] Skipped: {task_id}")
            return
        deliv = read_deliverables(task_dir)
        if not deliv:
            with _state_lock:
                jobs[task_id] = {
                    "status": "error",
                    "error": "Pipeline finished but deliverables are missing or empty",
                    "deliverables": None,
                }
            return
        with _state_lock:
            jobs[task_id] = {"status": "done", "error": None, "deliverables": deliv}
        print(f"[RUN] Done: {task_id}")
    except Exception as e:
        with _state_lock:
            jobs[task_id] = {"status": "error", "error": str(e), "deliverables": None}
        print(f"[RUN] CRASH {task_id}: {e}")


@app.route("/run/status/<task_id>", methods=["GET"])
def run_status(task_id):
    # Filesystem wins over the in-memory cache.
    task_dir = find_task_dir(task_id)
    if task_dir:
        skip = read_skip_flag(task_dir)
        if skip:
            with _state_lock:
                jobs.pop(task_id, None)
            return jsonify({"status": "skipped", "reason": skip["reason"]})
        deliv = read_deliverables(task_dir)
        if deliv:
            with _state_lock:
                jobs.pop(task_id, None)
            return jsonify({"status": "done", "deliverables": deliv})
    with _state_lock:
        job = jobs.get(task_id)
    if job:
        if job["status"] == "running":
            return jsonify({"status": "running"})
        if job["status"] == "skipped":
            return jsonify({"status": "skipped", "reason": job.get("reason", "")})
        if job["status"] == "error":
            return jsonify({"status": "error", "error": job["error"]})
    return jsonify({"status": "not_found"})


@app.route("/task/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_dir = find_task_dir(task_id)
    if not task_dir:
        return jsonify({"error": "not found"}), 404
    shutil.rmtree(task_dir)
    with _state_lock:
        jobs.pop(task_id, None)
    return jsonify({"ok": True})


# ---------- Review ----------

review_jobs = {}  # task_id -> {"status": running|done|error, "error": ..., "result": ...}


def _platform_axis_md(label, reasoning, axis_title, justification_label):
    return f"{label}\n{axis_title}\n{reasoning}\n"


def write_review_workspace(review_dir, data):
    """Materialize inputs.md + deliverables/*.md from scraped page data.

    Axis ordering matches the 5-axis platform layout. `addressed.md` is only
    written when the scraper found a value, which happens only on merged PRs.
    """
    (review_dir / "deliverables").mkdir(parents=True, exist_ok=True)
    (review_dir / "work").mkdir(parents=True, exist_ok=True)
    write_inputs_md(review_dir, data)

    deliv = data.get("current") or {}
    q  = deliv.get("quality") or {}
    ad = deliv.get("addressed") or None
    s  = deliv.get("severity") or {}
    c  = deliv.get("context_scope") or {}
    a  = deliv.get("advanced") or {}

    (review_dir / "deliverables" / "quality.md").write_text(
        f"{q.get('label','')}\nAxis 1: Quality Justification *\n{q.get('reasoning','')}\n",
        encoding="utf-8")

    # Addressed is only present on merged PRs.
    if ad and (ad.get("label") or ad.get("reasoning")):
        (review_dir / "deliverables" / "addressed.md").write_text(
            f"{ad.get('label','')}\nAxis 2: Addressed Justification *\n{ad.get('reasoning','')}\n",
            encoding="utf-8")

    (review_dir / "deliverables" / "severity.md").write_text(
        f"{s.get('label','')}\nAxis 3: Severity Justification *\n{s.get('reasoning','')}\n",
        encoding="utf-8")

    rows = "\n".join(
        f"{i+1}\n{e.get('diff_line','')}\n{e.get('file_path','')}\n{e.get('why','')}"
        for i, e in enumerate(c.get("entries") or [])
    )
    (review_dir / "deliverables" / "context_scope.md").write_text(
        f"{c.get('label','')}\nAxis 4: Context\n\n#\tdiff_line\tfile_path\twhy\n{rows}\n",
        encoding="utf-8")

    (review_dir / "deliverables" / "advanced.md").write_text(
        f"{a.get('label','')}\nAxis 5: Advanced Justification\n{a.get('reasoning','')}\n",
        encoding="utf-8")


def _parse_platform_axis_md(text):
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


def _read_axis_dir(dir_path):
    """Read all axis files from a deliverables-style directory. Addressed is
    optional, present only when the PR was merged."""
    out = {}
    if not dir_path.is_dir():
        return out
    if (dir_path / "quality.md").is_file():
        out["quality"] = _parse_platform_axis_md((dir_path / "quality.md").read_text(encoding="utf-8"))
    if (dir_path / "addressed.md").is_file():
        out["addressed"] = _parse_platform_axis_md((dir_path / "addressed.md").read_text(encoding="utf-8"))
    if (dir_path / "severity.md").is_file():
        out["severity"] = _parse_platform_axis_md((dir_path / "severity.md").read_text(encoding="utf-8"))
    if (dir_path / "advanced.md").is_file():
        out["advanced"] = _parse_platform_axis_md((dir_path / "advanced.md").read_text(encoding="utf-8"))
    if (dir_path / "context_scope.md").is_file():
        out["context_scope"] = parse_context_scope((dir_path / "context_scope.md").read_text(encoding="utf-8"))
    return out


def read_fixed_deliverables(review_dir):
    """Read fixed_deliverables/*.md (platform format) if present."""
    return _read_axis_dir(review_dir / "fixed_deliverables")


def read_full_deliverables(review_dir):
    """Return original deliverables overlaid with fixed_deliverables.

    Always includes every axis present on disk so the extension can refill
    axes that were not part of the review fix. Without this the extension
    would fall back to whatever was scraped from the form, which may be empty
    if the user reset or never filled that axis before running Review.
    """
    base = _read_axis_dir(review_dir / "deliverables")
    fixed = _read_axis_dir(review_dir / "fixed_deliverables")
    base.update(fixed)
    return base


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
        "deliverables": read_full_deliverables(review_dir),
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
        with _state_lock:
            review_jobs[task_id] = {"status": "running", "error": None, "result": None}
        threading.Thread(target=_review_worker, args=(task_id, existing, "reevaluate", model), daemon=True).start()
        return jsonify({"status": "running"})

    # Idempotency: feedback already exists?
    if existing:
        out = read_review_outputs(existing)
        if out:
            return jsonify({"status": "done", **out})

    with _state_lock:
        if task_id in review_jobs and review_jobs[task_id]["status"] == "running":
            return jsonify({"status": "running"})
        review_jobs[task_id] = {"status": "running", "error": None, "result": None}

    review_dir = existing or (REVIEWS_DIR / date_folder() / task_id)
    write_review_workspace(review_dir, data)

    threading.Thread(target=_review_worker, args=(task_id, review_dir, "auto", model), daemon=True).start()
    return jsonify({"status": "running"})


def _recheck_passed(review_dir):
    """Return True if recheck_report.md exists and reports 0 failures."""
    rp = review_dir / "recheck_report.md"
    if not rp.is_file():
        return False
    try:
        text = rp.read_text(encoding="utf-8")
    except Exception:
        return False
    m = re.search(r"(\d+)\s+failures?", text, re.IGNORECASE)
    if not m:
        return False
    return int(m.group(1)) == 0


def _review_worker(task_id, review_dir, mode="auto", model=None):
    try:
        ok, result = run_claude(task_id, label="REVIEW", command="review", mode=mode, model=model)
        if not ok:
            with _state_lock:
                review_jobs[task_id] = {"status": "error", "error": result.get("error"), "result": None}
            return
        out = read_review_outputs(review_dir)
        if not out and _recheck_passed(review_dir):
            # Subprocess returned OK and recheck passed but feedback_to_cb.md
            # was never written. Known failure mode: the parent session ran
            # out of budget after the nested recheck. Run step-review-finalize
            # to close out the review using the artifacts already on disk.
            print(f"[REVIEW] {task_id}: feedback_to_cb.md missing but recheck passed, invoking finalize")
            ok2, _ = run_claude(
                task_id, label="FINALIZE", command="step-review-finalize",
                mode="auto", model=model,
            )
            if ok2:
                out = read_review_outputs(review_dir)
        if not out:
            with _state_lock:
                review_jobs[task_id] = {
                    "status": "error",
                    "error": "Review finished but feedback_to_cb.md is missing or empty",
                    "result": None,
                }
            return
        with _state_lock:
            review_jobs[task_id] = {"status": "done", "error": None, "result": out}
        print(f"[REVIEW] Done: {task_id}")
    except Exception as e:
        with _state_lock:
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
            with _state_lock:
                review_jobs.pop(task_id, None)
            return jsonify({"status": "done", **out})
    with _state_lock:
        job = review_jobs.get(task_id)
    if job:
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
    with _state_lock:
        run_job_snapshot = dict(jobs[task_id]) if task_id in jobs else None
    run_block = {"present": bool(run_dir), "status": "not_found", "progress": None}
    if run_dir:
        prog = run_dir / "progress.md"
        if prog.is_file():
            run_block["progress"] = prog.read_text(encoding="utf-8")
        skip = read_skip_flag(run_dir)
        if skip:
            run_block["status"] = "skipped"
            run_block["reason"] = skip["reason"]
        elif read_deliverables(run_dir):
            run_block["status"] = "done"
        elif run_job_snapshot and run_job_snapshot["status"] == "running":
            run_block["status"] = "running"
        elif run_job_snapshot and run_job_snapshot["status"] == "error":
            run_block["status"] = "error"
            run_block["error"] = run_job_snapshot["error"]
        else:
            run_block["status"] = "incomplete"
    elif run_job_snapshot and run_job_snapshot["status"] == "running":
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
    with _state_lock:
        review_job_snapshot = dict(review_jobs[task_id]) if task_id in review_jobs else None
    review_block = {"present": bool(review_dir), "status": "not_found", "progress": None}
    if review_dir:
        rprog = review_dir / "review_progress.md"
        if rprog.is_file():
            review_block["progress"] = rprog.read_text(encoding="utf-8")
        if (review_dir / "feedback_to_cb.md").is_file() and (review_dir / "feedback_to_cb.md").stat().st_size > 0:
            review_block["status"] = "done"
        elif review_job_snapshot and review_job_snapshot["status"] == "running":
            review_block["status"] = "running"
        elif review_job_snapshot and review_job_snapshot["status"] == "error":
            review_block["status"] = "error"
            review_block["error"] = review_job_snapshot["error"]
        else:
            review_block["status"] = "incomplete"
    elif review_job_snapshot and review_job_snapshot["status"] == "running":
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

    with _state_lock:
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
    with _state_lock:
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
            with _state_lock:
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
        passed = bool(result.stdout and "RECHECK_PASSED" in result.stdout)
        if not passed and report:
            passed = "0 failures" in report
        with _state_lock:
            recheck_jobs[task_id] = {
                "status": "done",
                "error": None,
                "report": report,
                "passed": passed,
            }
        print(f"[RECHECK] Done: {task_id} — {'PASSED' if passed else 'FAILED'}")
    except Exception as e:
        with _state_lock:
            recheck_jobs[task_id] = {"status": "error", "error": str(e), "report": None}
        print(f"[RECHECK] CRASH {task_id}: {e}")


@app.route("/recheck/status/<task_id>", methods=["GET"])
def recheck_status(task_id):
    with _state_lock:
        job = dict(recheck_jobs[task_id]) if task_id in recheck_jobs else None
    if job:
        return jsonify(job)
    # Check for an existing report on disk
    for base in [find_task_dir(task_id), find_review_dir(task_id)]:
        if base and (base / "recheck_report.md").is_file():
            report = (base / "recheck_report.md").read_text(encoding="utf-8")
            passed = "0 failures" in report
            return jsonify({"status": "done", "report": report, "passed": passed})
    return jsonify({"status": "not_found"})


# ---------- Fix recheck ----------

fix_jobs = {}  # task_id -> {"status", "error", "log", "fixed", "overflags"}


def _parse_fix_done_line(stdout):
    """Parse 'FIX_RECHECK_DONE: X fixed, Y overflags' from CLI stdout."""
    if not stdout:
        return None, None
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("FIX_RECHECK_DONE:"):
            tail = line.split(":", 1)[1].strip()
            fixed, overflags = None, None
            for part in tail.split(","):
                part = part.strip()
                if part.endswith("fixed"):
                    try:
                        fixed = int(part.split()[0])
                    except Exception:
                        pass
                elif part.endswith("overflags"):
                    try:
                        overflags = int(part.split()[0])
                    except Exception:
                        pass
            return fixed, overflags
    return None, None


@app.route("/fix-recheck", methods=["POST"])
def fix_recheck():
    data = request.get_json(force=True) or {}
    task_id = data.get("task_id", "").strip()
    if not task_id:
        return jsonify({"error": "task_id required"}), 400

    with _state_lock:
        if task_id in fix_jobs and fix_jobs[task_id]["status"] == "running":
            return jsonify({"status": "running"})

    model = data.get("model")
    with _state_lock:
        fix_jobs[task_id] = {
            "status": "running", "error": None, "log": None,
            "fixed": None, "overflags": None,
        }
    threading.Thread(
        target=_fix_recheck_worker, args=(task_id, model), daemon=True
    ).start()
    return jsonify({"status": "running"})


def _fix_recheck_worker(task_id, model=None):
    try:
        ok, result = run_claude(
            task_id, label="FIX-RECHECK", command="fix-recheck", mode="auto", model=model
        )
        if not ok:
            with _state_lock:
                fix_jobs[task_id] = {
                    "status": "error",
                    "error": result.get("error"),
                    "log": None, "fixed": None, "overflags": None,
                }
            return
        # Read fix_recheck_log.md
        log = None
        for base in [find_task_dir(task_id), find_review_dir(task_id)]:
            if base and (base / "fix_recheck_log.md").is_file():
                log = (base / "fix_recheck_log.md").read_text(encoding="utf-8")
                break
        fixed, overflags = _parse_fix_done_line(result.stdout or "")
        with _state_lock:
            fix_jobs[task_id] = {
                "status": "done",
                "error": None,
                "log": log,
                "fixed": fixed,
                "overflags": overflags,
            }
        print(f"[FIX-RECHECK] Done: {task_id} fixed={fixed} overflags={overflags}")
    except Exception as e:
        with _state_lock:
            fix_jobs[task_id] = {
                "status": "error", "error": str(e),
                "log": None, "fixed": None, "overflags": None,
            }
        print(f"[FIX-RECHECK] CRASH {task_id}: {e}")


@app.route("/fix-recheck/status/<task_id>", methods=["GET"])
def fix_recheck_status(task_id):
    with _state_lock:
        job = dict(fix_jobs[task_id]) if task_id in fix_jobs else None
    if job:
        return jsonify(job)
    # Fall back to disk
    for base in [find_task_dir(task_id), find_review_dir(task_id)]:
        if base and (base / "fix_recheck_log.md").is_file():
            log = (base / "fix_recheck_log.md").read_text(encoding="utf-8")
            return jsonify({
                "status": "done", "log": log,
                "fixed": None, "overflags": None,
            })
    return jsonify({"status": "not_found"})


if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"TASKS_DIR:    {TASKS_DIR}")
    app.run(host="127.0.0.1", port=5002, debug=True)
