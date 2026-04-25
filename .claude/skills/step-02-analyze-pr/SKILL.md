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

### 2c. Detect nested comment and load ancestor thread

Review comments on GitHub can be top-level (the first comment on a line) or nested replies inside an existing thread. When the body of the task is a nested reply, the reviewer's intent often depends on what was asked or stated by earlier comments in the same thread. The pipeline needs that context so the labeling steps can reason correctly.

Fetch the `in_reply_to_id` for the task's comment:

```bash
gh api repos/{nwo}/pulls/comments/{comment_id} --jq '{in_reply_to_id, user: .user.login, created_at, body}'
```

**Top-level case:** if `in_reply_to_id` is null or absent, this comment is top-level.
- Do NOT create `work/thread.md`.
- In `task_info.md` Input Data section, add the line: `- **Comment Type:** top-level`.
- Skip the rest of this section and continue with section 3.

**Nested case:** if `in_reply_to_id` has a value, this comment is a reply inside a thread. Walk the chain of ancestors until you reach the root.

1. Start with the body comment (already fetched above).
2. While the current comment has a non-null `in_reply_to_id`, call the API again on that parent id and record the parent.
3. Stop when a comment has no `in_reply_to_id` (that comment is the root).
4. Reverse the collected list so the root is first and the body is last. All entries belong to the same thread by construction, because `in_reply_to_id` always points to a parent in the same thread. Do NOT include sibling replies that came after the body, and do NOT cross into other threads of the PR.

Write the thread to `tasks/{date}/{id}/work/thread.md` in this format:

```markdown
# Thread context (ancestors only)

This file is present only when the task body is a nested reply. It lists the ancestor chain from the root of the review thread down to the body of this task. Use this as context to understand the intent of the body. Do NOT label any of the ancestor comments. The label still targets the body of the task.

## Root comment, @{author}, {created_at}
{comment body text}

## Reply, @{author}, {created_at}
{comment body text}

...

## Body of this task, @{author}, {created_at}
{comment body text}
```

Each comment section uses a level-2 heading. The last section must be the body of the task.

In `task_info.md` Input Data section, add the line: `- **Comment Type:** nested reply (see work/thread.md, {N} ancestors)` where N is the number of comments above the body.

If any API call in the ancestor walk fails (404, auth error, network), stop walking, write whatever has been collected so far as `work/thread.md`, and add this warning to `task_info.md`:

> **Warning:** Thread walk stopped early due to API error. The loaded thread may be incomplete.

### 2d. Detect comment-about-comment (GATE)

This gate is narrow on purpose. It catches ONLY tasks where the body explicitly references another comment instead of reviewing the code. A body that is just vague, short, or low quality is NOT a skip case, that is a normal labeling job and will almost always land on `unhelpful`. Do not stretch this gate into a catch-all for weak comments.

The batch coordinator asked to skip, release, and flag any task that matches this narrow case. Detecting it here saves the diff fetch in section 3 and the repo clone in section 5.

Read the `body` field from `task_info.md`. If `work/thread.md` was written in section 2c, read it too. Then apply BOTH of the following cumulative tests. The gate triggers only when BOTH are true.

1. **Does the body contain an explicit reference to another comment?** Look for ONE of the following textual cues. Mere absence of code content is NOT a reference, there must be an actual pointer:
   - An at-mention of a reviewer in a discussion sense, such as `@alice good catch`, `thanks @bob`. An at-mention inside a code span, a file path, or a technical identifier does not count.
   - A spatial or temporal pointer to another comment, such as `above`, `below`, `previous comment`, `earlier`, `before`, `later`, `as noted`.
   - A verbal attribution to another reviewer, such as `as alice said`, `to X's point`, `per the earlier comment`.
   - A quote or restatement of another comment's text (markdown `>` blockquote of someone else's words, or a paraphrase of an ancestor in `work/thread.md`).
   - A nested reply whose meaning collapses without the ancestor, for example a body of `yes`, `no`, `agreed`, `thanks`, `good catch` where the thread in `work/thread.md` shows the ancestor framed a yes/no question or made a claim the reply is endorsing. This sub-case ONLY applies when `work/thread.md` exists AND the ancestor supplies the missing referent. A top-level `yes` with no thread does NOT match this test.
2. **Does the body, read on its own, avoid saying anything about the code at `file_path:diff_line`?** No claim about the code, no bug report, no concrete suggested change, no specific code observation. If the body makes even one substantive claim about the code (even if sloppy or partial), test 2 fails and the gate does not trigger.

**If BOTH tests are TRUE**, apply ALL of the following. Do them in order, do not skip any step.

1. Stamp `task_info.md`. In the Input Data section, set `- **Comment Type:** references another comment (skip, release, flag)`. This overwrites any earlier `Comment Type` line written by section 2c. Add a note directly under the `## Status` heading:

   > **SKIP AND FLAG:** The body is a meta-discussion about another comment, not a code review. Skip this task in the annotation platform, release it, and flag it to the batch coordinator.

2. Write `tasks/{date}/{id}/skip_flag.md` at the task root with this content:

   ```markdown
   # SKIP AND FLAG

   **Reason:** The comment references another comment, not code.

   **Action:** Skip this task in the annotation platform, release it, and flag it to the batch coordinator.

   **Detected at:** step 02, section 2d.
   ```

   The presence of this file is the contract between the pipeline, the API, and the extension. Do not rename or move it. The API extracts the `**Reason:**` line verbatim to render the extension's skip banner, so keep that line as a single natural sentence.

3. Update `progress.md`. Set step 02 `Status` to `skipped` and fill `Completed` with the current ISO 8601 timestamp. Set steps 03 through 08 `Status` to `skipped` with empty `Started` and `Completed` cells. Set the top `**Current Step:**` line to `SKIPPED (references another comment)` and the top `**Status:**` line to `skipped`. Bump `**Last Updated:**`.

4. Do NOT run sections 3, 4, or 5. Do NOT fetch the diff. Do NOT clone the repo.

5. Print the following single-line flag to stdout so the runner and API can surface it to the extension:

   `SKIP_AND_FLAG: {id} references another comment (not code). Skip, release, flag in the platform.`

6. Stop. Step 02 is finished for this task in the skip sense. Return control to `/run`, which will detect `skip_flag.md` and stop the pipeline cleanly without invoking steps 03-08.

**Borderline cases:**

- A body that points to another comment AND adds a code observation is NOT a match. Example: `Not sure about @alice's option A, but either way this branch should still release the connection on line 83.` Test 2 fails, proceed normally. The reference is context, not the subject.
- A nested reply that directly answers an ancestor's question with a code observation is NOT a match. Example ancestor: `Should this use a semaphore or a mutex?`. Example body: `Mutex, the only writer is the reaper goroutine and readers are rare.` That body is about the code, it just sits in a thread. Proceed.
- A vague or cryptic top-level body with no reference to another comment is NOT a match. Example: `refactor`, `types`, `naming`, `enum`. Test 1 fails, proceed normally. Step-04 will almost certainly label this `unhelpful`. Do not stretch this gate into a vague-comment catch-all.
- A top-level body that only says `done` or `fixed` or `thanks` with no reference to another comment is NOT a match either. Test 1 fails. Proceed, and let step-04 label as usual.
- A body that quotes another comment and then says only `yes`, `no`, `agreed`, or `good catch` matches the gate if both tests are true, the quote is an explicit reference and the reply carries no code observation on its own.
- A nested `yes`/`no`/`agreed`/`thanks` body matches the gate only when `work/thread.md` exists AND the ancestor makes the reply a clear endorsement or denial of another reviewer's position. If the thread is ambiguous, do NOT stretch the gate, proceed normally.

**Interaction with nested threads:** this gate runs after 2c. A nested reply that only endorses the ancestor's opinion with no code observation matches. A nested reply that genuinely responds with a code observation does not. The ancestor thread is never labeled regardless of this gate, section 2c continues to apply for thread context.

### 3. Fetch PR information

Use `gh` CLI to get PR details:

```bash
# Extract PR number from the URL
# e.g., https://github.com/owner/repo/pull/123 -> 123
gh pr view {pr_number} --repo {nwo} --json title,body,files,additions,deletions,changedFiles,state,mergedAt,mergeCommit
```

Extract and record:
- **PR title** — what the change is about
- **PR description/body** — why the change is being made
- **Files changed** — list of files modified, added, or deleted
- **Stats** — total additions, deletions, number of files changed
- **Merged status** — derive from `state` and `mergedAt`. Values:
  - `merged`. `state == "MERGED"` (or `mergedAt` is non-null)
  - `open`. `state == "OPEN"`
  - `closed_not_merged`. `state == "CLOSED"` and `mergedAt` is null

Record the merged status in `task_info.md` under the Input Data section as `- **PR Merged Status:** {merged | open | closed_not_merged}`. This value gates the Addressed axis. `step-045-label-addressed` only labels when the value is `merged`.

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
- **Comment Type:** top-level | nested reply (see work/thread.md, {N} ancestors)
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

If section 2d wrote `skip_flag.md`, do NOT run this section. The progress file and the task's skip state were already set there. The pipeline must stop after section 2d and return control to `/run`.

Otherwise, update `progress.md`: step 02 status = "done", Completed = {timestamp ISO 8601}, Current Step = 03 - Analyze Comment.

**Note:** The repo clone at `work/repo/` is cleaned up by `run.md` after the task completes or the user stops.
