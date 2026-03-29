# Step 6: Label Axis 1 — Quality

## What to Do

1. With full understanding of the comment and its context, decide the quality of the comment.
2. Follow this decision tree:

```
Is the comment factually incorrect?
Does it misunderstand the code, suggest something that would
introduce a bug, or make a false claim about the language/framework?
  -> Yes: WRONG
  -> No: continue...

Does the comment identify a genuine issue, catch a real bug,
or suggest a meaningful improvement? Is it actionable and specific?
  -> Yes: HELPFUL
  -> No: continue...

The comment is technically correct but adds no practical value.
(pedantic, obvious, stylistic without substance, not actionable)
  -> UNHELPFUL
```

3. Assign exactly one of: `helpful`, `unhelpful`, or `wrong`.

## Goal of This Step

Classify whether the comment provides real value to the code review process. Remember: Wrong does not mean "I disagree" — it means "it is factually false." Unhelpful does not mean "it is incorrect" — it means "it adds no practical value even though it may be true."
