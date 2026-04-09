# Axis 1: Quality

Classify the overall quality of the review comment. Choose exactly one label.

---

## Possible Values

| Value | Definition |
|---|---|
| **helpful** | Identifies a genuine issue, suggests a significant improvement, or detects a real bug. The comment is technically correct, actionable, and adds value by pointing to something a competent engineer would want to resolve. It does not matter whether the comment offers one option or several to fix the issue. What defines the label is the quality of the issue detected and whether the suggestion has substance, not the number of proposed paths. |
| **unhelpful** | Pedantic, stylistic without substance, obvious, or not actionable. Can be technically correct but adds no practical value. Also unhelpful when the comment offers multiple fix options that contradict each other or where one is significantly worse than the other, because the comment then confuses the dev instead of guiding them. Also unhelpful when the comment points at a real problem but the proposed fix introduces regressions, incompatibilities, or worsens overall code quality. |
| **wrong** | The comment is factually incorrect, suggests a change that would introduce a bug, or misunderstands the code. |

---

## How to Evaluate

```
1. Is the comment factually incorrect?
   Does it misunderstand the code, suggest something that would
   introduce a bug, or make a false claim about the language/framework?
   -> Yes: WRONG

2. Does the comment identify a genuine issue, catch a real bug,
   or suggest a significant improvement? Is it technically correct,
   actionable, and adding value?
   -> No: UNHELPFUL
   -> Yes: continue to 3

3. If the comment offers multiple fix options, do those options
   contradict each other, or is one significantly worse than the
   other? Does the set of options confuse the dev or risk leading
   them down a bad path?
   -> Yes: UNHELPFUL
   -> No or single option: continue to 4

4. Does the proposed fix introduce regressions, incompatibilities,
   or worsen the overall code quality? The comment may point at a
   real problem but the solution makes things worse.
   -> Yes: UNHELPFUL
   -> No: HELPFUL
```

### Key Rules

- **Wrong** means factually incorrect, NOT "I disagree with the suggestion."
- **Helpful** requires a genuine issue, a technically correct claim, actionability, and a fix with substance. The number of proposed options does not matter. One good option and several good options are both Helpful.
- **Unhelpful** does NOT mean factually incorrect. A comment can be factually true and still unhelpful if it is pedantic, obvious, or not actionable.
- **Contradictory or uneven options make a comment Unhelpful.** When a comment proposes several fixes that pull in different directions, or where one option is clearly worse than another, the comment fails to guide the dev and is Unhelpful.
- **A good catch with a bad fix is Unhelpful.** If the comment identifies a real issue but the suggested solution introduces regressions, incompatibilities, or worsens code quality, label as Unhelpful.
- Always verify the comment's claims against the actual code before labeling as Wrong.

---

## Example

**Comment:** "This will crash on Python 2. dict.items() returns a list, not a view."
**Context:** The code runs exclusively on Python 3.

| Field | Value | Reasoning |
|---|---|---|
| quality | **wrong** | The claim is factually incorrect about the runtime environment. The code runs on Python 3 where dict.items() returns a view. The comment bases its criticism on the wrong runtime. |
