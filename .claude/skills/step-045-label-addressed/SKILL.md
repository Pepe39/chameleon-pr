# step-045-label-addressed

## What it does
Labels Axis 2 Addressed. Determines whether the review comment was addressed, ignored, or a false positive in the merged PR. **Only runs when the PR is merged.** On open PRs the skill marks the step as `skipped` and moves on without producing a deliverable.

## Prerequisites
- Step 04 completed (Quality labeled)
- `task_info.md` records the PR merged status, written by step-02

## Context
> See `docs/axis-2-addressed.md` for definitions, evaluation criteria, and examples.
> See `DOCUMENTATION.md` section 5 (Axis 2 Addressed) for the rationale.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md`. Extract:
- `PR Merged Status` (set by step-02). Typical values. `merged`, `open`, `closed_not_merged`
- `Review Comment` body
- `Comment Analysis` from step-03 if present

If `work/thread.md` exists, read it as well. The body of this task is a nested reply. Take the thread context into account when judging whether the comment was addressed. The decision targets the body only, not the ancestors.

Update `progress.md`. step 045 status = `in-progress`, Started = {timestamp ISO 8601}.

### 2. Merged-status gate

**If the PR is not merged**, do the following and stop:

1. Set step 045 status = `skipped` in `progress.md` with a short reason like `PR not merged, Addressed is open-PR excluded`.
2. Set Current Step = `05 - Label Severity`.
3. Add to `task_info.md` Labels section:
   ```markdown
   ### Addressed
   - **Label:** (skipped, PR not merged)
   - **Reasoning:** Axis 2 Addressed is only labeled for merged PRs. The PR status at task time was {merged_status_value}, so the axis was skipped by design.
   ```
4. Return. Do not produce an `addressed.md` deliverable. Step-08 will see the skipped status and omit the field from `labels.json`.

**If the PR is merged**, continue to step 3.

### 3. Gather merged-state evidence

To decide between `addressed`, `ignored`, and `false_positive`, you need three pieces of evidence:

1. **The comment body.** Read it fresh.
2. **The thread replies, if any.** Check the discussion thread in the PR for any reply from the author or another reviewer. Pay attention to replies that either acknowledge the comment and commit to a fix, or push back on the comment's premise.
3. **The merged code state.** Look at the file at the merge commit and compare against what the comment asked for. If follow-up commits inside the same PR changed the code, evaluate against the merged state, not against the `original_commit_id`.

### 4. Apply the decision tree

```
Did someone reply saying the comment was incorrect, invalid, or unnecessary?
  Look for explicit rebuttal. Author or reviewer explaining why the
  comment does not apply, is based on a misunderstanding, or points
  to a non-issue.
  -> Yes: FALSE_POSITIVE
  -> No: continue

Was the code changed in a way that addresses the concern raised in the comment?
  The fix does not have to match the reviewer's exact suggestion.
  Any merged change that resolves the underlying concern counts.
  Also counts if the author said "will fix later" or "fixed in
  another PR" without changing this PR.
  -> Yes: ADDRESSED
  -> No: continue

The comment was not acted upon and no one dismissed it.
  -> IGNORED
```

### 5. Common mistakes to avoid

- **Silence is not false positive.** Without an explicit rebuttal, the default is `ignored`. Do not label `false_positive` just because the code was not changed.
- **Compare against merged state, not HEAD at comment time.** Follow the thread to whatever actually shipped.
- **Loose acknowledgment counts as addressed.** If the author says `good catch, will fix in another PR` and the underlying concern was genuine, the label is `addressed`, not `ignored`. The acknowledgment is the action.
- **False positive requires an accurate rebuttal.** If someone pushes back but their argument is wrong, the comment is not a false positive. It is still `addressed` or `ignored` depending on what happened to the code.
- **Do not couple Addressed with Quality.** A `wrong` comment can still be `addressed` if the PR author was convinced and changed the code anyway. Rate the merged outcome, not the comment's correctness.

### 6. Write reasoning

Document your reasoning in 2-3 sentences:
- Which signal from the merged state drove the label. A code change, a reply, absence of both
- The specific commit, file, or reply that supports the decision
- For `false_positive`, name the rebutter and summarize their argument

### 7. Update task_info.md

Add to the Labels section. Place this block right after the Quality block, matching the platform's axis order:

```markdown
### Addressed
- **Label:** {addressed | ignored | false_positive}
- **Reasoning:** {2-3 sentences explaining the decision}
```

### 8. Update progress

Update `progress.md`. step 045 status = `done`, Completed = {timestamp ISO 8601}, Current Step = `05 - Label Severity`.
