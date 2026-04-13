# step-01-parse-inputs

## What it does
Parses the task variables pasted by the user into `inputs.md` and populates `task_info.md` with structured data.

## Prerequisites
- Task directory created by `/run`
- User has pasted task variables into `inputs.md`

## Context
> See `docs/steps/step0.md` for reference on input fields.

## Arguments
- `id` (required): Task ID. E.g.: 2937204136

## Instructions

### 1. Recover context

Find the task:
```
find tasks/ -maxdepth 2 -type d -name "{id}"
```
Read `inputs.md` from the task directory.

If `progress.md` exists, update: step 01 status = "in-progress", Started = {timestamp ISO 8601}.

### 2. Validate inputs

Read `tasks/{date}/{id}/inputs.md` and extract all fields:
- `pull_request_url` — must be a valid GitHub PR URL
- `nwo` — must be in `owner/repo` format
- `head_sha` — must be a commit hash
- `comment_id` — must be a numeric ID
- `body` — the review comment text (required, can be multi-line)
- `file_path` — path to the file in the repo
- `diff_line` — numeric line number
- `discussion_url` — must be a valid GitHub URL
- `repo_url` — must be a valid GitHub URL
- `coding_language` — programming language name

**Validation rules:**
- All fields must be filled (not "(paste here)" or empty)
- URLs must start with `https://github.com/`
- If any field is missing or invalid, tell the user which field needs fixing and STOP

### 3. Populate task_info.md

Update `tasks/{date}/{id}/task_info.md`:

```markdown
# Task: {id}

## Status
Created: {timestamp}
Step 01 completed: {timestamp}

## Input Data
- **PR URL:** {pull_request_url}
- **Repository:** {nwo}
- **Head SHA:** {head_sha}
- **Comment Commit:** (populated after step 02)
- **Comment ID:** {comment_id}
- **File Path:** {file_path}
- **Diff Line:** {diff_line}
- **Language:** {coding_language}
- **Discussion URL:** {discussion_url}
- **Repo URL:** {repo_url}

### Review Comment
> {body}

## Analysis
(populated after steps 02-03)

## Labels
(populated after steps 04-07)

## Output
(populated after step 08)
```

### 4. Update progress

Update `progress.md`: step 01 status = "done", Completed = {timestamp ISO 8601}, Current Step = 02 - Analyze PR.
