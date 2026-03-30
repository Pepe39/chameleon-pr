# step-07-label-advanced

## What it does
Labels Axis 4 — Advanced. Determines whether the review comment goes beyond what is obvious from reading the changed lines alone.

## Prerequisites
- Step 06 completed (Context Scope labeled)

## Context
> See `docs/axis-4-advanced.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step9.md` for the step-by-step process.
> See `DOCUMENTATION.md` sections 8 (FAQ), 9 (Common Mistakes), and 10 (Tips) for edge cases and pitfalls.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Comment Analysis" and all Labels so far.

Update `progress.md`: step 07 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Apply the criteria

Ask: "Could a reviewer make this comment by looking only at the changed lines in the diff?" If yes, the label is `False`. If no, select the specific category that best explains why.

**Select the category that best fits. If more than one applies, pick the primary driver.**

| Category (platform value) | What to look for |
|---|---|
| **Repo-specific conventions** | Does the comment reference patterns, conventions, or architectural decisions specific to this repo? |
| **Context outside changed files** | Does the comment require knowledge from files not touched by the PR? |
| **Recent language/library updates** | Does the comment require awareness of recent or non-obvious language/framework behavior? |
| **Better implementation approach** | Does the comment suggest a fundamentally better design, algorithm, or API usage (not just style)? |
| **False** | The issue is visible directly in the diff and a reviewer could make this comment from the changed lines alone. |

**Label `False` if:**
- The issue is visible directly in the diff (typos, syntax errors, obvious logic bugs)
- A reviewer could make this comment from the changed lines alone
- Even if the comment is insightful, if derivable from the diff alone -> `False`

### 3. Cross-check with Context Scope

Use the Context Scope label from step 06 as a signal (but not a rule):
- If context_scope = `diff` -> Advanced is **likely** `False` (but not always)
- If context_scope = `repo` or `external` -> Advanced is **likely** a specific category (but not always)
- If context_scope = `file` -> could go either way

**These are correlations, not rules.** A comment can be `diff` scope but advanced (e.g., it suggests a better algorithm that requires framework expertise). A comment can be `repo` scope but `False` (e.g., a standard code review check like "this import is unused" verified by reading another file).

### 4. Write reasoning

Document in 1-2 sentences:
- Whether the comment could be made from the diff alone
- If not `False`, which specific category was selected and why

### 5. Common mistakes to avoid

- **Do NOT confuse "requires thinking" with "advanced."** A complex logic error visible in the diff is `False`. (Mistake 5: Marking Everything as Advanced)
- **Advanced is about the source of knowledge**, not the difficulty of the analysis. It requires knowledge most reviewers wouldn't have from the diff alone: repo conventions, untouched files, or non-obvious framework behavior.
- **Do NOT select a category** just because the comment is non-trivial or insightful.
- **If the comment could have been written by seeing only the changed lines, Advanced is `False`**, even if the comment is insightful or well-crafted.
- **If multiple categories apply**, pick the one that is the primary driver of the comment's insight.

### 6. Update task_info.md

Add to the Labels section:

```markdown
### Advanced
- **Label:** {Repo-specific conventions | Context outside changed files | Recent language/library updates | Better implementation approach | False}
- **Reasoning:** {1-2 sentences explaining the decision}
```

### 7. Update progress

Update `progress.md`: step 07 status = "done", Completed = {timestamp ISO 8601}, Current Step = 08 - Generate Output.
