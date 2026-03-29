# Deliverables Template

Reference for the expected structure of each deliverable file generated in `tasks/{date}/{id}/deliverables/`.

---

## labels.json

The structured output for submission. Contains all four axis labels and the context evidence array.

```json
{
  "quality": "helpful | unhelpful | wrong",
  "severity": "nit | moderate | critical",
  "context_scope": "diff | file | repo | external",
  "context": [
    {
      "diff_line": "line_or_range (string) or null",
      "file_path": "repo-relative path (string)",
      "why": "short phrase explaining why this context matters (string)"
    }
  ],
  "advanced": true | false
}
```

**Rules:**
- 2-space indentation
- `advanced` is a boolean, not a string
- `diff_line` is a string (e.g., `"42"`, `"83-120"`) or `null`; never a number
- `context` must have at least 1 entry when context_scope is `diff`, `file`, or `repo`
- `context` may be `[]` when context_scope is `external`

---

## quality.md

Justification for Axis 1 (Quality). The Reasoning section is pasted directly into the annotation platform.

```markdown
# Quality: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{helpful | unhelpful | wrong}**

## Reasoning
{Self-contained justification. 2-3 sentences explaining:
- What led to this label
- What evidence from the code/diff supports the decision
- If borderline, why one label was chosen over another}
```

---

## severity.md

Justification for Axis 2 (Severity). The Reasoning section is pasted directly into the annotation platform.

```markdown
# Severity: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{nit | moderate | critical}**

## Reasoning
{Self-contained justification. 2-3 sentences explaining:
- What the underlying issue is
- Why this severity level was chosen
- Likelihood of occurrence and impact if it occurs}
```

---

## context_scope.md

Justification for Axis 3 (Context Scope). Includes the context evidence table. The Reasoning section is pasted directly into the annotation platform.

```markdown
# Context Scope: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{diff | file | repo | external}**

## Context Evidence
| diff_line | file_path | why |
|---|---|---|
| {line_or_range or null} | {repo-relative path} | {short phrase} |

## Reasoning
{Self-contained justification. 2-3 sentences explaining:
- What the broadest level of context needed was and why
- Which specific files or lines outside the diff (if any) were required}
```

**Notes on Context Evidence:**
- At least 1 row when label is `diff`, `file`, or `repo`
- Table may have no rows when label is `external` (knowledge comes from outside the repo)
- Must match the `context` array in labels.json

---

## advanced.md

Justification for Axis 4 (Advanced). The Reasoning section is pasted directly into the annotation platform.

```markdown
# Advanced: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{true | false}**

## Reasoning
{Self-contained justification. 1-2 sentences explaining:
- Whether the comment could be made from the diff alone
- If true, which specific criterion it meets (repo conventions, external context, recent language/library updates, or better implementation approach)}
```
