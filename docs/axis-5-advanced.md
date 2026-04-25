# Axis 5: Advanced

Determine whether the comment goes beyond what is obvious from reading the changed lines alone, and if so, which kind of beyond-diff knowledge the reviewer relied on.

**Advanced is a 5-value enum, not a boolean.** Earlier guidance treated it as `true/false`. That is no longer correct. You must pick exactly one of these five string values:

- `False`
- `Repo-specific conventions`
- `Context outside changed files`
- `Recent language / library updates`
- `Better implementation approach`

The label is **derived automatically from Context Scope** via the mapping below.

---

## Mapping Rule

Once Context Scope is determined in step 06, Advanced follows this deterministic mapping:

| Context Scope | Advanced |
|---|---|
| **diff** | `False` |
| **file** | `False` |
| **repo** | one of the four beyond-diff values |
| **external** | one of the four beyond-diff values |

You do not need to evaluate Context Scope and Advanced separately. Once you determine the Context Scope, whether Advanced is `False` or one of the four beyond-diff values is automatically determined by this rule.

**Hard rule.** `context_scope = "repo"` with `advanced = "False"` is internally inconsistent. Crossing the diff boundary is itself beyond-diff knowledge. Same for `external` with `False`. If you reach that combination, one of the two labels is wrong.

---

## Why This Mapping Works

Axis 5 asks. Does the comment require knowledge beyond the files changed in the PR?

The files touched by the PR include:
- The changed lines, that is the diff
- The unchanged lines of those same files

Therefore:
- **Diff** and **File** are within the PR's files. No beyond-diff knowledge needed. Advanced is `False`.
- **Repo** and **External** are outside the PR's files. Beyond-diff knowledge was needed. Advanced is one of the four non-False values.

---

## Beyond-Diff Values

When Context Scope is `repo` or `external`, pick the value that best explains which kind of beyond-diff knowledge the reviewer relied on:

| Value | What to look for |
|---|---|
| **Repo-specific conventions** | Pertains to conventions, patterns, or architectural decisions specific to this repository that are not universally known. |
| **Context outside changed files** | Requires knowledge from files not touched by the PR. Base classes, shared utilities, configs, API contracts. |
| **Recent language / library updates** | Requires awareness of recent or non-obvious language features, library behavior, deprecations, or framework semantics. |
| **Better implementation approach** | Suggests a meaningfully better way to implement. Not just style, but a fundamentally improved design, algorithm, or API usage. |

If more than one value applies, pick the primary driver. When in doubt between `Repo-specific conventions` and `Context outside changed files`, ask. Was the knowledge a general convention, that points to `Repo-specific conventions`, or a specific untouched file the reviewer needed to open, that points to `Context outside changed files`.

---

## Example

**Comment:** "You should use `useCallback` here to avoid unnecessary re-renders of the child component `ExpensiveList`, which is memoized with `React.memo` in `components/ExpensiveList.tsx`."
**Context:** The PR adds an inline `onClick` handler in `Dashboard.tsx`. The file `ExpensiveList.tsx` is not part of the PR. Context Scope is `repo`.

| Field | Value | Reasoning |
|---|---|---|
| advanced | **Context outside changed files** | Context Scope is `repo` because the reviewer needed to know that `ExpensiveList` is memoized in a file not touched by the PR. The mapping rule gives one of the four beyond-diff values, and the primary driver is knowledge from an untouched file. |

---

**Counter-example:**

**Comment:** "Missing semicolon at the end of line 15."
**Context:** The typo is visible directly in the diff. Context Scope is `diff`.

| Field | Value | Reasoning |
|---|---|---|
| advanced | **False** | Context Scope is `diff`. The mapping rule gives `False`. |
