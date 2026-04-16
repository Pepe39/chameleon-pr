# Axis 4: Advanced

Determine whether the comment goes beyond what is obvious from reading the changed lines alone. This label is **derived automatically from Context Scope**.

---

## Mapping Rule

Once Context Scope is determined in step 06, Advanced follows this deterministic mapping:

| Context Scope | Advanced |
|---|---|
| **diff** | False |
| **file** | False |
| **repo** | True (select the specific beyond-diff category) |
| **external** | True (select the specific beyond-diff category) |

You do not need to evaluate Axis 3 and Axis 4 separately. Once you determine the Context Scope, the value of Advanced is automatically determined by this rule.

---

## Why This Mapping Works

Axis 4 asks: "Does the comment require knowledge beyond the files changed in the PR?"

The files touched by the PR include:
- The changed lines (the diff)
- The unchanged lines of those same files

Therefore:
- **Diff** and **File** are within the PR's files. They do not require going "beyond." Advanced is **False**.
- **Repo** and **External** are outside the PR's files. They require going "beyond." Advanced is **True**.

---

## Beyond-Diff Categories (when Advanced = True)

When Context Scope is `repo` or `external`, select the category that best explains why the comment requires knowledge beyond the PR's files:

| Category (platform value) | What to look for |
|---|---|
| **Repo-specific conventions** | Pertains to conventions, patterns, or architectural decisions specific to this repository that are not universally known. |
| **Context outside changed files** | Requires knowledge from files not touched by the PR (base classes, shared utilities, configs, API contracts). |
| **Recent language/library updates** | Requires awareness of recent or non-obvious language features, library behavior, deprecations, or framework semantics. |
| **Better implementation approach** | Suggests a meaningfully better way to implement, not just style but a fundamentally improved design, algorithm, or API usage. |

If more than one category applies, pick the primary driver.

---

## Example

**Comment:** "You should use `useCallback` here to avoid unnecessary re-renders of the child component `ExpensiveList`, which is memoized with `React.memo` in `components/ExpensiveList.tsx`."
**Context:** The PR adds an inline `onClick` handler in `Dashboard.tsx`. The file `ExpensiveList.tsx` is not part of the PR. Context Scope is `repo`.

| Field | Value | Reasoning |
|---|---|---|
| advanced | **Context outside changed files** | Context Scope is repo because the reviewer needed to know that `ExpensiveList` is memoized in a file not touched by the PR. The mapping rule gives Advanced = True, and the primary driver is knowledge from an untouched file. |

---

**Counter-example:**

**Comment:** "Missing semicolon at the end of line 15."
**Context:** The typo is visible directly in the diff. Context Scope is `diff`.

| Field | Value | Reasoning |
|---|---|---|
| advanced | **False** | Context Scope is diff. The mapping rule gives Advanced = False. |
