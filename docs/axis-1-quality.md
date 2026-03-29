# Axis 1: Quality

Classify the overall quality of the review comment. Choose exactly one label.

---

## Possible Values

| Value | Definition |
|---|---|
| **helpful** | The comment identifies a genuine issue, suggests a meaningful improvement, or catches a real bug. It is technically correct, actionable, and adds value. |
| **unhelpful** | The comment is pedantic, stylistic without substance, obvious, or not actionable. It may be technically correct but adds no practical value. |
| **wrong** | The comment is factually incorrect, suggests a change that would introduce a bug, or misunderstands the code. |

---

## How to Evaluate

```
1. Is the comment factually incorrect?
   Does it misunderstand the code, suggest something that would
   introduce a bug, or make a false claim about the language/framework?
   -> Yes: WRONG

2. Does the comment identify a genuine issue, catch a real bug,
   or suggest a meaningful improvement? Is it actionable and specific?
   -> Yes: HELPFUL

3. Is the comment technically correct but adds no practical value?
   Pedantic, obvious, stylistic without substance, not actionable?
   -> UNHELPFUL
```

### Key Rules

- **Wrong** means factually incorrect, NOT "I disagree with the suggestion."
- **Unhelpful** is for comments that are true but provide no practical value.
- Always verify the comment's claims against the actual code before labeling as Wrong.

---

## Example

**Comment:** "This will crash on Python 2 — dict.items() returns a list, not a view."
**Context:** The code runs exclusively on Python 3.

| Field | Value | Reasoning |
|---|---|---|
| quality | **wrong** | The claim is factually incorrect about the runtime environment. The code runs on Python 3, where `dict.items()` returns a view, not a list. The comment bases its criticism on the wrong runtime. |
