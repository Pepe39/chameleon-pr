# Step 3: Review the Diff and Changed Files

## What to Do

1. From the discussion view, click on the **file name** at the top of the diff hunk.
2. This takes you to the PR's **"Files Changed"** tab.
3. Use the `diff_line` value to locate the specific line where the comment is anchored.
4. Read **all diff hunks** across all changed files, not just the file where the comment was made.
5. Pay attention to:
   - What code was added, removed, or modified
   - How the changes relate to each other across files
   - The overall intent of the PR (what problem it solves, what feature it adds)

## Goal of This Step

Build a comprehensive understanding of what the PR changes. Many review comments only make sense when you understand the full change, not just the individual line where the comment was made. Reading the entire diff allows you to evaluate whether the comment is correct, relevant, and appropriately severe.
