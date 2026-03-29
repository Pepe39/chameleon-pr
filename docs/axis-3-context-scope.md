# Axis 3: Context Scope

Determine what level of context a reviewer would need to confidently make this comment. Choose exactly one scope level. Each level includes everything below it. **Pick the broadest scope needed.**

---

## Possible Values

```
EXTERNAL  — Knowledge outside the repository
    ^
REPO      — Files not touched by the PR
    ^
FILE      — Within PR-touched files, beyond the diff
    ^
DIFF      — Only the changed lines
```

| Value | Definition | Typical Examples |
|---|---|---|
| **diff** | The comment can be made by reading only the PR's changed lines (diff hunks), possibly across multiple changed files. No context beyond the diff is needed. | Typos, obvious syntax errors, clearly wrong constants, style violations visible in the diff alone. |
| **file** | Requires reading beyond the diff hunks but within the file(s) the PR touches. Surrounding functions, imports, class definitions outside the changed lines. | Variable defined elsewhere in the file, contradicting a pattern earlier in the same file, missing import. |
| **repo** | Requires knowledge from files NOT changed by the PR — other source files, configs, tests, docs, or build scripts elsewhere in the repository. | Inconsistency with a shared utility in an untouched file, violating a pattern in a base class the PR doesn't modify. |
| **external** | Requires knowledge outside the repository entirely — API docs, RFCs, language specs, business requirements not documented in the repo. | The product team decided this feature must support offline mode but the implementation assumes constant connectivity. |

---

## How to Evaluate

1. Ask yourself: "What would the reviewer need to read to make this comment?"
2. If they needed diff + file context -> `file`
3. If they also needed a file not touched by the PR -> `repo`
4. If the knowledge comes from outside the repo -> `external`
5. **Always pick the broadest level needed.**

### Key Rules

- `diff` can span multiple files — as long as only the changed lines were needed.
- The scope is about **what the reviewer needed to know**, not where the comment appears.
- A comment on a diff line can require `repo` scope if the reviewer needed to read untouched files.

### How to Record Context

```json
{
  "context_scope": "repo",
  "context": [
    {
      "diff_line": "45",
      "file_path": "src/api/handlers/user.py",
      "why": "The new handler calls validate_email() without importing it"
    },
    {
      "diff_line": null,
      "file_path": "src/utils/validators.py",
      "why": "validate_email() is defined here — not touched by the PR"
    }
  ]
}
```

- If `context_scope` is `"external"`, the `context` array may be empty (`[]`).

---

## Example

**Comment:** "This function duplicates the logic of `formatCurrency()` that already exists in `utils/format.ts`."
**Context:** The PR adds a new function `displayPrice()` in `src/components/Cart.tsx`. The file `utils/format.ts` is not part of the PR.

| Field | Value | Reasoning |
|---|---|---|
| context_scope | **repo** | The reviewer needed to know about a file (`utils/format.ts`) that was not touched by the PR to identify the duplication. |
| context | `[{"diff_line": "23-30", "file_path": "src/components/Cart.tsx", "why": "New displayPrice() function in the diff"}, {"diff_line": null, "file_path": "utils/format.ts", "why": "formatCurrency() already exists here — not touched by the PR"}]` | Both pieces of evidence the reviewer used are listed. |
