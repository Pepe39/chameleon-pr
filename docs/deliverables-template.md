# Deliverables Template

Reference for the expected structure of each deliverable file generated in `tasks/{date}/{id}/deliverables/`.

---

## labels.json

The structured output for submission. Contains all five axis labels and the context evidence array. The `addressed` field is always present and uses one of four enum values. `empty` is selected ONLY on OPEN PRs. Closed PRs, including closed-without-merge, get one of `addressed`, `ignored`, or `false_positive`.

```json
{
  "quality": "helpful | unhelpful | wrong",
  "addressed": "empty | addressed | ignored | false_positive",
  "severity": "nit | moderate | critical",
  "context_scope": "diff | file | repo | external",
  "context": [
    {
      "diff_line": "line_or_range (string) or null",
      "file_path": "repo-relative path (string)",
      "why": "short phrase explaining why this context matters (string)"
    }
  ],
  "advanced": "False | Repo-specific conventions | Context outside changed files | Recent language / library updates | Better implementation approach"
}
```

**Rules:**
- 2-space indentation
- `advanced` is a string enum, not a boolean. One of the five values `False`, `Repo-specific conventions`, `Context outside changed files`, `Recent language / library updates`, `Better implementation approach`
- `addressed` is a string enum with four values. `empty`, `addressed`, `ignored`, `false_positive`. The value `empty` is an active selection used ONLY when the PR is OPEN. Closed PRs (merged or closed-without-merge) get one of the other three. The field is always present in `labels.json`
- `diff_line` is a string like `"42"` or `"83-120"`, or `null`. Never a number
- `context` must have at least 1 entry when context_scope is `diff`, `file`, or `repo`
- `context` may be `[]` when context_scope is `external`
- Hard rule. If `context_scope` is `repo` or `external`, then `advanced` must not be `False`. That combination is invalid by definition because crossing the diff boundary is itself beyond-diff knowledge
- Hard rule. If `addressed` is `empty`, the PR must be OPEN. If `addressed` is one of `addressed`, `ignored`, `false_positive`, the PR must be closed (merged or closed-without-merge). Mismatch is invalid

---

## quality.md

Justification for the Quality axis. The Reasoning section is pasted directly into the annotation platform.

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

## addressed.md

Justification for the Addressed axis. Always generated. Uses one of four enum values. The Reasoning section is pasted directly into the annotation platform.

```markdown
# Addressed: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{empty | addressed | ignored | false_positive}**

## Reasoning
{Self-contained justification. 2-3 sentences explaining:
- For `empty`, state that the PR is OPEN and the final state needed to evaluate the other values does not exist yet
- For `addressed`, name the specific commit, reply, or code change that shows the outcome
- For `ignored`, confirm no reply and no relevant code change in the merged state
- For `false_positive`, cite the reviewer or author reply that dismissed the comment}
```

---

## severity.md

Justification for the Severity axis. The Reasoning section is pasted directly into the annotation platform.

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

Justification for the Context Scope axis. Includes the context evidence table. The Reasoning section is pasted directly into the annotation platform.

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

Justification for the Advanced axis. The Reasoning section is pasted directly into the annotation platform.

```markdown
# Advanced: {id}

- **Comment:** {first 80 chars of body}...
- **File:** {file_path}:{diff_line}
- **PR:** {pull_request_url}

## Label
**{False | Repo-specific conventions | Context outside changed files | Recent language / library updates | Better implementation approach}**

## Reasoning
{Self-contained justification. 1-2 sentences explaining:
- The Context Scope from the preceding step
- The resulting Advanced value from the deterministic mapping
- If the value is not `False`, name the specific beyond-diff knowledge the reviewer relied on}
```
