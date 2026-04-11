---
description: fix-recheck
---

# fix-recheck - Apply targeted fixes for a failing recheck report

Reads a task's `recheck_report.md`, classifies each failure as a real problem
or an overflag, applies minimal targeted fixes to the deliverables for the real
problems, and leaves overflags untouched so the next `/step-09-recheck` run
surfaces them again for human attention.

## Arguments

- `$ARGUMENTS` (positional): `{task_id} [auto]`. `auto` is currently the only
  supported mode and is treated as the default when omitted.

## Mode detection

Same rule as `/step-09-recheck`. If `tasks/{date}/{id}/fixed_deliverables/`
exists the skill is in **review-mode** and MUST write fixes only under
`fixed_deliverables/`. Otherwise it is in **run-mode** and writes under
`deliverables/`. Never edit `deliverables/` from review-mode.

## Prerequisites

1. Locate task dir with `Glob` or `find tasks/ -maxdepth 3 -type d -name "{id}"`.
2. Read the following if they exist, STOP with a clear error if the task dir
   or recheck report is missing:
   - `recheck_report.md`
   - `task_info.md`
   - `deliverables/labels.json`, `deliverables/context.json`
   - `deliverables/quality.md`, `deliverables/severity.md`,
     `deliverables/context_scope.md`, `deliverables/advanced.md`
   - In review-mode, also read the same files under `fixed_deliverables/`.
   - `work/pr_diff.txt` and the head_sha copy of any file named in a failure.
3. If `recheck_report.md` reports 0 failures, emit
   `FIX_RECHECK_DONE: 0 fixed, 0 overflags` and exit without touching anything.

## Parsing the failures

The report's `## Failures` section contains one bullet per failure in the form
`- **{check_id}** {detail}`. Build an in-memory list of
`{check_id, detail, raw_bullet}` entries. Check ids belong to one of:

- **F1-F3** file integrity (deliverables missing or malformed)
- **L1-L7** label value validation (quality, severity, scope, advanced,
  context array shape)
- **P1-P5** path and line validation (file exists at head_sha, line non-blank,
  line inside a hunk, etc.)
- **C1-C4** comment and context consistency (inputs alignment, body match,
  reconciliation with PR state)
- **W1-W8** wording rule violations (dashes, semicolons, colons, quotes,
  parentheses, hyphen connectors)
- **X1-X4** cross-axis consistency (e.g., scope=file but reasoning only cites
  the diff)

## Classifying each failure

For every failure, decide: **real** or **overflag**.

A failure is **real** if the underlying file/field does contain the issue the
check describes and a minimal edit will make the check pass without inventing
facts. Typical real failures:

- W6 bare colon inside reasoning prose. Fix by wrapping the construct in
  backticks or splitting the sentence.
- P3 blank diff_line anchor. Fix by re-anchoring to the nearest non-blank line
  that is inside a hunk AND still belongs to the method or region the reviewer
  was commenting on.
- P4 diff_line outside every hunk. Fix by the same re-anchor rule.
- C1 byte mismatch between `inputs.md` and `task_info.md` Input Data when the
  drift is a typo or a normalization slip in `task_info.md`. Never change
  `inputs.md`.
- X3 / X4 scope vs justification mismatch when the reasoning clearly points at
  the diff and the label is wrong, or vice versa.

A failure is an **overflag** if the check is triggered by something that is
not actually wrong in context. Typical overflags:

- W6 bare colon inside a quoted code fragment that the check did not recognize
  as code because backticks were omitted by design (for example a literal
  attribute spelled without backticks because it is being discussed as a
  phrase, not as code). If wrapping in backticks is acceptable, prefer to fix
  it as real. Only call it an overflag when the text genuinely cannot be
  rewritten without losing meaning.
- C1 mismatch caused by unicode normalization of a smart quote or apostrophe
  in `inputs.md`, where `task_info.md` correctly stores the normalized form.
- P5 when the `why` field references a symbol in prose without backticks and
  the check misreads a quoted identifier.
- Any check whose detail message explicitly contradicts the observable state
  of the file at head_sha.

When in doubt, err toward **real** and apply a safe fix. Only leave a failure
untouched when fixing it would require guessing or would regress correctness.

## Applying fixes

Fixes must be **minimal** and **localized**. One failure, one edit. Never
rewrite full files. Never touch files that the failure does not reference.
Never change label values (`quality`, `severity`, `context_scope`, `advanced`)
unless the failure is an L or X check that explicitly flags the label itself.

Every edit that touches `labels.json.context[*].why` or
`context.json.rows[*].dA0ihr` MUST also be mirrored in the embedded JSON block
under `task_info.md` `### Context Scope`, and in `deliverables/context_scope.md`
(the table row and the `## Reasoning` section when the change materially
updates the justification).

Every edit that touches reasoning in a deliverable `.md` MUST also update the
corresponding `## Reasoning` section in `task_info.md` if one exists, to keep
the pair in sync.

All edited text MUST respect the project wording rules in
`/Volumes/Sandisk 1T/Work/Microsoft/code-review/CLAUDE.md`. No em-dashes, no
en-dashes, no ellipsis character, no smart quotes, no bare semicolons, no bare
colons outside file paths, no parentheses around asides. Scan every edited
string before saving.

## Logging

Write `tasks/{date}/{id}/fix_recheck_log.md` with the following structure.
Overwrite if it already exists.

```markdown
# Fix Recheck Log: {task_id}

**Mode:** run | review
**Timestamp:** {ISO 8601}
**Source report:** recheck_report.md with {F} failures
**Action totals:** {X} fixed, {Y} overflags

## Fixed
- **{check_id}** {short description of the failure}. **Fix:** {one sentence
  describing the minimal edit applied, including file and field}.

## Overflags
- **{check_id}** {short description of the failure}. **Why skipped:** {one
  sentence explaining why the check is misfiring here}.

## Touched files
- `tasks/{date}/{id}/deliverables/labels.json`
- ...
```

Use short, direct prose. No em-dashes, no semicolons, no bare colons outside
file paths, no parentheses around asides.

## Exit contract

After writing the log, print exactly one final line:

```
FIX_RECHECK_DONE: {X} fixed, {Y} overflags
```

where `X` is the number of real failures actually edited and `Y` is the number
of overflags left alone. This line is parsed by the Flask API worker.

## Non-negotiables

- Fix the root cause, never silence a check by rewording the recheck report.
  The recheck report itself is read-only from this skill's perspective.
- Never modify `inputs.md`. `inputs.md` is the task input contract.
- Never modify `deliverables/` from review-mode.
- Never delete or rewrite `recheck_report.md`.
- Never touch `work/repo/`. Reads only.
- If a failure requires a judgment call that cannot be resolved from the
  diff and the head_sha file alone, classify it as an overflag and skip it.
  A human will catch it on the next recheck pass.
