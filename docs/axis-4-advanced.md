# Axis 4: Advanced

Determine whether the comment goes beyond what is obvious from reading the changed lines alone. This is a **binary label**.

---

## Possible Values

| Value | Definition |
|---|---|
| **true** | The comment requires deeper knowledge or reasoning beyond the diff. |
| **false** | The comment is obvious from reading the changed lines alone. |

---

## How to Evaluate

### Label `true` if the comment meets ONE OR MORE of these criteria:

| Criterion | Description |
|---|---|
| **Repo-Specific Conventions** | Pertains to conventions, patterns, or architectural decisions specific to this repository that are not universally known. |
| **Context Outside Changed Files** | Requires knowledge from files not touched by the PR (base classes, shared utilities, configs, API contracts). |
| **Recent Language / Library Updates** | Requires awareness of recent or non-obvious language features, library behavior, deprecations, or framework semantics. |
| **Better Implementation Approach** | Suggests a meaningfully better way to implement — not just style, but a fundamentally improved design, algorithm, or API usage. |

### Label `false` if:

- The issue is visible directly in the diff (typos, syntax errors, obvious logic bugs).
- A reviewer could make this comment by reading only the changed lines.
- Even if the comment is insightful, if it is derivable from the diff alone -> `false`.

### Key Rules

- Do not confuse "requires thinking" with "advanced." A complex but visible logic error in the diff is `false`.
- Advanced is about the **source of knowledge**, not the difficulty of the analysis.

---

## Example

**Comment:** "You should use `useCallback` here to avoid unnecessary re-renders of the child component `ExpensiveList`, which is memoized with `React.memo` in `components/ExpensiveList.tsx`."
**Context:** The PR adds an inline `onClick` handler in `Dashboard.tsx`. The file `ExpensiveList.tsx` is not part of the PR.

| Field | Value | Reasoning |
|---|---|---|
| advanced | **true** | The reviewer needed to know that `ExpensiveList` is memoized with `React.memo` in a file not touched by the PR. Without that repo knowledge, there would be no reason to suggest `useCallback`. The comment goes beyond what is visible in the diff. |

---

**Counter-example:**

**Comment:** "Missing semicolon at the end of line 15."
**Context:** The typo is visible directly in the diff.

| Field | Value | Reasoning |
|---|---|---|
| advanced | **false** | Any reviewer can spot this by reading only the changed lines. No additional knowledge is required. |
