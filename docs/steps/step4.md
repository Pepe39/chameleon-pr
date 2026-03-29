# Step 4: Browse the Repository (Only If Needed)

## What to Do

> This step is only performed when the comment requires context beyond the files changed by the PR.

1. Click on `repo_url` to open the repository at the exact commit of the PR (`head_sha`).
2. Explore the files that the comment references or implies:
   - **Imports and shared utilities** — functions used in the diff but defined in other files
   - **Base classes or interfaces** — if the changed code inherits from or implements something
   - **Configuration files** — configs that could affect the code's behavior
   - **Tests** — existing tests that might break with the changes
   - **API contracts** — definitions in other modules that the changed code consumes or exposes
3. Make sure you are viewing the correct snapshot of the repo (the PR's commit, not `main`).

## Goal of This Step

Verify the comment's claims that require knowledge outside the diff. If a comment says "this breaks the contract with the base class," you need to go look at that base class. This step also helps you determine the correct `context_scope` — if you needed to come here, the scope is at least `repo`.
