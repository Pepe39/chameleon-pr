# Axis 1: Quality

Classify the overall quality of the review comment. Choose exactly one label.

---

## Possible Values

| Value | Definition |
|---|---|
| **helpful** | The comment goes directly to the root cause of the problem. It is technically correct, actionable, targets the actual underlying issue rather than a symptom or side effect, and its suggestion is validated against the full repo (not proposing something redundant or already implemented). |
| **unhelpful** | The comment does not target the root cause, or proposes something redundant. It may be factually correct and identify a real observation, but if it points at a symptom, a side effect, or a tangential concern instead of the actual root problem, it is unhelpful. Also unhelpful if it suggests a fix or functionality that already exists in the repo. Includes pedantic, stylistic, obvious, or not actionable comments. |
| **wrong** | The comment is factually incorrect, suggests a change that would introduce a bug, or misunderstands the code. |

---

## How to Evaluate

```
1. Is the comment factually incorrect?
   Does it misunderstand the code, suggest something that would
   introduce a bug, or make a false claim about the language/framework?
   -> Yes: WRONG

2. Does the comment go directly to the root cause of the problem?
   Does it identify the actual underlying issue, not just a symptom
   or side effect? Is it actionable and specific about the root problem?
   -> No: UNHELPFUL
   -> Yes: continue to 3

3. Is the suggestion accurate against the full repo context?
   Does the proposed fix or functionality already exist in the codebase?
   Would the change duplicate what the repo already provides?
   -> Already exists / redundant: UNHELPFUL
   -> Validated, not redundant: HELPFUL

4. Is the comment factually correct but does NOT target the root cause?
   Does it point at a symptom, a tangential concern, or a side effect
   instead of the actual root problem? Or is it pedantic, obvious,
   stylistic without substance, or not actionable?
   -> UNHELPFUL
```

### Key Rules

- **Wrong** means factually incorrect, NOT "I disagree with the suggestion."
- **Unhelpful** does NOT mean factually incorrect. A comment can be factually true and still unhelpful if it does not target the root cause of the problem. Pointing at a real symptom instead of the root issue is unhelpful.
- **Helpful** requires that the comment goes directly to the root problem AND that the suggestion is validated against the full repo. Identifying a real observation is not enough; it must address the actual underlying cause with a non-redundant suggestion.
- If the comment proposes a fix or functionality that already exists in the repo, it is **Unhelpful**; the correct suggestion would be to use what already exists, not to recreate it.
- Always verify the comment's claims against the actual code before labeling as Wrong.

---

## Example

**Comment:** "This will crash on Python 2 — dict.items() returns a list, not a view."
**Context:** The code runs exclusively on Python 3.

| Field | Value | Reasoning |
|---|---|---|
| quality | **wrong** | The claim is factually incorrect about the runtime environment. The code runs on Python 3, where `dict.items()` returns a view, not a list. The comment bases its criticism on the wrong runtime. |
