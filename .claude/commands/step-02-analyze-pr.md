# step-02-analyze-pr

## What it does
Opens the PR on GitHub, reads the title and description, and gathers high-level context about what the PR changes and why. This context is essential for evaluating the review comment accurately.

## Prerequisites
- Step 01 completed (inputs parsed into `task_info.md`)

## Context
> See `docs/steps/step1.md` and `docs/steps/step3.md` for reference.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Find the task directory and read `task_info.md` to get PR URL, nwo, head_sha, file_path, diff_line.

Update `progress.md`: step 02 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Fetch PR information

Use `gh` CLI to get PR details:

```bash
# Extract PR number from the URL
# e.g., https://github.com/owner/repo/pull/123 -> 123
gh pr view {pr_number} --repo {nwo} --json title,body,files,additions,deletions,changedFiles
```

Extract and record:
- **PR title** — what the change is about
- **PR description/body** — why the change is being made
- **Files changed** — list of files modified, added, or deleted
- **Stats** — total additions, deletions, number of files changed

### 3. Fetch the diff

```bash
gh pr diff {pr_number} --repo {nwo}
```

Save the full diff to `tasks/{date}/{id}/work/pr_diff.txt` for reference.

### 4. Identify the target file and surrounding context

From the diff, extract the section relevant to `file_path` and `diff_line`:
- The diff hunk containing the comment's target line
- Surrounding context (the full file diff, not just the hunk)

### 5. Update task_info.md

Add analysis section:

```markdown
## Analysis

### PR Context
- **PR Title:** {title}
- **PR Description:** {description summary — 1-2 sentences}
- **Files Changed:** {N} files, +{additions} -{deletions}
- **Changed Files List:**
  - {file1}
  - {file2}
  - ...

### Target File
- **File:** {file_path}
- **Diff Line:** {diff_line}
- **Language:** {coding_language}
```

### 6. Update progress

Update `progress.md`: step 02 status = "done", Completed = {timestamp ISO 8601}, Current Step = 03 - Analyze Comment.
