# step-08-generate-output

## What it does
Compiles all four axis labels into the final JSON output, validates consistency, and generates the deliverable file ready for submission.

## Prerequisites
- Steps 04-07 completed (all four axes labeled)

## Context
> See `docs/steps/step10.md` for the submission checklist.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — extract all four labels and their reasoning from the Labels section.

Update `progress.md`: step 08 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Compile labels

Collect from task_info.md:
- **Quality:** {helpful | unhelpful | wrong}
- **Severity:** {nit | moderate | critical}
- **Context Scope:** {diff | file | repo | external}
- **Context Array:** [{entries}]
- **Advanced:** {Repo-specific conventions | Context outside changed files | Recent language/library updates | Better implementation approach | False}

### 3. Validate consistency (GATE)

Run these checks before generating output. If any check fails, report to the user and STOP.

**Field validation:**
- [ ] Quality is one of: `helpful`, `unhelpful`, `wrong`
- [ ] Severity is one of: `nit`, `moderate`, `critical`
- [ ] Context Scope is one of: `diff`, `file`, `repo`, `external`
- [ ] Advanced is one of: `Repo-specific conventions`, `Context outside changed files`, `Recent language/library updates`, `Better implementation approach`, `False`
- [ ] Context array is valid JSON (array of objects with diff_line, file_path, why)
- [ ] If context_scope is `diff`, `file`, or `repo`, the context array has at least 1 entry
- [ ] If context_scope is `external`, the context array may be empty

**Independence checks (warnings, not blockers):**
- If Quality = `wrong` AND Severity = `nit`, flag for review: "Verify: the issue the comment tried to flag is truly nit-level, even though the comment is wrong."
- If Quality = `helpful` AND Advanced = `False` AND Context Scope = `repo`, flag for review: "Verify: the comment requires repo-level context but is not considered advanced?"

### 4. Generate labels.json

Write `tasks/{date}/{id}/deliverables/labels.json`:

```json
{
  "quality": "{value}",
  "severity": "{value}",
  "context_scope": "{value}",
  "context": [
    {
      "diff_line": "{value_or_null}",
      "file_path": "{value}",
      "why": "{value}"
    }
  ],
  "advanced": "{category_or_False}"
}
```

**Formatting rules:**
- Use 2-space indentation
- `advanced` must be a string matching one of the platform categories or `"False"`
- `diff_line` must be a string or `null`, not a number
- All string values must be properly escaped

### 5. Generate context.json

Write `tasks/{date}/{id}/deliverables/context.json` using the table format from `table-template.json`.

Map the context array entries to the table column IDs:
- `_dshks` = `diff_line` value (string or empty string if null)
- `ahMYbl` = `file_path` value
- `dA0ihr` = `why` value

```json
{
  "rows": [
    {
      "_dshks": "{diff_line_or_empty}",
      "ahMYbl": "{file_path}",
      "dA0ihr": "{why}"
    }
  ]
}
```

**Rules:**
- If `diff_line` is `null`, use an empty string `""` for `_dshks`
- One row per context array entry
- Use 2-space indentation

### 6. Generate per-axis deliverables

Write one markdown file per axis inside `tasks/{date}/{id}/deliverables/`.

**IMPORTANT:** The `## Reasoning` section in each file is the justification the user will paste directly into the annotation platform. It must be self-contained, clear, and ready to copy-paste as-is.

#### 5a. `quality.md`

```markdown
# Quality: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{helpful | unhelpful | wrong}**

## Reasoning
{reasoning from step 04}
```

#### 5b. `severity.md`

```markdown
# Severity: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{nit | moderate | critical}**

## Reasoning
{reasoning from step 05}
```

#### 5c. `context_scope.md`

```markdown
# Context Scope: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{diff | file | repo | external}**

## Context Evidence
| diff_line | file_path | why |
|---|---|---|
| {line} | {path} | {reason} |

## Reasoning
{reasoning from step 06}
```

#### 5d. `advanced.md`

```markdown
# Advanced: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{Repo-specific conventions | Context outside changed files | Recent language/library updates | Better implementation approach | False}**

## Reasoning
{reasoning from step 07}
```

### 7. Update task_info.md

Add to the Output section:

```markdown
## Output
- **labels.json:** deliverables/labels.json
- **context.json:** deliverables/context.json
- **quality.md:** deliverables/quality.md
- **severity.md:** deliverables/severity.md
- **context_scope.md:** deliverables/context_scope.md
- **advanced.md:** deliverables/advanced.md
- **Generated:** {timestamp ISO 8601}
- **Validation:** PASSED / PASSED WITH WARNINGS
```

### 8. Update progress

Update `progress.md`: step 08 status = "done", Completed = {timestamp ISO 8601}.

Set Current Step to: "ALL COMPLETE"

### 9. Final message

Display:

```
== Task {id} COMPLETE ==
All 8 steps completed.

Output files:
  - deliverables/labels.json (for submission)
  - deliverables/context.json (context table for platform)
  - deliverables/quality.md
  - deliverables/severity.md
  - deliverables/context_scope.md
  - deliverables/advanced.md

Labels summary:
  Quality:       {value}
  Severity:      {value}
  Context Scope: {value}
  Advanced:      {value}
```
