# Step 10: Record and Submit Labels

## What to Do

1. Compile your 4 labels into the JSON output format:

```json
{
  "quality": "helpful | unhelpful | wrong",
  "severity": "nit | moderate | critical",
  "context_scope": "diff | file | repo | external",
  "context": [
    {
      "diff_line": "45",
      "file_path": "src/handlers/user.py",
      "why": "Short description of why this context matters"
    }
  ],
  "advanced": true | false
}
```

2. Before submitting, run this final checklist:

- [ ] Verified that the comment in the discussion matches the `body` field
- [ ] Quality is based on factual correctness and usefulness, not personal opinion
- [ ] Severity rates the issue itself, not the tone of the comment
- [ ] Context scope reflects the broadest level of context needed
- [ ] The context array lists all pieces of evidence used
- [ ] Advanced is based on the source of knowledge, not the difficulty
- [ ] All four axes were evaluated independently

3. Submit your labels in the annotation platform.

## Goal of This Step

Produce a complete, consistent, and verified record of your labels. The final checklist prevents the most common errors (such as coupling Quality with Severity or inflating the scope).
