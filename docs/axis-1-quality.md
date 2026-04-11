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

The canonical decision tree lives in `.claude/skills/step-04-label-quality/SKILL.md` Section 2 and is mirrored in `.claude/skills/review/SKILL.md` Section 4a. Both must stay identical. The tree has **6 nodes**, reproduced here for reference.

```
1. Is the comment factually incorrect?
   Does it misunderstand the code, suggest something that would
   introduce a bug, or make a false claim about the language/framework?
   -> Yes: WRONG

2. Does ANY part of the comment body contain a non-actionable
   suggestion? Look for hedges like "or use an existing X if the
   repo has one", "if it exists", "if available", "consider",
   "you may want to", "perhaps", "maybe". A truly actionable
   comment tells the attempter WHAT to do, it does not punt the
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

### Key Rules

- **Wrong** means factually incorrect, not "I disagree with the suggestion."
- **Helpful** requires a genuine issue, a technically correct claim, actionability, and a fix with substance. The number of proposed options does not matter. One good option and several good options are both Helpful.
- **Unhelpful** does not mean factually incorrect. A comment can be factually true and still unhelpful if it is pedantic, obvious, vague, or not actionable.
- **Non-actionable hedges taint the whole comment.** If any clause inside the body punts discovery back to the attempter, for example `if the repo has one`, `if it exists`, `if available`, label Unhelpful even if the rest of the comment is strong.
- **Vague or cryptic comments are Unhelpful.** A one-word hint like `enum`, `refactor`, `types`, or `naming` is not actionable. Correct observation plus zero specificity equals Unhelpful.
- **Contradictory or uneven options make a comment Unhelpful.** When a comment proposes several fixes that pull in different directions, or where one option is clearly worse than another, the comment fails to guide the dev.
- **A good catch with a bad fix is Unhelpful.** If the comment identifies a real issue but the suggested solution introduces regressions, incompatibilities, or worsens code quality, label as Unhelpful.
- **Auto-generated files.** If the target file is a generated artifact and the generator or template is also in the PR, the comment targets the symptom, not the root cause. Label Unhelpful unless the comment explicitly addresses the generator.
- Always verify the comment's claims against the actual code before labeling as Wrong.

---

## Example

**Comment:** "This will crash on Python 2. dict.items() returns a list, not a view."
**Context:** The code runs exclusively on Python 3.

| Field | Value | Reasoning |
|---|---|---|
| quality | **wrong** | The claim is factually incorrect about the runtime environment. The code runs on Python 3 where dict.items() returns a view. The comment bases its criticism on the wrong runtime. |
