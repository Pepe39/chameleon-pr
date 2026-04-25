# Axis 2: Addressed

Determine whether the review comment was addressed. The platform exposes a 4-value enum on every task. The fourth value `empty` is selected on PRs that are not merged, since the merge state needed to evaluate `addressed`, `ignored`, or `false_positive` does not exist yet.

`step-045-label-addressed` always runs and writes one of the four values. Step-08 always emits `addressed.md` and the field is always present in `labels.json`.

---

## Possible Values

| Value | Definition |
|---|---|
| **empty** | The PR is not merged. The merge state needed to choose between `addressed`, `ignored`, or `false_positive` does not exist yet. This is an active selection on the platform, not the absence of a label. Used when `state == OPEN` or the PR is closed without merging. |
| **addressed** | The codebase was changed in a way that addresses the underlying problem or concern raised in the comment. If the comment was not valid and will be addressed later or in another PR, it is also considered as addressed. |
| **ignored** | The comment was neither addressed nor indicated to be incorrect, invalid, or unnecessary. The content was not changed in any way that was influenced by the comment, and no one indicated an intention to address the comment now or in the future. |
| **false_positive** | The developer or another participant commented or otherwise indicated that the comment was incorrect, invalid, or unnecessary. |

---

## How to Evaluate

Use this decision tree:

```
Is the PR open or closed without merging?
  → Yes → EMPTY
  → No, PR is merged ↓

Did someone reply saying the comment was incorrect, invalid, or unnecessary?
  → Yes → FALSE_POSITIVE
  → No ↓

Was the code changed in a way that addresses the concern raised in the comment?
  → Yes → ADDRESSED
  → No ↓

The comment was not acted upon and no one dismissed it.
  → IGNORED
```

### Key Rules

- Compare the comment's suggestion against what was **actually merged**, not against HEAD of the branch at the time of the comment. Follow the thread all the way to the merged state.
- The fix does not have to match the reviewer's exact suggestion. Any merged change that resolves the underlying concern counts as `addressed`.
- Statements like `will fix later` or `fixed in another PR` from the author still count as `addressed`, because the comment is acknowledged and committed to.
- `false_positive` requires an **explicit rebuttal**. The PR author or another reviewer must explain why the comment does not apply, is based on a misunderstanding, or points to a non-issue. Silence is not rebuttal.
- `ignored` is the default when the code did not change and no one dismissed the comment. It is the honest "no action was taken" label, not a judgment.

### Disambiguation. `addressed` vs `false_positive`

Both involve a reply. The difference:

- `addressed`. Someone acknowledged the comment and either fixed it or promised to fix it. Intent is to act.
- `false_positive`. Someone pushed back on the comment. Intent is to **not** act, because the premise is wrong.

If the reply agrees with the comment but explains the fix is deferred, it is `addressed`. If the reply disagrees and the code stays the same for that reason, it is `false_positive`.

### Disambiguation. `ignored` vs `false_positive`

Both involve the code not changing. The difference:

- `ignored`. No one replied. The comment was posted, nobody touched the code, nobody dismissed it.
- `false_positive`. Someone replied explicitly saying the comment was wrong, invalid, or unnecessary.

The presence of an explicit rebuttal is what separates the two.

---

## Writing a Good Addressed Justification

Three rules:

1. **Self-contained.** Explain whether and how the comment was addressed using only evidence from the PR discussion and the merged code. Do not mention quality, severity, context scope, or advanced. Those are separate axes.
2. **Specific, not generic.** Name the specific commit, code change, or reply that demonstrates how the comment was handled. "The comment was addressed" without evidence is not a justification.
3. **Check the final merged state.** Compare the comment's suggestion against what was actually merged. A comment can be `addressed` even if the exact suggestion was not followed. What matters is whether the underlying concern was resolved.

### Weak versus strong justifications

**WEAK, too generic**

> The comment was addressed in a later commit.

No evidence. Which commit. What change. How did it address the concern.

**STRONG, names the evidence**

> The author pushed commit `a4f2e1` that replaced the raw SQL string in `users_repo.py` with a parameterized query, which is the fix the reviewer suggested.

Names the commit, the file, and the concrete change.

**WEAK, mixes axes**

> The comment is helpful and was addressed in the merged code.

Mentions quality. Strip the quality reference.

**STRONG, stays in the Addressed axis**

> The merged code on `users_repo.py` line 142 switched from string interpolation to `execute` with positional parameters, which eliminates the injection surface the comment flagged.

Just the evidence for Addressed.

---

## Example

**Comment:** "This function should sort the output for stable iteration order across Python versions."
**Context:** The PR was merged. The author replied saying they would fix it in a follow-up PR, and did so two days later in PR 4521.

| Field | Value | Reasoning |
|---|---|---|
| addressed | **addressed** | The author explicitly committed to the fix in the thread and followed through in PR 4521. The commitment itself counts as `addressed` even though the sort call was not added in this PR. |

**Counter-example:**

**Comment:** "This will break authentication for OAuth users because `req.user` is null for them."
**Context:** The PR author replied: "OAuth users go through `middleware/oauth.js` before reaching this handler, so `req.user` is always populated here. No fix needed." The code was merged unchanged. The middleware claim is accurate.

| Field | Value | Reasoning |
|---|---|---|
| addressed | **false_positive** | The PR author explicitly pushed back on the comment's premise, pointed to the middleware that populates `req.user` for OAuth, and the claim holds up. The comment was dismissed, not deferred. |
