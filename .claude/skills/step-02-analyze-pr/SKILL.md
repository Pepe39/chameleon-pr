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

### 2. Resolve comment_commit

The `head_sha` from the task inputs is the tip of the PR branch, but the review comment may have been made on an earlier commit within the PR. Use the GitHub API to resolve the exact commit the comment was anchored to.

```bash
gh api repos/{nwo}/pulls/comments/{comment_id} --jq '.original_commit_id'
```

- Save the result as `comment_commit`.
- If the call fails (404, auth error, network), add a warning to `task_info.md`:
  > **Warning:** Could not resolve comment_commit from GitHub API. This may indicate a force push that removed the original commit.
  Set `comment_commit` to the API-returned value anyway. Do NOT silently fall back to `head_sha`.
- Update `task_info.md` Input Data section: set `**Comment Commit:**` to the resolved value.

The pipeline uses `comment_commit` (not `head_sha`) for cloning the repo and verifying whether the problem exists. `head_sha` is still used for the PR diff (section 3) because the diff should reflect the full PR scope.

### 2b. Detect Force Push (orphan check)

After resolving `comment_commit`, verify it exists in the PR's commit history:

```bash
gh api repos/{nwo}/pulls/{pr_number}/commits --paginate --jq '.[].sha' | grep -Fxq "{comment_commit}"
```

- If found: the commit is part of the PR history. Continue normally.
- If NOT found: the commit was likely removed by a force push. Mark as orphan in `task_info.md`:
  > **Force Push Detected:** The original commit ({comment_commit}) does not appear in the PR commit history. The comment is orphaned.
  Set a flag `orphan = true` for step-03. Skip the repo clone (section 5). Step-03 will evaluate using only the comment body and suggestion block.

### 3. Fetch PR information

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

### 5. Clone repository at comment_commit

Clone the repository at the exact commit the reviewer commented on, so that subsequent steps see the code as it was when the comment was made.

Use `comment_commit` (resolved in section 2). If step 2b flagged the task as orphan (force push detected), skip this section entirely. The repo clone is not needed for orphan comments.

```bash
# Ensure clean state (handles interrupted reruns)
rm -rf "tasks/{date}/{id}/work/repo"

# Shallow clone of the exact commit the comment was made on
# IMPORTANT: Use git -C to avoid changing the working directory.
# Do NOT cd into the repo dir — cd does not persist across Bash tool
# calls and subsequent git commands would run in the project root,
# overwriting the project's own remote.
git init "tasks/{date}/{id}/work/repo"
git -C "tasks/{date}/{id}/work/repo" remote add origin "https://github.com/{nwo}.git"
git -C "tasks/{date}/{id}/work/repo" fetch --depth=1 origin {comment_commit}
git -C "tasks/{date}/{id}/work/repo" checkout FETCH_HEAD
```

**After checkout, verify the commit matches comment_commit:**

```bash
ACTUAL_SHA=$(git -C "tasks/{date}/{id}/work/repo" rev-parse HEAD)
if [ "$ACTUAL_SHA" != "{comment_commit}" ]; then
  echo "SHA MISMATCH: expected {comment_commit}, got $ACTUAL_SHA"
fi
```

**Verification outcomes:**

1. **Clone fails** (network error, auth issue, repo too large):
   - Log in task_info.md: `- **Repo Clone:** FAILED — {error summary}`
   - Do NOT stop the pipeline. Steps 03+ will fall back to the `gh api contents` method.
   - Continue to the next section.

2. **Clone succeeds but SHA does not match comment_commit:**
   - Log in task_info.md: `- **Repo Clone:** SHA MISMATCH — expected {comment_commit}, got {actual_sha}`
   - **Flag to the user:** "The cloned repo is NOT at the expected commit. File browsing results may not match the code state when the comment was made. Proceed with caution or verify manually."
   - Do NOT stop the pipeline, but this warning must be carried forward into the analysis. Steps 03+ should cross-check any file content against the diff to detect inconsistencies.

3. **Clone succeeds and SHA matches:**
   - Log in task_info.md: `- **Repo Clone:** OK — work/repo/ (verified at {comment_commit})`

### 6. Update task_info.md

Add analysis section:

```markdown
## Analysis

### PR Context
- **PR Title:** {title}
- **PR Description:** {description summary — 1-2 sentences}
- **Files Changed:** {N} files, +{additions} -{deletions}
- **Comment Commit:** {comment_commit} (resolved from original_commit_id) | fallback to head_sha
- **Repo Clone:** OK — work/repo/ (verified at {comment_commit}) | SHA MISMATCH | FAILED
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
