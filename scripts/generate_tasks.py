#!/usr/bin/env python3
"""Generate task file structure from extracted platform JSON data."""
import json
import os
import sys

BASE_DIR = "/Volumes/Sandisk 1T/Work/Microsoft/code-review"
INPUT_FILE = os.path.join(BASE_DIR, "tasks_raw.json")

# Field ID mapping from taxonomy
FIELD_MAP = {
    "fV9tRUxY": "quality",
    "_rXPqCtw": "quality_justification",
    "keGDphyj": "severity",
    "TpmEQuAs": "severity_justification",
    "2alZBhTr": "context_scope",
    "WjhPQn51": "context_table",
    "6rkuPqDj": "advanced",
    "RBrJh64s": "advanced_justification",
}


def extract_labels(task):
    """Extract label data from conversationEvaluation."""
    ce = (
        task.get("conversation", {})
        .get("conversationEvaluation", {})
        .get("RMySfdr7", {})
    )
    labels = {}
    for field_id, name in FIELD_MAP.items():
        labels[name] = ce.get(field_id)
    return labels


def build_labels_json(labels):
    """Build labels.json content."""
    context_raw = labels.get("context_table")
    # Normalize context table entries
    # Platform uses internal IDs: _dshks=diff_line, ahMYbl=file_path, dA0ihr=why
    normalized_context = []
    rows = []
    if isinstance(context_raw, dict):
        rows = context_raw.get("rows", [])
    elif isinstance(context_raw, list):
        rows = context_raw
    for entry in rows:
        if isinstance(entry, dict):
            normalized_context.append({
                "diff_line": entry.get("_dshks", entry.get("diff_line", "")),
                "file_path": entry.get("ahMYbl", entry.get("file_path", "")),
                "why": entry.get("dA0ihr", entry.get("why", "")),
            })
    return {
        "quality": labels.get("quality") or "",
        "severity": labels.get("severity") or "",
        "context_scope": labels.get("context_scope") or "",
        "context": normalized_context,
        "advanced": labels.get("advanced") or "",
    }


def build_inputs_md(variables):
    """Build inputs.md content."""
    v = variables or {}
    return f"""# Task Inputs

## Task Variables

- **pull_request_url:** {v.get('pull_request_url', '')}
- **nwo:** {v.get('nwo', '')}
- **head_sha:** {v.get('head_sha', '')}
- **comment_id:** {v.get('comment_id', '')}
- **body:** {v.get('body', '')}
- **file_path:** {v.get('file_path', '')}
- **diff_line:** {v.get('diff_line', '')}
- **discussion_url:** {v.get('discussion_url', '')}
- **repo_url:** {v.get('repo_url', '')}
- **coding_language:** {v.get('coding_language', '')}
"""


def build_axis_md(axis_name, label_value, reasoning):
    """Build a deliverable axis .md file."""
    return f"""## {axis_name}

**Label:** {label_value or ''}

## Reasoning

{reasoning or 'N/A'}
"""


def build_task_info_md(task_id, date, variables, labels):
    """Build task_info.md content."""
    v = variables or {}
    body = v.get("body", "")
    # Indent body for blockquote
    body_quoted = "\n".join(f"> {line}" for line in body.split("\n")) if body else "> N/A"

    quality_reasoning = labels.get("quality_justification") or "N/A"
    severity_reasoning = labels.get("severity_justification") or "N/A"
    # context_scope has no separate justification field on the platform
    context_scope_reasoning = "See context.json for evidence entries."
    advanced_reasoning = labels.get("advanced_justification") or "N/A"

    return f"""# Task: {task_id}

## Status
Created: {date}T00:00:00Z

## Input Data
- **PR URL:** {v.get('pull_request_url', '')}
- **Repository:** {v.get('nwo', '')}
- **Head SHA:** {v.get('head_sha', '')}
- **Comment ID:** {v.get('comment_id', '')}
- **File Path:** {v.get('file_path', '')}
- **Diff Line:** {v.get('diff_line', '')}
- **Language:** {v.get('coding_language', '')}
- **Discussion URL:** {v.get('discussion_url', '')}
- **Repo URL:** {v.get('repo_url', '')}

### Review Comment
{body_quoted}

## Labels

### Quality
- **Label:** {labels.get('quality') or ''}
- **Reasoning:** {quality_reasoning}

### Severity
- **Label:** {labels.get('severity') or ''}
- **Reasoning:** {severity_reasoning}

### Context Scope
- **Label:** {labels.get('context_scope') or ''}
- **Reasoning:** {context_scope_reasoning}

### Advanced
- **Label:** {labels.get('advanced') or ''}
- **Reasoning:** {advanced_reasoning}

## Output
- **labels.json:** deliverables/labels.json
- **context.json:** deliverables/context.json
- **quality.md:** deliverables/quality.md
- **severity.md:** deliverables/severity.md
- **context_scope.md:** deliverables/context_scope.md
- **advanced.md:** deliverables/advanced.md
"""


def process_task(raw_task):
    """Process a single raw task and create all files."""
    task_id = raw_task["id"]
    created = raw_task.get("createdAt", "")
    date = created[:10] if created else "unknown"
    variables = raw_task.get("variables", {})
    labels = raw_task.get("labels", {})

    # Determine directory: tasks/{date}/{task_id}/
    task_dir = os.path.join(BASE_DIR, "tasks", date, task_id)
    deliverables_dir = os.path.join(task_dir, "deliverables")
    os.makedirs(deliverables_dir, exist_ok=True)

    # 1. inputs.md
    with open(os.path.join(task_dir, "inputs.md"), "w") as f:
        f.write(build_inputs_md(variables))

    # 2. labels.json
    labels_json = build_labels_json(labels)
    with open(os.path.join(deliverables_dir, "labels.json"), "w") as f:
        json.dump(labels_json, f, indent=2)
        f.write("\n")

    # 3. context.json
    with open(os.path.join(deliverables_dir, "context.json"), "w") as f:
        json.dump(labels_json["context"], f, indent=2)
        f.write("\n")

    # 4. quality.md
    with open(os.path.join(deliverables_dir, "quality.md"), "w") as f:
        f.write(build_axis_md("Quality", labels.get("quality"), labels.get("quality_justification")))

    # 5. severity.md
    with open(os.path.join(deliverables_dir, "severity.md"), "w") as f:
        f.write(build_axis_md("Severity", labels.get("severity"), labels.get("severity_justification")))

    # 6. context_scope.md
    with open(os.path.join(deliverables_dir, "context_scope.md"), "w") as f:
        f.write(build_axis_md("Context Scope", labels.get("context_scope"), "See context.json for evidence entries."))

    # 7. advanced.md
    with open(os.path.join(deliverables_dir, "advanced.md"), "w") as f:
        f.write(build_axis_md("Advanced", labels.get("advanced"), labels.get("advanced_justification")))

    # 8. task_info.md
    with open(os.path.join(task_dir, "task_info.md"), "w") as f:
        f.write(build_task_info_md(task_id, date, variables, labels))

    return task_dir


def main():
    with open(INPUT_FILE) as f:
        raw_tasks = json.load(f)

    print(f"Processing {len(raw_tasks)} tasks...")

    # Count by date
    dates = {}
    created = 0
    skipped = 0

    for raw in raw_tasks:
        task_id = raw.get("id", "")
        status = raw.get("status", "")

        # Skip in_progress tasks
        if status == "in_progress":
            skipped += 1
            continue

        task_dir = process_task(raw)
        date = raw.get("createdAt", "")[:10]
        dates[date] = dates.get(date, 0) + 1
        created += 1

    print(f"\nCreated {created} task directories, skipped {skipped}")
    print("\nTasks by date:")
    for date in sorted(dates.keys()):
        print(f"  {date}: {dates[date]} tasks")
    print(f"\nTotal files created: {created * 8}")


if __name__ == "__main__":
    main()
