# /run - Single entry point for code review labeling tasks

Creates new tasks or resumes existing ones from where they left off.

## Arguments
- `$ARGUMENTS` (positional): Task ID. E.g.: `/run 2937204136`

## Instructions

### 1. Locate task

Check if task exists: `find tasks/ -maxdepth 2 -type d -name "$ARGUMENTS" 2>/dev/null`
- If find returns a path -> task EXISTS (go to 2b or 2c)
- If find returns nothing -> task DOES NOT exist (go to 2a)

**IMPORTANT:** Do NOT use glob with `ls tasks/*/ID/` as quotes around the path
prevent `*` expansion and cause false negatives. Always use `find`.

### 2a. If task does NOT exist -> Create task

1. Get current date in YYYY-MM-DD format
2. Create structure:
   ```bash
   mkdir -p tasks/{date}/{id}/deliverables
   mkdir -p tasks/{date}/{id}/work
   ```
3. Generate `tasks/{date}/{id}/inputs.md`:

```markdown
# Task Inputs

Paste your task variables below. Fill in each field from the annotation platform.

## Task Variables

- **pull_request_url:** (paste here)
- **nwo:** (paste here)
- **head_sha:** (paste here)
- **comment_id:** (paste here)
- **body:** (paste here)
- **file_path:** (paste here)
- **diff_line:** (paste here)
- **discussion_url:** (paste here)
- **repo_url:** (paste here)
- **coding_language:** (paste here)
```

4. Generate `tasks/{date}/{id}/progress.md`:

```markdown
# Progress: {id}

**Current Step:** 01 - Parse Inputs
**Status:** pending
**Last Updated:** {timestamp ISO 8601}

| # | Step | Status | Started | Completed |
|---|------|--------|---------|-----------|
| 01 | Parse Inputs | pending | | |
| 02 | Analyze PR | pending | | |
| 03 | Analyze Comment | pending | | |
| 04 | Label Quality | pending | | |
| 05 | Label Severity | pending | | |
| 06 | Label Context Scope | pending | | |
| 07 | Label Advanced | pending | | |
| 08 | Generate Output | pending | | |
```

5. Generate `tasks/{date}/{id}/task_info.md`:

```markdown
# Task: {id}

## Status
Created: {timestamp ISO 8601}

## Input Data
(populated after step 01)

## Analysis
(populated after steps 02-03)

## Labels
(populated after steps 04-07)

## Output
(populated after step 08)
```

6. Confirm: "Task {id} created at tasks/{date}/{id}/"
7. Tell the user: "Paste your task variables into `inputs.md` and confirm when ready."
8. Wait for user confirmation, then continue to step 3.

### 2b. If task exists but has NO progress.md -> Bootstrap

1. Create `progress.md` with all steps as "pending"
2. Continue to step 3

### 2c. If task exists and HAS progress.md -> Read it

Read `tasks/{date}/{id}/progress.md`. Extract Current Step and Status.

### 3. Show summary

```
== Task {id} ==
Steps completed: {N}/8
Next step: {N} - {name} ({status})
```

If status is "in-progress": "NOTE: This step was interrupted. It will be resumed."

### 4. Determine step to execute

Dispatch logic:

1. If Current Step status = "in-progress" -> resume that step (interrupted session)
2. If Current Step status = "pending" -> start that step
3. If Current Step status = "done" -> find the next pending step

**If ALL steps are "done":** Show "All steps completed. Task ready for submission." and stop.

**Step to command mapping:**

| Step | Command |
|---|---|
| 01 | step-01-parse-inputs |
| 02 | step-02-analyze-pr |
| 03 | step-03-analyze-comment |
| 04 | step-04-label-quality |
| 05 | step-05-label-severity |
| 06 | step-06-label-context-scope |
| 07 | step-07-label-advanced |
| 08 | step-08-generate-output |

### 5. Execute step

Read `.claude/commands/{step-command}.md` and follow ALL instructions from that file with `id={id}`.

### 6. After the step

1. Update progress.md (each step already does this when finishing)
2. Show: "Step {N} completed. Next: {N+1} - {name}"
3. Ask: "Continue with the next step? (yes/no)"
4. If yes -> go back to step 4 with the next step
5. If no -> show: "To resume: `/run {id}`"
