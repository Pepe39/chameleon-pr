# Step 9: Label Axis 4. Advanced

> Advanced is a 5-value string enum, not a boolean. Pick exactly one of `FALSE`, `Repo-specific conventions`, `Context outside changed files`, `Recent language/library updates`, `Better implementation approach`.

## What to Do

1. Read the Context Scope label from the preceding step.
2. Apply the deterministic mapping:
   - `diff` or `file` maps to `FALSE`
   - `repo` or `external` maps to one of the four non-FALSE values
3. If Context Scope is `repo` or `external`, pick the value that best describes which beyond-diff knowledge the reviewer relied on:

| Value | Example |
|---|---|
| Repo-specific conventions | "We use the Repository pattern here, not direct ORM access" |
| Context outside changed files | "This breaks the interface defined in `base.ts`" |
| Recent language/library updates | "Since React 18, `useEffect` has different cleanup in StrictMode" |
| Better implementation approach | "You should use a bloom filter here instead of iterating the list" |

4. If more than one value applies, pick the primary driver.

**Hard rule.** `repo` or `external` scope with `advanced = "FALSE"` is invalid. If you reach that combination, one of the two labels is wrong. Go back and re-check scope.

## Goal of This Step

Distinguish between comments that are evident from reading the diff and comments that require deeper knowledge. A complex but visible logic error in the diff is `FALSE`. A simple comment that requires knowing how a base class works in another file is `Context outside changed files`. Advanced measures the source of knowledge, not the difficulty of the analysis.
