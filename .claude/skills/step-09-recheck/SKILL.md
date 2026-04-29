---
description: step-09-recheck
---

# step-09-recheck - Post-labeling verification checklist

Runs a mandatory verification pass over a task's deliverables BEFORE the task
is considered done. Invoked by `/run` after step-08 and by `/review` after
`fixed_deliverables/` are written. Every check must pass, or the task fails
back to the caller.

## Arguments
- `$ARGUMENTS` (positional): Task id, optionally followed by `auto` and/or
  `review`. Examples:
  - `step-09-recheck 2937204136` (run-mode, interactive)
  - `step-09-recheck 2937204136 auto` (run-mode, non-interactive)
  - `step-09-recheck 2937204136 review auto` (review-mode over fixed_deliverables)

## Mode semantics

- **run-mode** (default): validates `tasks/{date}/{id}/deliverables/` (produced
  by step-08). Baseline = the repo clone at `comment_commit` (or `head_sha` fallback) and `task_info.md`.
- **review-mode** (`review` token present): validates
  `tasks/{date}/{id}/fixed_deliverables/` using `deliverables/` + `task_info.md`
  + the repo clone as baseline.

## Prerequisites

1. Locate task dir: `find tasks/ -maxdepth 2 -type d -name "{id}"`.
2. Load the following into memory (STOP with a clear error if any is missing):
   - `task_info.md`
   - `deliverables/labels.json`
   - `deliverables/context.json`
   - `deliverables/quality.md`
   - `deliverables/severity.md`
   - `deliverables/context_scope.md`
   - `deliverables/advanced.md`
   - `work/pr_diff.txt`
   - In review-mode, also load every file under `fixed_deliverables/` that
     exists. Axes without a fixed file inherit from `deliverables/`.
3. Ensure the repo clone at `work/repo/` is present and at `comment_commit` (read from `task_info.md` "Comment Commit" field; fall back to `head_sha` if missing). If it
   does not exist, re-clone per step-02 instructions. If SHA does not match,
   delete and re-clone. Record the result in the report.

## The checklist

Build an in-memory dict `report` keyed by check id. Each entry is
`{ "status": "pass"|"fail", "detail": "..." }`. Run every check even if
earlier ones fail. Never stop mid-checklist.

### F - File integrity

| id | Check |
|---|---|
| F1 | Every deliverable file exists and is non-empty: `quality.md`, `severity.md`, `context_scope.md`, `advanced.md`, `labels.json`, `context.json`. In review-mode, the files loaded from `fixed_deliverables/` override the corresponding `deliverables/` entries. |
| F2 | `labels.json` is valid JSON and contains keys `quality`, `severity`, `context_scope`, `context`, `advanced`. `context` is an array. |
| F3 | `context.json` is valid JSON with shape `{ "rows": [ { "_dshks", "ahMYbl", "dA0ihr" }, ... ] }`. |

### L - Label value validation (case-insensitive)

| id | Check |
|---|---|
| L1 | `quality` in {`helpful`, `unhelpful`, `wrong`} |
| L2 | `severity` in {`nit`, `moderate`, `critical`} |
| L3 | `context_scope` in {`diff`, `file`, `repo`, `external`} |
| L4 | `advanced` in {`repo-specific conventions`, `context outside changed files`, `recent language/library updates`, `better implementation approach`, `false`} |
| L5 | If `context_scope != external`, `labels.json.context.length >= 1`. If `external`, the array may be empty. |
| L6 | The label in each `*.md` file matches the label in `labels.json` for that axis. |
| L7 | `context.json` row count equals `labels.json.context.length`. |

### P - File path and line number validation (requires repo clone)

For each entry in `labels.json.context`:

| id | Check |
|---|---|
| P1 | `file_path` exists in the repo clone: `test -f "work/repo/{file_path}"`. **New-file tolerance:** if the file does NOT exist at `comment_commit` but IS listed as NEW (e.g., `(NEW, +N)`) in the Changed Files List inside `task_info.md`, report as `warn` instead of `fail`. This can happen when the comment was made on a commit that predates the file being added. |
| P2 | If `diff_line` is non-empty, parse it. Accept a single integer (`246`), a range (`65-116`), or a comma list (`12,34-40`). Every parsed line number must be within the file's line count (`wc -l work/repo/{file_path}`). If P1 was a `warn` (file NEW but missing at `comment_commit`), cascade this check as `warn` too. |
| P3 | If `diff_line` is non-empty, the referenced line(s) must be non-blank in the file. Read with `sed -n '{n}p'` and verify the content is not whitespace-only. If P1 was a `warn` (file NEW but missing at `comment_commit`), cascade this check as `warn` too. |
| P4 | If `diff_line` is non-empty, verify the line is covered by a hunk in `work/pr_diff.txt` for that `file_path`. Use the `@@ -x,y +a,b @@` headers to compute the set of line numbers present in the new file, then check membership. If the file is new in the PR, all added lines count. **Tolerance:** if the line falls within ±5 lines of a hunk boundary but is not inside any hunk, report as `warn` instead of `fail`. This accounts for outdated comments where the PR was updated after the comment was posted, shifting line numbers slightly. |
| P5 | If the `why` field references a specific symbol (function, class, or variable name in backticks), at least one of those symbols must appear in the file at or near the referenced line(s). Use `grep -n` within a +/- 5 line window around each referenced line. This is a soft check: report as `warn` instead of `fail` if no match is found, but still record it. |

### C - Comment and context consistency

| id | Check |
|---|---|
| C1 | The `body` field in `task_info.md` Input Data equals the `body` in `inputs.md` (after normalizing whitespace). |
| C2 | The `file_path` and `diff_line` in `task_info.md` Input Data match what `inputs.md` declared. |
| C3 | If any reasoning field contains a quoted phrase in double quotes that looks like it came from the comment (length >= 8 words), that substring must exist in `task_info.md`'s Review Comment block. |
| C4 | `task_info.md`'s "Problem at comment_commit" (or legacy "Problem at head_sha") assessment is present. If it says "Not found" and `quality != wrong` and `quality != unhelpful`, flag as `fail` with a note asking for reconciliation. **Exception:** if the assessment says "Not applicable" and `task_info.md` explains that the file does not exist at `comment_commit` because it was added in a different commit on the PR branch, report as `warn` instead of `fail`. The comment may still be helpful if it was made on an intermediate commit where the file existed. |

### W - Wording rules (ZERO tolerance)

Scan these text streams:

- Reasoning sections (`## Reasoning`) from every deliverable `.md` file present. `quality.md`, `addressed.md` when merged, `severity.md`, `context_scope.md`, `advanced.md`.
- Every `why` value in `context.json.rows[].dA0ihr`.
- Every `why` value in `labels.json.context[].why`.

Forbidden characters in those streams:

| id | Check | Rule |
|---|---|---|
| W1 | No em-dashes `\u2014` (`—`) |
| W2 | No en-dashes `\u2013` (`–`) outside numeric ranges. A numeric range like `65–116` must use ASCII hyphen `-`. |
| W3 | No ellipsis character `\u2026` (`…`). Use three ASCII dots. |
| W4 | No smart/curly quotes `\u201C \u201D \u2018 \u2019`. Use ASCII `"` and `'`. |
| W5 | No bare semicolons `;` outside code fragments inside backticks. |
| W6 | No bare colons `:` outside file paths (pattern `\S+\.\w+:\d+`) and outside code fragments inside backticks. |
| W7 | No bare parentheses around asides. Parentheses are allowed only when quoting a function signature or a code expression inside backticks (e.g. `fn(a, b)`). |
| W8 | No hyphen used as a sentence connector (a space-hyphen-space pattern between clauses, ` - `). Hyphens inside compound words (`focus-loss`) and numeric ranges (`65-116`) are allowed. |

For each stream, scan with a simple character/regex pass and record the exact
offending snippet (20 chars before and after) in the report.

### X - Cross-axis consistency

| id | Check |
|---|---|
| X1 | Each `*.md` file has a non-empty `## Reasoning` section (at least 40 chars after trimming whitespace). |
| X2 | Advanced must be consistent with Context Scope via the deterministic mapping. If `context_scope` is `diff` or `file`, `advanced` must be the string `"False"`. If `context_scope` is `repo` or `external`, `advanced` must be one of the four beyond-diff enum strings `Repo-specific conventions`, `Context outside changed files`, `Recent language/library updates`, `Better implementation approach`. Violation is `fail`. Hard rule. `repo` or `external` with `advanced = "False"` is ALWAYS a fail. |
| X3 | If `context_scope == diff`, no entry in `labels.json.context` may have a `file_path` that is NOT in the PR's Changed Files List from `task_info.md`. |
| X4 | If `context_scope == file` or `repo`, at least one entry must reference a file or line NOT present in the PR diff hunks (otherwise scope should be `diff`). |
| X5 | Advanced is a string enum, never a JSON boolean. `labels.json.advanced` must be one of the five string values, never `true` or `false` as a JSON literal. |
| X6 | Addressed is always present and uses one of four values. `labels.json.addressed` must be one of `empty`, `addressed`, `ignored`, `false_positive`. The value must match the PR state recorded in `task_info.md`. If `PR Merged Status` is `open`, the value must be exactly `empty`. If `PR Merged Status` is `merged` or `closed_not_merged`, the value must be one of `addressed`, `ignored`, `false_positive`. The platform treats closed PRs (with or without merge) as final states that are evaluated the same way. Missing key, wrong value, or mismatched PR state is a `fail`. |

### T - Thread and to_report (nested replies only)

These checks only run when `work/thread.md` exists inside the task dir. When the file is absent, skip every T check. Do not treat the absence as a failure.

| id | Check |
|---|---|
| T1 | `task_info.md` Input Data section contains a `Comment Type:` line. When `work/thread.md` exists, the value must be `nested reply`. When it is absent, the value must be `top-level`. Mismatch is a `fail`. |
| T2 | When `work/thread.md` exists, none of the reasoning sections in the deliverable `.md` files may contradict the ancestor chain. Specifically, if the body answers a direct question from an ancestor, the Quality reasoning must not call the body vague or off-topic without referencing the thread. This is a soft check, report as `warn` when the reasoning ignores a clearly relevant ancestor. |
| T3 | When `work/thread.md` exists, no entry in `labels.json.context` may point at an ancestor comment as if it were a line of code. Ancestor comments are not files and must not appear as `file_path`. |
| T4 | When `work/thread.md` exists, `to_report.md` must exist at the root of the task directory. Missing file is a `fail`. When `work/thread.md` is absent, `to_report.md` must also be absent. A stray `to_report.md` on a top-level task is a `fail`. |
| T5 | When `to_report.md` exists, it must contain exactly one data row with six cells. The row must start with the task id. The Status cell must be `done`. The Other task cell must be empty. Any other shape is a `fail`. |
| T6 | When `to_report.md` exists, the row contents must pass the same wording checks as W1-W8. Forbidden characters anywhere in the cells are `fail`, not `warn`. Auto-fix rules apply the same way as for reasoning fields. |
| T7 | When `to_report.md` exists, the Axis and Justification cell must contain the five axis names in platform order. `Quality`, `Addressed`, `Severity`, `Context`, `Advanced`. Each name must be followed by a label value and at least one sentence of justification. Addressed is always present, with value `empty` only on OPEN PRs and one of `addressed`/`ignored`/`false_positive` on closed PRs (merged or closed without merge). Missing axes, wrong order, or absence of Addressed is a `fail`. |

## Reporting

After every check has run:

1. Count `pass`, `warn`, `fail` totals.
2. Write `tasks/{date}/{id}/recheck_report.md` with the following structure:

```markdown
# Recheck Report: {id}

**Mode:** run | review
**Timestamp:** {ISO 8601}
**Repo clone:** PASS | SHA MISMATCH | FAILED
**Totals:** {P} passed, {W} warnings, {F} failures

## Failures
- **{id}** {detail}
...

## Warnings
- **{id}** {detail}
...

## Passed
F1, F2, F3, L1, ... (comma-separated ids only)
```

3. If run-mode AND failures > 0:
   - **Interactive:** display the report and ask "Apply auto-fixes for wording violations and rerun? (yes/no)". If yes, rewrite the offending reasoning fields to remove the forbidden characters (replace em-dashes with periods, drop parentheses, etc.) and rerun the W checks only. For non-wording failures (L, P, C, X), list them and stop without touching labels.
   - **Auto mode:** do NOT attempt label fixes. Print the report path and exit with a non-zero signal by emitting a final line `RECHECK_FAILED: {F} failures, see recheck_report.md`. The caller (step-08 or /run auto) must treat this as a pipeline failure and surface it to the API.
4. If run-mode AND failures == 0:
   - Mark step 09 as `done` in `progress.md`.
   - Print `RECHECK_PASSED`.
5. If review-mode AND failures > 0:
   - For wording-only failures inside `fixed_deliverables/`, rewrite the offending files in place (still under `fixed_deliverables/`) and rerun the W checks once.
   - For label or consistency failures, record them in `recheck_report.md` and append to `feedback_to_cb.md` a single plain sentence such as `I also caught {N} consistency issue(s) in my own fixes and left notes in recheck_report.md.` Do NOT silently edit labels.
   - In auto mode, still emit `RECHECK_PASSED` only if no failures remain after the wording auto-fix pass. Otherwise emit `RECHECK_FAILED`.
6. If review-mode AND failures == 0:
   - Print `RECHECK_PASSED`.

## Auto-fix rules for wording violations

When auto-fixing wording (W1-W8):

- Em-dash `—` between clauses -> replace with `. ` and capitalize the next word if it was lowercased.
- En-dash `–` inside a range -> replace with `-`.
- Ellipsis `…` -> replace with `...`.
- Smart quotes -> replace with straight ASCII equivalents.
- Bare semicolon `;` -> replace with `. ` and capitalize.
- Bare colon `:` outside a file path -> replace with `, ` or split into two sentences, whichever reads cleaner.
- Parentheses around an aside -> drop the parentheses and the aside becomes its own sentence, or delete the aside if it is redundant.
- ` - ` as a connector -> replace with `. ` and capitalize.

After auto-fixing, RESCAN the same streams. Any remaining W failures are hard
failures (something the auto-fix could not handle) and must be reported.

## Non-negotiables

- **Fix the root cause, never silence a check.** When a check flags a problem
  (especially C4 reconciliation or label-consistency checks), the correct
  response is to investigate and fix the deliverable, NOT to downgrade the
  check severity or relax the rule so it passes. A reconciliation request
  means the label may be wrong. Re-evaluate the label first. Only after
  confirming the label is correct should you consider whether the check
  itself needs a tolerance exception for a legitimate edge case.
- Never modify `deliverables/` from review-mode. Review-mode only writes to
  `fixed_deliverables/` and `recheck_report.md`.
- Never delete `recheck_report.md` on retry. Overwrite it with the latest run.
- Always keep the repo clone at `work/repo/` available until the caller
  cleans it up.
