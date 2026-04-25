# step-04-label-quality

## What it does
Labels Axis 1 — Quality. Determines whether the review comment is helpful, unhelpful, or wrong.

## Prerequisites
- Step 03 completed (comment fully analyzed)

## Context
> See `docs/axis-1-quality.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step6.md` for the step-by-step process.
> See `DOCUMENTATION.md` sections 9 (FAQ), 10 (Common Mistakes), and 11 (Tips) for edge cases and pitfalls.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Review Comment" (body) and "Comment Analysis" sections.

If `work/thread.md` exists, read it as well. The body of this task is a nested reply. Take the thread context into account when judging the helpfulness of the body. A reply that looks vague in isolation may be perfectly actionable inside its thread (for example, a one-word answer to a yes/no question from the reviewer above). Do NOT label the ancestor comments. The label targets the body only.

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

3. Is the comment too vague or cryptic to act on without
   investigation? A single word, a bare keyword, or a comment
   that does not specify WHAT to change, WHERE, or HOW is not
   actionable. The developer should not have to guess the
   reviewer's intent or search the codebase to decode the
   suggestion. Examples: "enum", "refactor", "types", "naming".
   -> Yes (vague/cryptic): UNHELPFUL
   -> No: continue to 4

4. Does the comment identify a genuine issue, catch a real bug,
   or suggest a significant improvement? Is it technically correct,
   actionable, and adding value a competent engineer would want
   resolved?
   -> No (pedantic, obvious, stylistic without substance, no real
      issue, restates what the code obviously does): UNHELPFUL
   -> Yes: continue to 5

5. If the comment offers multiple fix options, do those options
   contradict each other, or is one significantly worse than the
   other? The number of options itself does not matter. What
   matters is whether the set of options guides the dev or
   confuses them and risks leading them to a bad path.
   -> Contradictory or uneven options: UNHELPFUL
   -> Single option, or options that are all reasonable: continue to 6

6. Does the proposed fix introduce regressions, incompatibilities,
   or worsen overall code quality? A comment can point at a real
   problem but propose a solution that makes things worse.
   -> Yes: UNHELPFUL
   -> No: HELPFUL
```

**Non-actionable suggestion rule (taint-the-whole-comment):** if even one clause inside the body is non-actionable, the whole comment is UNHELPFUL, regardless of how good the rest is. The attempter cannot act on something that requires them to first verify whether a component or pattern exists in the repo. The comment must already carry that context. Example: `"replace this with a proper segmented control (or use an existing accessible segmented-control/tabs component if the repo has one)"` is UNHELPFUL because the parenthetical punts the repo lookup back to the attempter instead of doing it. Even though the first half is actionable, the second half taints it.

**Mixed comments rule:** when a comment makes multiple claims or has multiple parts, evaluate each individually and then aggregate:
1. If ANY part is **Wrong** -> the comment is **Wrong**
2. If no part is Wrong but ANY part is **Unhelpful** -> the comment is **Unhelpful**
3. Only if ALL parts add value -> **Helpful**

The most problematic part determines the final label. A comment must be completely useful to deserve Helpful.

### 3. Write reasoning

Document your reasoning in 2-3 sentences:
- What led you to this label
- What evidence from the code/diff supports your decision
- If borderline, why you chose one label over another

### 4. Common mistakes to avoid

Before finalizing, check against these common errors:
- **Do NOT label as Wrong just because you disagree** with the suggestion. Wrong = factually false. (Mistake 1: Confusing Unhelpful with Wrong)
- **Do NOT label as Helpful just because it sounds reasonable or is factually correct.** Helpful requires a genuine issue, a technically correct claim, actionability, and a fix with substance.
- **The number of proposed options does not decide the label.** One option and several options can both be Helpful. What matters is whether the suggestion has substance and guides the dev toward a good resolution.
- **Contradictory or uneven options taint the comment.** If the comment offers multiple fixes that pull in different directions, or one option is significantly worse than the other, label as Unhelpful. The comment confuses the dev instead of guiding them.
- **A good catch with a bad fix is Unhelpful.** If the comment identifies a real issue but the proposed solution introduces regressions, incompatibilities, or worsens code quality, label as Unhelpful.
- **Do NOT assume Unhelpful means factually incorrect.** A comment can be technically true and still add no practical value.
- **Do NOT label as Unhelpful just because it's about a small thing.** A correct, actionable comment with substance is Helpful, even if minor.
- **Do NOT couple Quality and Severity.** A Wrong comment about a critical security issue is still Wrong. A Helpful comment about a naming nit is still Helpful. (Mistake 4)
- A comment that restates what the code obviously does is **Unhelpful**, even if technically correct.
- **Vague or cryptic comments are UNHELPFUL, even if the underlying idea is correct.** A comment like "enum", "refactor", "types", or "naming" does not tell the developer what to change or how. The reviewer must specify which enum, which refactor, which type. If the developer has to search the codebase to decode a one-word hint, the comment is not actionable. Correct observation + zero specificity = unhelpful.
- **Non-actionable hedges taint the whole comment.** If any portion of the body says "if the repo has one", "if it exists", "if available", "or use the existing X if there is one", or any other variant that asks the attempter to first go discover something, label as **Unhelpful**. The reviewer is supposed to bring that context. Punting it back to the attempter is not actionable.
- **Check for auto-generated files.** If file_path points to a generated artifact (HTML output, compiled file, build output) AND the generator/template that produces it is also in the PR's changed files, a comment filed on the generated output targets the symptom, not the root cause. The root cause is in the generator/template. Label as **Unhelpful** unless the comment explicitly and primarily addresses the generator, not the output.
- **How to detect generated files:** Look for clues such as: (1) the file lives in a `docs/`, `build/`, `dist/`, or `output/` directory, (2) the PR also changes a script/template that produces it, (3) the file has a "generated by" header or comment, (4) editing the file directly would be overwritten on the next build/generation cycle.
- **Redundant with the diff.** If the dev already implemented what the comment suggests in the same PR, the comment is **Unhelpful**. It asks for something that already exists and adds no value.
- **Comment on code that did not change.** If the comment targets code that existed before the PR and was not modified: Helpful if the issue affects the new functionality, Unhelpful if the issue is completely separate from the PR scope.
- **Style trade-off.** If the comment suggests a stylistic alternative where both options are valid and neither is objectively better (for vs forEach, ternary vs if/else), the comment is **Unhelpful**. Preference without objective improvement is not a real issue.
- **Typo distinction.** A typo in an executable identifier (function name, variable) is a real issue that affects maintainability and is **Helpful**. A typo inside a code comment (non-executable text) may be **Unhelpful** depending on impact.

### 5. Update task_info.md

Add to the Labels section:

```markdown
## Labels

### Quality
- **Label:** {helpful | unhelpful | wrong}
- **Reasoning:** {2-3 sentences explaining the decision}
```

### 6. Update progress

Update `progress.md`: step 04 status = "done", Completed = {timestamp ISO 8601}, Current Step = 045 - Label Addressed.
