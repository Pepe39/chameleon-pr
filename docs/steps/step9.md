# Step 9: Label Axis 4 — Advanced

## What to Do

1. Ask yourself: "Could a reviewer make this comment by looking only at the changed lines in the diff?"
2. If the answer is **yes** -> `false`
3. If the answer is **no**, check whether the comment meets at least one of these criteria:

| Criterion | Example |
|---|---|
| Repo-specific conventions | "We use the Repository pattern here, not direct ORM access" |
| Context from files not touched by the PR | "This breaks the interface defined in `base.ts`" |
| Recent or non-obvious language/library features | "Since React 18, `useEffect` has different cleanup in StrictMode" |
| Fundamentally better implementation approach | "You should use a bloom filter here instead of iterating the list" |

4. If it meets at least one -> `true`. If it meets none -> `false`.

## Goal of This Step

Distinguish between comments that are evident from reading the diff and comments that require deeper knowledge. A complex but visible logic error in the diff is `false`. A simple comment that requires knowing how a base class works in another file is `true`. Advanced measures the source of knowledge, not the difficulty of the analysis.
