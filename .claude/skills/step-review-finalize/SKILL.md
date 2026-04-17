---
description: Finish a /review that completed recheck but never wrote feedback_to_cb.md. Generates feedback_to_cb.md and review_meta.json from existing deliverables, fixed_deliverables, and recheck_report.md. Non-interactive.
---

# step-review-finalize - Close out a stuck /review run

Recovers a /review workspace that ran phases 01-07A (recheck) successfully but whose subprocess ended before writing `feedback_to_cb.md` and `review_meta.json`. Generates those two artifacts from the existing state, then marks phases 08 and 09 done in `review_progress.md` and cleans up `work/repo/`.

This skill is always non-interactive. Do NOT ask the user any questions.

## Arguments

- `$ARGUMENTS` (positional): Task id, optionally followed by `auto`. The `auto` token is accepted but ignored since the skill is always non-interactive.

## Preconditions (check in order, STOP if any fails)

1. Find review directory:
   ```bash
   find reviews/ -maxdepth 2 -type d -name "{id}"
   ```
   If not found, print `step-review-finalize: review workspace not found for {id}` and STOP.

2. `recheck_report.md` must exist in the review directory. If missing, print `step-review-finalize: recheck_report.md missing, cannot finalize` and STOP. Do NOT try to rerun recheck.

3. Read `recheck_report.md`. If its `**Totals:**` line shows more than 0 failures, print `step-review-finalize: recheck has open failures, cannot finalize` and STOP. The caller must rerun /review.

4. If `feedback_to_cb.md` already exists and is non-empty, print `step-review-finalize: feedback_to_cb.md already present, nothing to do` and STOP. This is an idempotency guard.

## What to read

- `task_info.md` in the review directory. Contains the comment body, file_path, diff_line, and PR context.
- `deliverables/quality.md`, `deliverables/severity.md`, `deliverables/context_scope.md`, `deliverables/advanced.md`. These are the original labels and reasoning.
- Everything under `fixed_deliverables/` that exists. Axes without a fixed file were unchanged.
- `recheck_report.md`. Use the `**Totals:**` line and the `## Warnings` block.

## Decide what changed

For each of the four axes, compare the original deliverable against the fixed version if present.

- If no fixed file exists for the axis, treat it as unchanged.
- If a fixed file exists, extract its label and reasoning and compare against the original.
- Note every change: label flips, reasoning rewrites, context entry edits, wording fixes.

Also note any warnings from `recheck_report.md` that the reader should be aware of.

## Write feedback_to_cb.md

Write plain prose into `{review_dir}/feedback_to_cb.md`. Follow these rules exactly. They mirror section 12 of the `/review` skill.

- Past tense, phrased as what you adjusted. Not "the Quality label needs to be changed", instead "I changed the Quality label to `helpful`".
- Plain prose paragraphs only. No `#` or `##` headings, no bullet lists, no `>` blockquotes, no tables.
- Inline code with backticks is allowed when naming a label, function, or file, for example `helpful`, `nth(1)`, `useUserAccount/index.ts`.
- One or two short paragraphs total. Name the axis, name what changed, name the concrete reason in one sentence each. No preamble. No recap of the rubric.
- Friendly colleague tone. A short positive opener or closer is fine, for example "Nice work overall." or "Solid pass on the rest.". Never condescending, never mechanical.
- If nothing was adjusted, write a single sentence such as `All labels and reasoning looked good, nothing to adjust here. Nice work.`
- Do NOT copy the diff or paste long code blocks. Reference functions or files by name.

### Wording rules (ZERO tolerance)

Before saving `feedback_to_cb.md`, scan the text and remove every instance of:

- Em-dash `\u2014`. Split into two sentences or use a comma.
- En-dash `\u2013`. Use a plain hyphen for numeric ranges.
- Ellipsis character `\u2026`. Use three dots `...`.
- Smart quotes `\u201c \u201d \u2018 \u2019`. Use straight quotes.
- Bare semicolon `;` as a clause connector. Use a period and start a new sentence.
- Bare colon `:` outside a file path like `src/foo.ts:42`. Rewrite as a normal sentence.
- Parentheses around an aside. Promote the aside to its own sentence, or drop it if it is not important.

If you catch yourself typing one of these, stop and rewrite as two separate sentences. After writing the file and before saving, do a final pass searching for `\u2014`, `\u2013`, `;`, and stray `:` and rewrite those sentences.

## Write review_meta.json

Write `{review_dir}/review_meta.json` with this exact shape:

```json
{
  "quality_score": <int 1-5>,
  "feedback_text": "<the exact same paragraph(s) as feedback_to_cb.md>"
}
```

The `feedback_text` value MUST be the exact prose you just wrote into `feedback_to_cb.md`. The extension pastes this verbatim into the annotation platform.

### Scoring rubric

Pick one integer 1 to 5 using the following rule.

- 5, Excellent. No fixes of any kind. `fixed_deliverables/` is empty or only has format-only touches that did not change meaning.
- 4, Very Good. Only minor wording or format corrections. No label changes, no reasoning rewrites.
- 3, Good. Exactly one label change OR exactly one reasoning rewrite.
- 2, Needs Work. Multiple label changes, or one label change plus one or more reasoning rewrites, or weak reasoning that had to be rebuilt.
- 1, Poor. Three or four axes were wrong and needed fixes.

## Update review_progress.md

Edit `{review_dir}/review_progress.md` so phases 08 and 09 are marked `done` with the current ISO 8601 UTC timestamp in their `Completed` column, the top `**Current Phase:**` line reads `09 Cleanup`, `**Status:**` is `done`, and `**Last Updated:**` is bumped to now.

If phase 07A is still marked `in-progress`, flip it to `done` with the same completion timestamp before touching 08 and 09. The recheck did finish, the parent just never recorded it.

## Cleanup

Delete the cloned repo if it is still present:

```bash
REPO_DIR="{review_dir}/work/repo"
if [ -d "$REPO_DIR" ]; then
  rm -rf "$REPO_DIR"
  echo "Cleaned up repo clone at $REPO_DIR"
fi
```

Then print a single final line:

```
step-review-finalize: done for {id}, feedback_to_cb.md and review_meta.json written.
```

That is the end of the skill. Do NOT rerun any prior phase. Do NOT invoke `/review` or `step-09-recheck`.
