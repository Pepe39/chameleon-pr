# Axis 3: Context Scope

Determine what level of context a reviewer would need to confidently make this comment. Choose exactly one scope level. Each level includes everything below it. **Pick the broadest scope needed.**

**Central Question:** "What did the reviewer have to read or know to make this comment?" It is NOT about where the comment appears. It is NOT about where the problematic code is. It IS about what information was needed to identify the issue.

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

- `diff` can span multiple files -- as long as only the changed lines were needed.
- The scope is about **what the reviewer needed to know**, not where the comment appears.
- A comment on a diff line can require `repo` scope if the reviewer needed to read untouched files.
- **Do not conflate analyst verification with reviewer observation.** During analysis you may read the full file or browse the repo to verify a comment's claims. That does not mean the reviewer needed that context to make the comment. The scope reflects what the reviewer minimally needed, not what you consulted.
- **Do not speculate about what Copilot read.** Evaluate what information was needed to make the comment, not what the AI model may have consumed.

### New Files Rule

If the target file is completely new in the PR (diff header shows `@@ -0,0 +1,N @@`, all lines are added, no lines without `+` prefix), the scope is **diff** even if you need to read multiple parts of the file. There is no "file" scope for a file that did not exist before the PR. Everything in a new file is part of the diff.

### Repo Convention Rule

If a comment references a convention or pattern in the codebase:
- If the convention is visible in other lines of the same diff (other added or deleted lines follow the pattern) -> **diff**
- If you need to see unchanged lines within PR-touched files to identify the convention -> **file**
- If you need to see files not touched by the PR to know the convention -> **repo**

### Quick Decision Table

| Question | If YES |
|---|---|
| Can I identify the issue reading ONLY the green/red lines? | **diff** |
| Do I need to see other lines from the SAME file that are NOT in the diff? | **file** |
| Do I need to see OTHER files that the PR does NOT modify? | **repo** |
| Do I need knowledge that is NOT in any file in the repo? | **external** |

### Confusing Cases Resolved

**Case 1: "The comment points to a line in the diff, so it is Diff."** ERROR. Where the comment points does not determine the scope. If you need to see where `self.data` is defined (outside the diff) to understand the comment, the scope is file or repo.

**Case 2: "I need to read the entire file, so it is File."** ERROR. If the file is new in the PR, everything is diff. There is no file scope for files that did not exist.

**Case 3: "The PR touches multiple files."** If the diff includes changes in `file_a.py` and `file_b.py`, and the comment requires cross-referencing information between both, the scope is **diff**. Both files are in the diff, even though they are different files.

**Case 4: "Copilot mentions a repo convention."** If the convention is visible in the diff (other names in the same diff follow the pattern), the scope is **diff**. If you need to see other files to know the convention, the scope is **repo**.

### Common Errors

- **Defaulting to Diff.** The comment's simplicity does not determine the scope. A simple comment may require broad context.
- **Choosing File because the file is large.** The file's size is irrelevant. What matters is whether the lines you need are in the diff or not.
- **Choosing Repo because "Copilot must have read other files."** Do not speculate about what Copilot consumed. Evaluate what information was needed to make the comment.
- **Forgetting the new files rule.** New file means everything is diff. There is no "file" scope for files that did not exist before.

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
