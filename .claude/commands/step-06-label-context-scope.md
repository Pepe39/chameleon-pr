# step-06-label-context-scope

## What it does
Labels Axis 3 — Context Scope. Determines what level of context a reviewer would need to confidently make this comment and documents all evidence used.

## Prerequisites
- Step 05 completed (Severity labeled)

## Context
> See `docs/axis-3-context-scope.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step8.md` for the step-by-step process.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Comment Analysis" section (context consulted, files read).

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

- `diff_line`: line number or range (e.g., "42", "42-50"). Set to `null` if the exact line is hard to locate.
- `file_path`: repo-relative path to the file.
- `why`: a short phrase explaining why this context matters.

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

- **Do NOT default to `diff` just because the comment is on a diff line.** The scope is about what the reviewer needed to know, not where the comment appears.
- **Do NOT forget that `diff` can span multiple files.** If two diff hunks in different files were needed but nothing beyond the diff, it's still `diff`.
- **Do NOT set scope to `file` when `repo` is needed.** If you had to consult files not touched by the PR, the scope is `repo`.

### 6. Update task_info.md

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

### 7. Update progress

Update `progress.md`: step 06 status = "done", Completed = {timestamp ISO 8601}, Current Step = 07 - Label Advanced.
