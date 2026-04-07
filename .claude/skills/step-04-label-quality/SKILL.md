# step-04-label-quality

## What it does
Labels Axis 1 — Quality. Determines whether the review comment is helpful, unhelpful, or wrong.

## Prerequisites
- Step 03 completed (comment fully analyzed)

## Context
> See `docs/axis-1-quality.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step6.md` for the step-by-step process.
> See `DOCUMENTATION.md` sections 8 (FAQ), 9 (Common Mistakes), and 10 (Tips) for edge cases and pitfalls.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Review Comment" (body) and "Comment Analysis" sections.

Update `progress.md`: step 04 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Apply the decision tree

Read the comment body and the analysis from step 03. Follow this decision tree strictly:

```
1. Is the comment factually incorrect?
   Does it misunderstand the code, suggest something that would
   introduce a bug, or make a false claim about the language/framework?
   -> Yes: WRONG

2. Does ANY part of the comment body contain a non-actionable
   suggestion? Look for hedges like "or use an existing X if the
   repo has one", "if it exists", "if available", "consider",
   "you may want to", "perhaps", "maybe". A truly actionable
   comment tells the attempter WHAT to do; it does not punt the
   discovery work back to the reader.
   -> Yes (any portion is non-actionable): UNHELPFUL
   -> No: continue to 3

3. Does the comment go directly to the root cause of the problem?
   Does it identify the actual underlying issue, not just a symptom
   or side effect? Is it actionable and specific about the root problem?
   -> No: UNHELPFUL
   -> Yes: continue to 4

4. Is the suggestion accurate against the full repo context?
   Does the proposed fix or functionality already exist in the codebase?
   Would the change duplicate what the repo already provides?
   -> Already exists / redundant: UNHELPFUL
   -> Validated, not redundant: HELPFUL

5. Is the comment factually correct but does NOT target the root cause?
   Does it point at a symptom, a tangential concern, or a side effect
   instead of the actual root problem? Or is it pedantic, obvious,
   stylistic without substance, or not actionable?
   -> UNHELPFUL
```

**Non-actionable suggestion rule (taint-the-whole-comment):** if even one clause inside the body is non-actionable, the whole comment is UNHELPFUL, regardless of how good the rest is. The attempter cannot act on something that requires them to first verify whether a component or pattern exists in the repo. The comment must already carry that context. Example: `"replace this with a proper segmented control (or use an existing accessible segmented-control/tabs component if the repo has one)"` is UNHELPFUL because the parenthetical punts the repo lookup back to the attempter instead of doing it. Even though the first half is actionable, the second half taints it.

### 3. Write reasoning

Document your reasoning in 2-3 sentences:
- What led you to this label
- What evidence from the code/diff supports your decision
- If borderline, why you chose one label over another

### 4. Common mistakes to avoid

Before finalizing, check against these common errors:
- **Do NOT label as Wrong just because you disagree** with the suggestion. Wrong = factually false. (Mistake 1: Confusing Unhelpful with Wrong)
- **Do NOT label as Helpful just because it sounds reasonable or is factually correct.** Helpful requires that the comment targets the root cause of the problem, not just a symptom or side effect, AND that the suggestion is validated against the full repo context.
- **Always validate against the full repo.** If the comment proposes a fix or functionality that already exists in the codebase, it is Unhelpful. The correct approach would be to use what already exists, not recreate it.
- **Do NOT assume Unhelpful means factually incorrect.** A comment can be true, identify a real observation, and still be unhelpful if it does not go to the root problem.
- **Do NOT label as Unhelpful just because it's about a small thing.** A correct, actionable comment that targets the root cause is Helpful, even if minor.
- **Do NOT couple Quality and Severity.** A Wrong comment about a critical security issue is still Wrong. A Helpful comment about a naming nit is still Helpful. (Mistake 4)
- A comment that restates what the code obviously does is **Unhelpful**, even if technically correct.
- A comment that points at a real symptom but misses the root cause is **Unhelpful**, even if factually accurate.
- **Non-actionable hedges taint the whole comment.** If any portion of the body says "if the repo has one", "if it exists", "if available", "or use the existing X if there is one", or any other variant that asks the attempter to first go discover something, label as **Unhelpful**. The reviewer is supposed to bring that context. Punting it back to the attempter is not actionable.
- **Check for auto-generated files.** If file_path points to a generated artifact (HTML output, compiled file, build output) AND the generator/template that produces it is also in the PR's changed files, a comment filed on the generated output targets the symptom, not the root cause. The root cause is in the generator/template. Label as **Unhelpful** unless the comment explicitly and primarily addresses the generator, not the output.
- **How to detect generated files:** Look for clues such as: (1) the file lives in a `docs/`, `build/`, `dist/`, or `output/` directory, (2) the PR also changes a script/template that produces it, (3) the file has a "generated by" header or comment, (4) editing the file directly would be overwritten on the next build/generation cycle.

### 5. Update task_info.md

Add to the Labels section:

```markdown
## Labels

### Quality
- **Label:** {helpful | unhelpful | wrong}
- **Reasoning:** {2-3 sentences explaining the decision}
```

### 6. Update progress

Update `progress.md`: step 04 status = "done", Completed = {timestamp ISO 8601}, Current Step = 05 - Label Severity.
