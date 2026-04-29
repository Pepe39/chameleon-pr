# step-08-generate-output

## What it does
Compiles all five labeled axes into the final JSON output, validates consistency, and generates the deliverable files ready for submission. `Addressed` is always present using a 4-value enum. `empty` is selected ONLY on OPEN PRs. Closed PRs (merged or closed without merge) get one of `addressed`, `ignored`, `false_positive`.

## Prerequisites
- Steps 04, 045, 05, 06, 07 completed (all labeled axes have a status of `done` in `progress.md`)

## Context
> See `docs/steps/step10.md` for the submission checklist.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md`. Extract all labels and their reasoning from the Labels section. Note the `PR Merged Status` field from the Input Data section, written by step-02.

Read `progress.md` to confirm step 045 completed as `done`. If step 045 is missing or marked anything other than `done`, fail fast and instruct the user to run the addressed step.

Update `progress.md`. step 08 status = `in-progress`, Started = {timestamp ISO 8601}.

### 2. Compile labels

Collect from `task_info.md`:
- **Quality:** {helpful | unhelpful | wrong}
- **Addressed:** {empty | addressed | ignored | false_positive}. The value `empty` is an active selection used ONLY when the PR is OPEN. Closed PRs (merged or closed without merge) get one of the other three
- **Severity:** {nit | moderate | critical}
- **Context Scope:** {diff | file | repo | external}
- **Context Array:** [{entries}]
- **Advanced:** {False | Repo-specific conventions | Context outside changed files | Recent language/library updates | Better implementation approach}

### 3. Validate consistency (GATE)

Run these checks before generating output. If any check fails, report to the user and STOP.

**Field validation:**
- [ ] Quality is one of: `helpful`, `unhelpful`, `wrong`
- [ ] Addressed is one of: `empty`, `addressed`, `ignored`, `false_positive`
- [ ] Severity is one of: `nit`, `moderate`, `critical`
- [ ] Context Scope is one of: `diff`, `file`, `repo`, `external`
- [ ] Advanced is one of: `False`, `Repo-specific conventions`, `Context outside changed files`, `Recent language/library updates`, `Better implementation approach`
- [ ] Context array is valid JSON (array of objects with diff_line, file_path, why)
- [ ] If context_scope is `diff`, `file`, or `repo`, the context array has at least 1 entry
- [ ] If context_scope is `external`, the context array may be empty

**PR-state consistency (GATE, blocking):**
- If `PR Merged Status` is `open`, then `Addressed` must be exactly `empty`. The other three values are invalid on an open PR because the final state is not yet known.
- If `PR Merged Status` is `merged` or `closed_not_merged`, then `Addressed` must be one of `addressed`, `ignored`, `false_positive`. The value `empty` is invalid on any closed PR. A `closed_not_merged` PR is in a final state and the platform expects the same evaluation as a merged PR.

**Scope vs Advanced consistency (GATE, blocking):**
- If `Context Scope` is `repo` or `external`, then `Advanced` MUST NOT be `False`. Crossing the diff boundary is itself beyond-diff knowledge. That combination is invalid by definition. Report the failure in the form `INVALID. context_scope={value}, advanced=False is internally inconsistent. Re-run step-06 or step-07 before proceeding.` and STOP.

**Independence checks (warnings, not blockers):**
- If Quality = `wrong` AND Severity = `nit`, flag for review: "Verify. the issue the comment tried to flag is truly nit-level, even though the comment is wrong."

### 4. Generate labels.json

Write `tasks/{date}/{id}/deliverables/labels.json`. The `addressed` field is always present and uses one of the four enum values. The string `empty` is used ONLY on OPEN PRs. Closed PRs (merged or closed without merge) get one of the other three.

```json
{
  "quality": "{value}",
  "addressed": "{value}",
  "severity": "{value}",
  "context_scope": "{value}",
  "context": [
    {
      "diff_line": "{value_or_null}",
      "file_path": "{value}",
      "why": "{value}"
    }
  ],
  "advanced": "{value}"
}
```

**Formatting rules:**
- Use 2-space indentation
- `addressed` is always present. One of `empty`, `addressed`, `ignored`, `false_positive`. Never emit `null`, `""`, or any other placeholder. The string `empty` is the active selection used ONLY on OPEN PRs. Closed PRs get one of the other three
- `advanced` is a string enum. One of `False`, `Repo-specific conventions`, `Context outside changed files`, `Recent language/library updates`, `Better implementation approach`. Never a JSON boolean
- `diff_line` is a string like `"42"` or JSON `null` when empty. Never `""`, `"null"`, or a bare number
- All string values must be properly escaped
- Axis key order in the JSON follows the platform. `quality`, `addressed`, `severity`, `context_scope`, `context`, `advanced`

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

#### 5b. `addressed.md`

Always generate this file. Step 045 always produces one of the four enum values.

```markdown
# Addressed: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{empty | addressed | ignored | false_positive}**

## Reasoning
{reasoning from step 045}
```

#### 5c. `severity.md`

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

#### 5d. `context_scope.md`

> Use a markdown pipe-table for the Context Evidence rows. Do NOT emit a JSON code block. The API parser tolerates both formats but the pipe-table is the canonical form. JSON blocks make per-row diffs noisier and harder for `/review` to edit.


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

#### 5e. `advanced.md`

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

### 7. Generate to_report.md (nested threads only)

Check if `work/thread.md` exists. If it does NOT exist, skip this section. `to_report.md` is only generated for tasks whose body is a nested reply.

If it DOES exist, write `tasks/{date}/{id}/to_report.md` with a single-row table that summarizes the task for offline reporting. The file is consumed by the user to build a combined report across nested-comment tasks. The extension does not touch it.

Template:

```markdown
# Task report

| Task Number | Summary | Workaround | Axis and Justification | Status | Other task with the same issue / case |
|---|---|---|---|---|---|
| {task_id} | {summary} | {workaround} | {axis_block} | done | |
```

Field rules:

- **Task Number:** the task id from `task_info.md`.
- **Summary:** one or two short sentences describing what the body of the task is saying inside its thread. Focus on what the reply is actually communicating, not just what the thread is about. Plain English. Respect all wording rules from `CLAUDE.md`: no em-dashes, no en-dashes, no semicolons, no colons outside file paths, no parentheses in prose, no smart quotes. If you used a parenthetical, rewrite as a separate sentence.
- **Workaround:** describes any internal adjustment we had to make in order to label the task, for example reinterpreting the body through the thread context, working around a missing commit, or treating an ambiguous reply as a specific stance. Leave empty if no adjustment was needed. Same wording rules apply.
- **Axis and Justification:** a single cell that lists the five axes and their justifications, in platform order and exact format:

  `Quality {label}. {justification}. Addressed {label}. {justification}. Severity {label}. {justification}. Context {label}. {justification}. Advanced {label}. {justification}.`

  The Addressed block is always present. When the PR is OPEN, the value is `empty` and the justification states that the PR is still open. When the PR is closed, the value is one of `addressed`, `ignored`, `false_positive`. Use the labels and reasoning already recorded in `task_info.md` and the per-axis `.md` deliverables. Concatenate with periods between sentences. Do NOT use semicolons, dashes, colons outside file paths, or parentheses to separate the parts. Keep each justification short, one or two sentences per axis. If the reasoning in a deliverable contains forbidden characters, rewrite them into clean prose here before placing them in the cell.
- **Status:** always `done` at this point. The row is only written after the five axes have been labeled and validated.
- **Other task with the same issue / case:** always empty. This column is filled manually by the user. The pipeline never writes into it.

Single-line cell rule: every cell in the row must be a single line. Markdown tables break when a cell contains a literal newline. If a justification is long, rewrite it as shorter sentences joined by a period and a space, do not break it across lines.

Wording audit before saving: scan the generated row for `—`, `–`, `;`, `:` outside file paths, and `(` `)`. Rewrite any matches before writing the file.

### 8. Update task_info.md

Add to the Output section. Include the `addressed.md` line only when the PR was merged and Addressed was labeled:

```markdown
## Output
- **labels.json:** deliverables/labels.json
- **context.json:** deliverables/context.json
- **quality.md:** deliverables/quality.md
- **addressed.md:** deliverables/addressed.md
- **severity.md:** deliverables/severity.md
- **context_scope.md:** deliverables/context_scope.md
- **advanced.md:** deliverables/advanced.md
- **to_report.md:** to_report.md (only if work/thread.md exists)
- **Generated:** {timestamp ISO 8601}
- **Validation:** PASSED / PASSED WITH WARNINGS
```

### 9. Update progress

Update `progress.md`. step 08 status = `done`, Completed = {timestamp ISO 8601}.

Set Current Step to `ALL COMPLETE`.

### 10. Final message

Display. Include the Addressed line only when the PR was merged and the file was generated:

```
== Task {id} COMPLETE ==
All steps completed.

Output files:
  - deliverables/labels.json (for submission)
  - deliverables/context.json (context table for platform)
  - deliverables/quality.md
  - deliverables/addressed.md
  - deliverables/severity.md
  - deliverables/context_scope.md
  - deliverables/advanced.md

Labels summary:
  Quality:       {value}
  Addressed:     {value}
  Severity:      {value}
  Context Scope: {value}
  Advanced:      {value}
```
