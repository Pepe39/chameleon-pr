# Quality Decision Guide

## Decision Tree

```
COMMENT
  |
  v
+---------------------------------------------+
| 1. Is the comment factually incorrect?       |
|    Does it misunderstand the code, suggest    |
|    something that would introduce a bug, or   |
|    make a false claim about the language/     |
|    framework?                                 |
+--------------+--------------+----------------+
              YES             NO
               |               |
               v               v
            WRONG    +---------------------------------+
                     | 2. Does the comment go directly  |
                     |    to the ROOT CAUSE?            |
                     |                                  |
                     |    - Identifies the actual        |
                     |      underlying problem           |
                     |    - Not just a symptom or        |
                     |      side effect                  |
                     |    - Actionable and specific      |
                     |      about the root problem       |
                     +-----------+-----------+----------+
                                YES          NO
                                 |            |
                                 v            v
                     +---------------------+  UNHELPFUL
                     | 3. Is the suggestion |
                     |    accurate against  |
                     |    the full repo?    |
                     |                      |
                     |  - Does the fix or   |
                     |    functionality     |
                     |    already exist?    |
                     |  - Is the proposed   |
                     |    approach actually |
                     |    efficient?        |
                     |  - Would the change  |
                     |    duplicate what    |
                     |    the repo already  |
                     |    provides?         |
                     +----------+----------+
                               YES  NO
                                |    |
                                v    v
                           HELPFUL  UNHELPFUL
```

## Key Distinction: HELPFUL vs UNHELPFUL

| Question | HELPFUL | UNHELPFUL |
|---|---|---|
| Targets the root cause? | Yes | No |
| Factually correct? | Yes | Can also be yes |
| Identifies something real? | Yes, the underlying problem | May identify a real symptom |
| Actionable? | Yes, on the root cause | No, or on something tangential |
| Validated against full repo? | Yes, the suggestion is accurate and not redundant | No; proposes something that already exists or duplicates existing functionality |

## Examples

**HELPFUL:** "This function uses the global `device` instead of receiving it as a parameter, which causes the device mismatch"
- Goes directly to the root cause: the coupling to the global

**UNHELPFUL:** "The input tensor could be on a different device than the model"
- Factually correct, but describes the symptom (the mismatch), not the root cause (the use of the global)

**UNHELPFUL (redundant suggestion):** "The function should accept a `device` parameter to avoid mismatch"
- The repo already has a `get_device()` utility that infers the device from model parameters. The fix already exists; the comment proposes recreating what is already available instead of using it.

**WRONG:** "This function fails because PyTorch does not allow tensors on different devices"
- False: PyTorch does allow it; it raises an error when operating on them

## Common Mistakes

1. Do not assume "factually correct" = helpful. A comment can be true and still unhelpful.
2. Do not assume "unhelpful" = factually incorrect. Unhelpful means it does not target the root cause.
3. A comment can be true, identify a real observation, and still be unhelpful if it points at a symptom instead of the root problem.
4. Always validate the comment's suggestion against the full repo context. If the proposed fix or functionality already exists in the codebase (a utility, a parameter, a pattern), the comment is unhelpful because it proposes redundant work instead of leveraging what is already there.
5. A comment that suggests reimplementing something the repo already provides is unhelpful, even if the underlying problem it identifies is real.
