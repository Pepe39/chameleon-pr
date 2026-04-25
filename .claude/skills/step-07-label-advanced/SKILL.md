# step-07-label-advanced

## What it does
Labels Axis 4 — Advanced. Derives the Advanced label from Context Scope using a deterministic mapping.

## Prerequisites
- Step 06 completed (Context Scope labeled)

## Context
> See `docs/axis-5-advanced.md` for the mapping rule and definitions.
> See `DOCUMENTATION.md` section 8 (Axis 5. Advanced) for the rationale.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the Context Scope label from step 06.

If `work/thread.md` exists, the body is a nested reply. Thread context does not change Axis 4 by itself. A reply inside a thread is not automatically advanced. The mapping below still drives the label.

Update `progress.md`: step 07 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Apply the mapping rule

Read the `context_scope` label set in step 06. Apply this deterministic mapping:

| Context Scope | Advanced |
|---|---|
| **diff** | False |
| **file** | False |
| **repo** | True (select the specific beyond-diff category) |
| **external** | True (select the specific beyond-diff category) |

You do not need to evaluate Axis 3 and Axis 4 separately. Once Context Scope is determined, Advanced is automatic.

**Why this mapping works:** Axis 4 asks whether the comment requires knowledge beyond the files changed in the PR. The files touched by the PR include the changed lines (the diff) and the unchanged lines of those same files. Diff and File are within the PR's files, so Advanced is False. Repo and External are outside the PR's files, so Advanced is True.

### 3. Select beyond-diff category (only when True)

If Context Scope is `repo` or `external`, select the category that best explains why:

| Category (platform value) | What to look for |
|---|---|
| **Repo-specific conventions** | Pertains to conventions, patterns, or architectural decisions specific to this repo. |
| **Context outside changed files** | Requires knowledge from files not touched by the PR. |
| **Recent language / library updates** | Requires awareness of recent or non-obvious language/framework behavior. |
| **Better implementation approach** | Suggests a fundamentally better design, algorithm, or API usage (not just style). |

If more than one category applies, pick the primary driver.

### 4. Write reasoning

Document in 1-2 sentences:
- The Context Scope label from step 06
- The resulting Advanced label from the mapping
- If True, which specific category was selected and why

### 5. Update task_info.md

Add to the Labels section:

```markdown
### Advanced
- **Label:** {Repo-specific conventions | Context outside changed files | Recent language / library updates | Better implementation approach | False}
- **Reasoning:** {1-2 sentences explaining the mapping derivation}
```

### 6. Update progress

Update `progress.md`: step 07 status = "done", Completed = {timestamp ISO 8601}, Current Step = 08 - Generate Output.
