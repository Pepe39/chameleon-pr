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

**Important:** The diff must reflect the PR state at `head_sha` from the task inputs, not the current PR state. The PR may have been updated after the comment was made, so `gh pr diff` (which returns the current diff) can be stale or different.

Use the GitHub compare API to get the diff at the exact `head_sha`:

```bash
gh api repos/{nwo}/compare/main...{head_sha} --jq '.files[] | {filename, patch, status}'
```

If the above fails or returns incomplete data, fall back in this order:

1. `gh pr diff {pr_number} --repo {nwo}`
2. `curl -sL https://github.com/{nwo}/pull/{pr_number}.diff` (works for public repos with no auth, add `-H "Authorization: Bearer $GH_TOKEN"` for private)

Both fallbacks return the **current** PR diff, not the one at `head_sha`. If you use either, add a warning to `task_info.md`:
> **Warning:** Diff fetched from current PR state, not from head_sha. The PR may have been updated after the comment was made. Verify diff accuracy against the comment's diff_hunk if results seem inconsistent.

Save the full diff to `tasks/{date}/{id}/work/pr_diff.txt` for reference.

### 4. Identify the target file and surrounding context

From the diff, extract the section relevant to `file_path` and `diff_line`:
- The diff hunk containing the comment's target line
- Surrounding context (the full file diff, not just the hunk)

### 5. Clone repository at head_sha

Clone the repository to enable local file browsing in subsequent steps (per the labeling instructions, Step 3: Browse the repository).

```bash
# Ensure clean state (handles interrupted reruns)
rm -rf "tasks/{date}/{id}/work/repo"

# Shallow clone of the exact commit
git init "tasks/{date}/{id}/work/repo"
cd "tasks/{date}/{id}/work/repo"
git remote add origin "https://github.com/{nwo}.git"
git fetch --depth=1 origin {head_sha}
git checkout FETCH_HEAD
```

**After checkout, verify the commit matches head_sha:**

```bash
ACTUAL_SHA=$(git rev-parse HEAD)
if [ "$ACTUAL_SHA" != "{head_sha}" ]; then
  echo "SHA MISMATCH: expected {head_sha}, got $ACTUAL_SHA"
fi
cd -
```

**Verification outcomes:**

1. **Clone fails** (network error, auth issue, repo too large):
   - Log in task_info.md: `- **Repo Clone:** FAILED — {error summary}`
   - Do NOT stop the pipeline. Steps 03+ will fall back to the `gh api contents` method.
   - Continue to the next section.

2. **Clone succeeds but SHA does not match head_sha:**
   - Log in task_info.md: `- **Repo Clone:** SHA MISMATCH — expected {head_sha}, got {actual_sha}`
   - **Flag to the user:** "The cloned repo is NOT at the expected commit. File browsing results may not match the PR state when the comment was made. Proceed with caution or verify manually."
   - Do NOT stop the pipeline, but this warning must be carried forward into the analysis. Steps 03+ should cross-check any file content against the diff to detect inconsistencies.

3. **Clone succeeds and SHA matches:**
   - Log in task_info.md: `- **Repo Clone:** OK — work/repo/ (verified at {head_sha})`

### 6. Update task_info.md

Add analysis section:

```markdown
## Analysis

### PR Context
- **PR Title:** {title}
- **PR Description:** {description summary — 1-2 sentences}
- **Files Changed:** {N} files, +{additions} -{deletions}
- **Repo Clone:** OK — work/repo/ (verified at {head_sha}) | SHA MISMATCH | FAILED
- **Changed Files List:**
  - {file1}
  - {file2}
  - ...

### Target File
- **File:** {file_path}
- **Diff Line:** {diff_line}
- **Language:** {coding_language}
```

### 7. Update progress

Update `progress.md`: step 02 status = "done", Completed = {timestamp ISO 8601}, Current Step = 03 - Analyze Comment.

**Note:** The repo clone at `work/repo/` is cleaned up by `run.md` after the task completes or the user stops.
