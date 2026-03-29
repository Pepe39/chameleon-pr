# step-07-label-advanced

## What it does
Labels Axis 4 — Advanced. Determines whether the review comment goes beyond what is obvious from reading the changed lines alone.

## Prerequisites
- Step 06 completed (Context Scope labeled)

## Context
> See `docs/axis-4-advanced.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step9.md` for the step-by-step process.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Comment Analysis" and all Labels so far.

Update `progress.md`: step 07 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Apply the criteria

Ask: "Could a reviewer make this comment by looking only at the changed lines in the diff?"

**Label `true` if the comment meets ONE OR MORE of these criteria:**

| Criterion | What to look for |
|---|---|
| **Repo-Specific Conventions** | Does the comment reference patterns, conventions, or architectural decisions specific to this repo? |
| **Context Outside Changed Files** | Does the comment require knowledge from files not touched by the PR? |
| **Recent Language / Library Updates** | Does the comment require awareness of recent or non-obvious language/framework behavior? |
| **Better Implementation Approach** | Does the comment suggest a fundamentally better design, algorithm, or API usage (not just style)? |

**Label `false` if:**
- The issue is visible directly in the diff (typos, syntax errors, obvious logic bugs)
- A reviewer could make this comment from the changed lines alone
- Even if the comment is insightful, if derivable from the diff alone -> `false`

### 3. Cross-check with Context Scope

Use the Context Scope label from step 06 as a signal (but not a rule):
- If context_scope = `diff` -> Advanced is **likely** `false` (but not always)
- If context_scope = `repo` or `external` -> Advanced is **likely** `true` (but not always)
- If context_scope = `file` -> could go either way

**These are correlations, not rules.** A comment can be `diff` scope but `true` advanced (e.g., it suggests a better algorithm that requires framework expertise). A comment can be `repo` scope but `false` advanced (e.g., a standard code review check like "this import is unused" verified by reading another file).

### 4. Write reasoning

Document in 1-2 sentences:
- Whether the comment could be made from the diff alone
- If `true`, which specific criterion it meets

### 5. Common mistakes to avoid

- **Do NOT confuse "requires thinking" with "advanced."** A complex logic error visible in the diff is `false`.
- **Advanced is about the source of knowledge**, not the difficulty of the analysis.
- **Do NOT mark everything as `true`** just because the comment is non-trivial.

### 6. Update task_info.md

Add to the Labels section:

```markdown
### Advanced
- **Label:** {true | false}
- **Reasoning:** {1-2 sentences explaining the decision}
```

### 7. Update progress

Update `progress.md`: step 07 status = "done", Completed = {timestamp ISO 8601}, Current Step = 08 - Generate Output.
