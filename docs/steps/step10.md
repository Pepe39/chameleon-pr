# Step 10: Record and Submit Labels

## What to Do

1. Compile your labels into the JSON output format. The `addressed` field is always present and uses the 4-value enum. `empty` is selected ONLY when the PR is OPEN. Closed PRs (merged or closed without merge) get one of `addressed`, `ignored`, `false_positive`.

```json
{
  "quality": "helpful | unhelpful | wrong",
  "addressed": "empty | addressed | ignored | false_positive",
  "severity": "nit | moderate | critical",
  "context_scope": "diff | file | repo | external",
  "context": [
    {
      "diff_line": "45",
      "file_path": "src/handlers/user.py",
      "why": "Short description of why this context matters"
    }
  ],
  "advanced": "False | Repo-specific conventions | Context outside changed files | Recent language/library updates | Better implementation approach"
}
```

2. Before submitting, run this final checklist:

- [ ] Verified that the comment in the discussion matches the `body` field
- [ ] Quality is based on factual correctness and usefulness, not personal opinion
- [ ] Addressed is one of the 4 enum values. `empty` ONLY on OPEN PRs. Closed PRs (merged or not) get one of `addressed`, `ignored`, `false_positive`
- [ ] Severity rates the issue itself, not the tone of the comment
- [ ] Context scope reflects the broadest level of context needed
- [ ] The context array lists all pieces of evidence used
- [ ] Advanced is the string enum value, not `true/false`
- [ ] `repo` or `external` scope is never paired with `advanced = "False"`
- [ ] All five axes were evaluated independently

3. Submit your labels in the annotation platform.

## Goal of This Step

Produce a complete, consistent, and verified record of your labels. The final checklist prevents the most common errors such as coupling Quality with Severity, inflating the scope, or pairing `repo` scope with `advanced = "False"`.
