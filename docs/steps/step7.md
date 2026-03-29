# Step 7: Label Axis 2 — Severity

## What to Do

1. Evaluate the severity of the **issue itself** the comment points out — not the quality or tone of the comment.
2. Use these guiding questions:

| Question | If yes |
|---|---|
| Can this issue be safely ignored or deferred? | **nit** |
| Should it be improved but won't cause serious harm? | **moderate** |
| Would a senior engineer insist on fixing it before merge? | **critical** |

3. Assign exactly one of: `nit`, `moderate`, or `critical`.

## Goal of This Step

Measure the impact of the issue independently of how the comment is written. An urgently worded comment ("MUST FIX!") about a style preference is still `nit`. A calmly worded comment about a SQL injection is still `critical`. If the comment mentions multiple issues, rate by the most severe one.
