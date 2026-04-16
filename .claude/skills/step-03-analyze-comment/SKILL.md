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

**If the comment is not visible in Files Changed** (common for Outdated comments), use these methods:
1. **Conversations dropdown** in the Files Changed tab, which lists unresolved, resolved, and outdated conversations.
2. **Conversation tab** of the PR, where outdated comments appear with a gray "Outdated" badge.
3. **Commits tab**, click on the `original_commit_id` to see the comment in context with the code as it was.

```bash
# Fetch the review comment by ID
gh api repos/{nwo}/pulls/comments/{comment_id} --jq '.body'
```

**If the comment does NOT match the body field:** Report to the user and STOP. Do not continue labeling with mismatched data.

### 2b. Classify comment state

Determine the comment's state: **Active**, **Outdated**, **Resolved**, or **Outdated & Resolved**.

**Detect Outdated:** Compare the code at `comment_commit` around `diff_line` in `file_path` with the code at `head_sha` at the same location. If the lines changed, the comment is Outdated.

**Detect Resolved:** Use GraphQL to check if the review thread is resolved:

```bash
gh api graphql -f query='query {
  repository(owner:"{owner}", name:"{repo}") {
    pullRequest(number:{pr_number}) {
      reviewThreads(first:100) {
        nodes { isResolved comments(first:1) { nodes { databaseId } } }
      }
    }
  }
}' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.comments.nodes[0].databaseId == {comment_id}) | .isResolved'
```

If the GraphQL call fails, default to "unknown" and note in task_info.md.

**Classify:**
- Not outdated and not resolved -> **Active**
- Outdated and not resolved -> **Outdated**
- Not outdated and resolved -> **Resolved**
- Both -> **Outdated & Resolved**

Update `task_info.md` Input Data: set `**Comment State:**` to the classified value.

**Evaluation rules by state:**
- **Active**: evaluate normally, no special considerations.
- **Outdated**: evaluate the comment against the code at `comment_commit` (the original code), not HEAD. Note in the analysis what changed afterwards.
- **Resolved**: ignore the resolved state for technical evaluation. Evaluate as if Active.
- **Outdated & Resolved**: treat as Outdated. The resolved state is just context.

### 2c. Handle orphan comments (force push)

If step-02 flagged `orphan = true` (original commit removed by force push):

1. Do NOT attempt to browse the repo or verify the problem against HEAD.
2. Recover context from the comment body. Look for suggestion blocks with original code, file path, and line numbers.
3. If the comment body provides enough information to understand the issue, continue analysis with limited context. Document the limitation.
4. If the information is insufficient to evaluate, report to the user: "Cannot evaluate, original commit was removed by force push and the comment body does not contain enough context." STOP.
5. In all cases, add to task_info.md: `**Orphan Comment:** Original commit removed by force push. Evaluation based on comment body only.`

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

**Primary method (local clone):**
If `work/repo/` exists in the task directory (cloned in step 02), browse files directly.

**Important:** Check the `Repo Clone` field in `task_info.md` first. If it says `SHA MISMATCH`, cross-check any file content you read against the diff in `work/pr_diff.txt` to detect inconsistencies. If the local file content contradicts the diff, fall back to the `gh api contents` method for that file.

```bash
# Read the target file in full
cat "tasks/{date}/{id}/work/repo/{file_path}"

# Search for function definitions, usages, patterns
grep -rn "function_name" "tasks/{date}/{id}/work/repo/src/"

# Explore directory structure
ls "tasks/{date}/{id}/work/repo/{directory}/"

# Find related files (imports, base classes, configs)
grep -rn "import.*ModuleName" "tasks/{date}/{id}/work/repo/"
```

**Fallback (if clone failed or work/repo/ does not exist):**

Use `comment_commit` from the task_info.md "Comment Commit" field. If that field is missing or says "(populated after step 02)", fall back to `head_sha` with a warning in task_info.md that the file content may not reflect the exact code state when the comment was made.

```bash
gh api repos/{nwo}/contents/{file_path}?ref={comment_commit} --jq '.content' | base64 -d
```

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

### 6. Data consistency verification (GATE)

Before updating task_info.md, verify that the task inputs are internally consistent. This catches mismatched data early, before labeling begins.

**6a. Verify the PR matches the comment**
- Does the PR (pull_request_url) contain the file referenced in file_path?
- Does the PR diff include changes at or near diff_line?
- Is the comment (body) relevant to the changes in this PR?
- If the comment seems unrelated to the PR's purpose, flag it but continue (the comment may be wrong or unhelpful).

**6b. Verify the comment_commit contains the problem**

Use `comment_commit` from `task_info.md` (the exact commit the reviewer commented on). If `comment_commit` is not available and the comment is not orphaned, fall back to `head_sha` as last resort.

- At `comment_commit`, does the code exhibit the issue described in the comment?
- If YES: record "Problem confirmed at comment_commit ({comment_commit})."
- If NO (the problem does not exist at comment_commit): record this finding. This is critical context for labeling; it may mean the comment is **wrong** (claims something that is not true) or **unhelpful** (the issue was already fixed before the comment was made). Do not assume wrong automatically; analyze why the mismatch exists.

**If Comment State is Outdated or Outdated & Resolved**, also compare the code at `comment_commit` vs `head_sha` and classify the outcome:

1. **Problem was fixed afterwards**: the issue the comment points out existed at `comment_commit` but was resolved in a later commit. Record "Problem fixed in subsequent commit. Comment was valid at the time it was made."
2. **Problem still persists**: despite the code changing, the issue still exists at HEAD. Record "Problem persists despite code changes. Evaluate normally."
3. **Change introduced a different problem**: the original issue was resolved but the change introduced a new issue. Record "Original issue resolved, but a different problem was introduced. The comment is no longer relevant to the current code."

In all Outdated cases, evaluate Quality based on whether the comment was correct at the time it was made (at `comment_commit`), not based on the current state of the code.

**Common error to avoid:** Evaluating against the final code (HEAD) and concluding "the comment does not make sense" when it was actually valid for the original code at `comment_commit`.

**6c. Verify the PR resolves what it claims**
- Does the PR (title, description, changes) address what it claims to address?
- Are there obvious gaps between what the PR says it does and what the diff shows?
- Record any discrepancies. These do not block labeling but provide context.

**6d. Record findings**

Add a consistency section to the analysis:

```markdown
### Data Consistency
- **PR matches comment:** Yes/No - {brief explanation}
- **Problem at comment_commit:** Confirmed/Not found/Already fixed - {brief explanation}
- **PR resolves its claims:** Yes/Partially/No - {brief explanation}
```

**If any check reveals a critical mismatch** (e.g., the file does not exist in the PR, the head_sha points to a completely different state), report to the user and STOP. Minor discrepancies should be recorded and factored into labeling.

### 7. Update task_info.md

Add to the Analysis section:

```markdown
### Comment State
- **State:** {Active | Outdated | Resolved | Outdated & Resolved}
- **Outdated Analysis:** {only if Outdated: fixed afterwards | still persists | different problem introduced}

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

### Data Consistency
- **PR matches comment:** Yes/No — {brief explanation}
- **Problem at comment_commit:** Confirmed/Not found/Already fixed — {brief explanation}
- **PR resolves its claims:** Yes/Partially/No — {brief explanation}
```

### 8. Update progress

Update `progress.md`: step 03 status = "done", Completed = {timestamp ISO 8601}, Current Step = 04 - Label Quality.
