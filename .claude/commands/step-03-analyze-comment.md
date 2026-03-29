# step-03-analyze-comment

## What it does
Goes to the discussion URL, verifies the comment matches the body field, reviews the diff in depth, and optionally browses the repo for additional context. Produces a thorough understanding of what the comment is pointing out and whether its claims are correct.

## Prerequisites
- Step 02 completed (PR analyzed, diff saved)

## Context
> See `docs/steps/step2.md`, `docs/steps/step3.md`, `docs/steps/step4.md`, and `docs/steps/step5.md` for reference.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` to get: body, discussion_url, repo_url, file_path, diff_line, PR context.
Read `work/pr_diff.txt` for the full diff.

Update `progress.md`: step 03 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Verify the comment (GATE)

Open the `discussion_url` using browser tools or `gh` CLI to verify that the comment shown on GitHub matches the `body` field in the input data.

```bash
# Fetch the review comment by ID
gh api repos/{nwo}/pulls/comments/{comment_id} --jq '.body'
```

**If the comment does NOT match the body field:** Report to the user and STOP. Do not continue labeling with mismatched data.

### 3. Analyze the diff in depth

Read the full diff from `work/pr_diff.txt`. Focus on:

1. **The target hunk:** The diff section containing `file_path` at `diff_line`. Understand what code was changed and why.
2. **The full file diff:** Read all changes in the target file, not just the hunk. Look for patterns, related changes, and context.
3. **Cross-file changes:** Read changes in other files to understand the full scope of the PR.

Document your understanding:
- What is the PR doing overall?
- What specific change is at `diff_line`?
- What is the code around the commented line doing?

### 4. Browse the repository (if needed)

Determine if the comment requires context beyond the diff. Indicators:
- The comment references functions, classes, or patterns not visible in the diff
- The comment claims inconsistency with existing code
- The comment mentions imports, base classes, configs, or API contracts
- The comment requires knowledge of how other parts of the system work

If additional context is needed:

```bash
# Clone or fetch the repo at the correct commit
gh api repos/{nwo}/contents/{file_path}?ref={head_sha} --jq '.content' | base64 -d
```

Or use browser tools to navigate `repo_url` and explore relevant files.

Document what files you consulted and why.

### 5. Deep analysis of the comment

Re-read the `body` field with full context. Answer these questions and record them:

1. **What specific issue is the comment pointing out?**
   - Summarize in 1-2 sentences

2. **Is the comment factually correct?**
   - Verify every claim against the actual code
   - If the comment says "X will happen", trace the code to confirm or refute

3. **What context was needed to make this comment?**
   - Only the diff lines?
   - Other parts of the same file?
   - Other files in the repo?
   - Knowledge outside the repo?
   - **Important:** Distinguish between what you (the analyst) read to verify the comment and what the reviewer needed to make it. You may browse the full file to confirm a claim, but the reviewer might have seen enough in the diff alone. Record your honest assessment of the reviewer's minimum required context.

4. **How impactful is the underlying issue (if real)?**
   - Would it cause a bug, security issue, or data loss?
   - Is it just a style/preference issue?
   - Could it be safely deferred?

5. **Does the comment require knowledge beyond the diff?**
   - Could a reviewer make this comment from the changed lines alone?
   - Does it reference repo conventions, untouched files, or framework specifics?

### 6. Update task_info.md

Add to the Analysis section:

```markdown
### Comment Analysis
- **Comment Verified:** Yes/No (matches body field)
- **Issue Identified:** {1-2 sentence summary of what the comment points out}
- **Factually Correct:** Yes/No/Partially — {brief explanation}
- **Context Consulted (verification):**
  - {file_path}:{lines} — {why you read this to verify the comment}
  - {other_file}:{lines} — {why} (if applicable)
- **Context Needed (reviewer):**
  - {file_path}:{lines} — {why the reviewer needed this to make the comment}
  - (Only list what the reviewer minimally needed, not everything you read)
- **Impact Assessment:** {brief assessment of the issue's real-world impact}
- **Beyond Diff:** Yes/No — {brief explanation of what the reviewer needed, not what you consulted}
```

### 7. Update progress

Update `progress.md`: step 03 status = "done", Completed = {timestamp ISO 8601}, Current Step = 04 - Label Quality.
