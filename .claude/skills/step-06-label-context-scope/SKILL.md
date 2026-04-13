# step-06-label-context-scope

## What it does
Labels Axis 3 — Context Scope. Determines what level of context a reviewer would need to confidently make this comment and documents all evidence used.

## Prerequisites
- Step 05 completed (Severity labeled)

## Context
> See `docs/axis-3-context-scope.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step8.md` for the step-by-step process.
> See `DOCUMENTATION.md` sections 8 (FAQ), 9 (Common Mistakes), and 10 (Tips) for edge cases and pitfalls.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Comment Analysis" section. Pay attention to:

- **"Beyond Diff" field:** This is step-03's preliminary assessment of whether the reviewer needed context beyond the diff. Your context_scope label must be consistent with it. If you disagree, you must explain why in the reasoning.
- **"Context Consulted":** This lists what the analyst read to verify the comment. Be careful: the analyst may have read more than the reviewer needed. For example, the analyst might browse the full file to confirm a claim, but the reviewer could have made the comment from the diff alone. Do not inflate scope based on what was consulted for verification.

Update `progress.md`: step 06 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Determine scope level

Ask: "What would the reviewer need to read to make this comment with confidence?"

Evaluate from narrowest to broadest:

1. **DIFF** — Could the comment be made by reading only the changed lines in the PR?
   - The diff can span multiple files — as long as only changed lines were needed, it's still `diff`.
   - Typos, syntax errors, obvious logic bugs visible in changed lines -> `diff`

2. **FILE** — Did the reviewer need to read beyond the diff but within the PR-touched files?
   - Surrounding functions, imports, class definitions outside the changed lines
   - Code in other PR-touched files outside their diff hunks

3. **REPO** — Did the reviewer need knowledge from files NOT changed by the PR?
   - Shared utilities, base classes, config files, tests in untouched files
   - If you had to browse the repo in step 03 to verify the comment -> likely `repo`

4. **EXTERNAL** — Did the reviewer need knowledge outside the repository?
   - API docs, RFCs, language specs, business requirements not in the repo

**Always pick the broadest level needed.** If both diff and file context were required -> `file`.

### 3. Build the context array

List every specific piece of evidence the reviewer used. For each entry:

- `diff_line`: line number or range as a string (e.g., `"42"`, `"42-50"`). When the input field is empty or no specific line applies, set to JSON `null`, not an empty string, not `""`, not `"null"`. The literal JSON value `null`.
- `file_path`: repo-relative path to the file.
- `why`: a short phrase explaining why this context matters.

**ZERO-TOLERANCE punctuation in `why`:** the `why` field is user-facing text and is subject to the same wording rules as any justification. It MUST NOT contain em-dashes (`—`), en-dashes (`–`), hyphens used as sentence connectors, semicolons (`;`), or colons (`:`) outside file paths. If you need to join two ideas, write two short phrases separated by a period or use a comma. Before saving, re-read every `why` value and rewrite any that contain forbidden characters. This applies equally to `context.json`, `labels.json`, `context_scope.md`, and `task_info.md`.

**Rules:**
- If scope is `diff`, at least one entry is needed (the commented line).
- If scope is `file`, include both the diff lines AND the non-diff lines that were needed.
- If scope is `repo`, include entries for both PR files and non-PR files consulted.
- If scope is `external`, the context array may be empty (`[]`).

### 4. Write reasoning

Document in 2-3 sentences:
- What the broadest level of context needed was and why
- Which specific files or lines outside the diff (if any) were required

### 5. Common mistakes to avoid

- **Do NOT default to `diff` just because the comment is on a diff line.** The scope is about what the reviewer needed to know, not where the comment appears. (Mistake 3: Defaulting to Diff Scope)
- **Do NOT forget that `diff` can span multiple files.** If two diff hunks in different files were needed but nothing beyond the diff, it's still `diff`. (FAQ #2)
- **Do NOT set scope to `file` when `repo` is needed.** If you had to consult files not touched by the PR, the scope is `repo`.
- **Do NOT conflate analyst verification with reviewer observation.** In step-03, you may have read the full file or browsed the repo to verify the comment's claims. That does not mean the reviewer needed that context to make the comment. Ask: "Could the reviewer have made this comment from the diff alone?" not "Did I read beyond the diff to check it?"
- **Do NOT contradict step-03's "Beyond Diff" field without explanation.** If step-03 says "Beyond Diff: No" but you label `file`, or vice versa, state why you disagree in the reasoning.
- **If context_scope is `file`, you still fill in `diff_line`** for any context entry that points to a specific line, including lines inside the diff. (FAQ #3)
- **`diff_line` must be `null`** only for files NOT touched by the PR. For PR-touched files, always provide a line number or range unless the exact line is genuinely hard to locate.

### 6. Verify diff_line accuracy

Before writing any context entry, verify each `diff_line` value against the actual file content in the repo clone (at `comment_commit`, or `head_sha` as fallback):

1. For each context entry, confirm the line number points to the actual code referenced, not an adjacent blank line, comment, or closing brace.
2. If the entry references a range (e.g., "207-215"), confirm the range starts and ends at the correct boundaries of the relevant code block (function definition, statement, etc.).
3. Cross-check by reading the specific line(s) from the fetched file. If line N is blank but line N-1 or N+1 contains the target code, use the correct line number.

This prevents off-by-one errors from line counting during analysis.

### 7. Update task_info.md

Add to the Labels section:

```markdown
### Context Scope
- **Label:** {diff | file | repo | external}
- **Context:**
  ```json
  [
    {
      "diff_line": "{line_or_range}",
      "file_path": "{path}",
      "why": "{reason}"
    }
  ]
  ```
- **Reasoning:** {2-3 sentences explaining the decision}
```

### 8. Update progress

Update `progress.md`: step 06 status = "done", Completed = {timestamp ISO 8601}, Current Step = 07 - Label Advanced.
