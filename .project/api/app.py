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


def write_inputs_md(task_dir, data):
    """Write inputs.md in the format that the /run skill (step-01-parse-inputs) expects."""
    lines = ["# Task Inputs", "", "## Task Variables", ""]
    for v in VARS:
        lines.append(f"- **{v}:** {data.get(v, '')}")
    lines.append("")
    (task_dir / "inputs.md").write_text("\n".join(lines), encoding="utf-8")


def run_claude(task_id, label="RUN"):
    clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    cmd = [
        "claude", "-p", f"/run {task_id} auto",
        "--model", "claude-sonnet-4-6",
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
        # Markdown table: header line, then `|---|---|---|` separator, then rows.
        i = table_start + 1
        # Skip separator line(s) like |---|---|---|
        while i < len(lines) and re.match(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", lines[i]):
            i += 1
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

    jobs[task_id] = {"status": "running", "error": None, "deliverables": None}
    threading.Thread(target=_worker, args=(task_id, task_dir), daemon=True).start()
    return jsonify({"status": "running"})


def _worker(task_id, task_dir):
    try:
        ok, result = run_claude(task_id)
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
    task_dir = find_task_dir(task_id)
    if task_id in jobs:
        job = jobs[task_id]
        if job["status"] == "running":
            return jsonify({"status": "running"})
        if job["status"] == "error":
            return jsonify({"status": "error", "error": job["error"]})
    if task_dir:
        deliv = read_deliverables(task_dir)
        if deliv:
            return jsonify({"status": "done", "deliverables": deliv})
    return jsonify({"status": "not_found"})


@app.route("/task/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    task_dir = find_task_dir(task_id)
    if not task_dir:
        return jsonify({"error": "not found"}), 404
    shutil.rmtree(task_dir)
    jobs.pop(task_id, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"TASKS_DIR:    {TASKS_DIR}")
    app.run(host="127.0.0.1", port=5002, debug=True)
