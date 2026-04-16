# step-05-label-severity

## What it does
Labels Axis 2 — Severity. Assesses how severe the issue is that the review comment points out.

## Prerequisites
- Step 04 completed (Quality labeled)

## Context
> See `docs/axis-2-severity.md` for definitions, evaluation criteria, and examples.
> See `docs/steps/step7.md` for the step-by-step process.
> See `DOCUMENTATION.md` sections 9 (FAQ), 10 (Common Mistakes), and 11 (Tips) for edge cases and pitfalls.

**Critical reminder:** Severity measures the **issue itself**, NOT the quality or tone of the comment. These axes are independent.

## Arguments
- `id` (required): Task ID

## Instructions

### 1. Recover context

Read `task_info.md` — specifically the "Review Comment", "Comment Analysis", and the Quality label from step 04.

Update `progress.md`: step 05 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Identify the underlying issue

From the comment analysis, isolate the **issue** the comment is pointing out (regardless of whether the comment is correct about it):

- What problem does the comment claim exists?
- What would the real-world impact be if this issue is genuine?
- If the comment is Wrong (from step 04), still rate the severity of the issue **as described** — not the comment's correctness.

### 3. Apply severity criteria

| Question | If yes |
|---|---|
| Can this issue be safely ignored or deferred without risk? | **nit** |
| Does it affect behavior but is unlikely to cause serious harm? | **moderate** |
| Would a senior engineer insist on fixing this before merge? | **critical** |

Typical mappings:
- **nit:** style, naming, cosmetic, docs, minor code smell
- **moderate:** missing edge cases on uncommon paths, suboptimal but functional logic, missing null checks on rarely-hit paths
- **critical:** security vulnerabilities, data corruption, authentication bypass, race conditions, build-breaking errors, wrong results in core paths

### 4. Write reasoning

Document your reasoning in 2-3 sentences:
- What the underlying issue is
- Why you chose this severity level
- Consider: likelihood of occurrence + impact if it occurs

### 5. Common mistakes to avoid

- **Do NOT let the comment's tone influence severity.** "MUST FIX!" about a naming preference is still `nit`. An urgently worded comment about a style preference is still `nit`. A calmly worded comment about a SQL injection is still `critical`. (Mistake 2)
- **Do NOT couple Quality and Severity.** A Wrong comment about a security vulnerability is `wrong + critical`. A Helpful comment about a naming nit is `helpful + nit`. (Mistake 4)
- **Rate by the most severe issue** if the comment mentions multiple problems.
- **Context matters for the same pattern.** A missing null check in a rarely-used utility is `moderate`; the same check in a payment handler is `critical`.

### 6. Update task_info.md

Add to the Labels section:

```markdown
### Severity
- **Label:** {nit | moderate | critical}
- **Reasoning:** {2-3 sentences explaining the decision}
```

### 7. Update progress

Update `progress.md`: step 05 status = "done", Completed = {timestamp ISO 8601}, Current Step = 06 - Label Context Scope.
