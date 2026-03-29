# Step 0: Receive and Open the Task

## What to Do

1. Open your assigned task in the annotation platform.
2. You will receive a JSON object containing the code review comment data to label.
3. Identify the key fields in the input:

| Field | Purpose |
|---|---|
| `pull_request_url` | URL of the Pull Request on GitHub |
| `nwo` | Repository name (org/repo) |
| `head_sha` | Exact commit of the PR |
| `file_path` | File where the comment is located |
| `diff_line` | Specific diff line where the comment is anchored |
| `body` | The text of the comment you need to label |
| `discussion_url` | Direct link to the comment on the PR |
| `repo_url` | Link to the repo tree at the correct commit |

4. Read the `body` field — this is the review comment you need to evaluate and label.

## Goal of This Step

Familiarize yourself with the input data and understand what information is available before you start navigating the PR.
