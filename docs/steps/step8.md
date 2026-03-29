# Step 8: Label Axis 3 — Context Scope

## What to Do

1. Ask yourself: "What would the reviewer need to read to make this comment with confidence?"
2. Assign the broadest level needed:

| Level | The reviewer needed... |
|---|---|
| **diff** | Only the changed lines in the PR (can span multiple files) |
| **file** | Code beyond the diff but within files touched by the PR |
| **repo** | Files NOT changed by the PR |
| **external** | Knowledge outside the repository (API docs, RFCs, business requirements) |

3. Fill in the `context` array with each piece of evidence the reviewer used:
   - `diff_line`: line number or range (or `null` if not applicable)
   - `file_path`: repo-relative path to the file
   - `why`: short phrase explaining why this context matters

4. If the scope is `external`, the `context` array may be empty.

## Goal of This Step

Document where the knowledge needed to make the comment comes from. This is not about where the comment appears, but about what information the reviewer needed to consult. If the comment is on a diff line but the reviewer needed to read another file to verify it, the scope is `repo`, not `diff`.
