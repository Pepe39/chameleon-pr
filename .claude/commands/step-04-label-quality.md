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

2. Does the comment identify a genuine issue, catch a real bug,
   or suggest a meaningful improvement? Is it actionable and specific?
   -> Yes: HELPFUL

3. Is the comment technically correct but adds no practical value?
   (pedantic, obvious, stylistic without substance, not actionable)
   -> UNHELPFUL
```

### 3. Write reasoning

Document your reasoning in 2-3 sentences:
- What led you to this label
- What evidence from the code/diff supports your decision
- If borderline, why you chose one label over another

### 4. Common mistakes to avoid

Before finalizing, check against these common errors:
- **Do NOT label as Wrong just because you disagree** with the suggestion. Wrong = factually false. (Mistake 1: Confusing Unhelpful with Wrong)
- **Do NOT label as Helpful just because it sounds reasonable.** Verify it against the code.
- **Do NOT label as Unhelpful just because it's about a small thing.** A correct, actionable comment about a real issue is Helpful, even if minor.
- **Do NOT couple Quality and Severity.** A Wrong comment about a critical security issue is still Wrong. A Helpful comment about a naming nit is still Helpful. (Mistake 4)
- A comment that restates what the code obviously does is **Unhelpful**, even if technically correct.

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
