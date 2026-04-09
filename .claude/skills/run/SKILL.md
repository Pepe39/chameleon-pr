---
description: Single entry point for code review labeling tasks. Creates new tasks or resumes existing ones.
user_invocable: true
---

# /run - Single entry point for code review labeling tasks

Creates new tasks or resumes existing ones from where they left off.

## Arguments
- `$ARGUMENTS` (positional): Task ID, optionally followed by `auto`. E.g.: `/run 2937204136` or `/run 2937204136 auto`
- **`auto` mode (bypass):** When the second token is `auto`, the skill runs the full pipeline non-interactively: do NOT ask the user anything, do NOT wait for confirmations, do NOT pause between steps. This mode is used when the API / extension invokes the skill via `claude -p`. Manual console runs (no `auto`) keep the interactive prompts.

## Ground Rule

**Task isolation:** During task execution, focus only on the task (PR, diff, comment, labeling). Do not modify project docs, guides, commands, or templates. If you notice a pipeline issue, finish the task first, then report it.

## Instructions

### 1. Locate task

Check if task exists: `find tasks/ -maxdepth 2 -type d -name "{id}" 2>/dev/null`
(use only the task id, not the full `$ARGUMENTS`, since it may include `auto`).
- If find returns a path -> task EXISTS (go to 1a)
- If find returns nothing -> task DOES NOT exist (go to 2a)

**IMPORTANT:** Do NOT use glob with `ls tasks/*/ID/` as quotes around the path
prevent `*` expansion and cause false negatives. Always use `find`.

### 1a. Idempotency check (BEFORE doing anything else)

If the task dir was found, IMMEDIATELY check whether the four deliverable files
already exist on disk and are non-empty:

```bash
DIR=<path returned by find>
ALL=1
for f in quality.md severity.md context_scope.md advanced.md; do
  if [ ! -s "$DIR/deliverables/$f" ]; then ALL=0; break; fi
done
[ $ALL -eq 1 ] && echo ALREADY_DONE
```

- If `ALREADY_DONE` is printed -> the task is already labeled. Do **NOT** touch
  any file. Do NOT bootstrap `progress.md`. Do NOT run any step. Print:
  `Task {id} already labeled (deliverables present on disk). Skipping.` and STOP
  immediately. The API reads the deliverables from disk; nothing else is needed.
- If any file is missing -> continue to 2b or 2c as normal.

**Why:** the API can re-invoke `/run {id} auto` for tasks that were produced in
earlier sessions. Rerunning the pipeline would waste work and may produce
different labels for an already-validated task. Idempotency is mandatory in
auto mode AND in interactive mode.

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
| 09 | Recheck | pending | | |
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
7. **Interactive mode only:** Tell the user "Paste your task variables into `inputs.md` and confirm when ready." then wait for confirmation.
8. **Auto mode:** assume `inputs.md` is already populated by the API; continue immediately to step 3 without waiting.

### 2b. If task exists but has NO progress.md -> Bootstrap

1. Create `progress.md` with all steps as "pending"
2. Continue to step 3

### 2c. If task exists and HAS progress.md -> Read it

Read `tasks/{date}/{id}/progress.md`. Extract Current Step and Status.

### 3. Show summary

```
== Task {id} ==
Steps completed: {N}/9
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
| 09 | step-09-recheck |

### 5. Execute step

Read `.claude/skills/{step-command}.md` and follow ALL instructions from that file with `id={id}`.

### 6. After the step

1. Update progress.md (each step already does this when finishing)
2. Show: "Step {N} completed. Next: {N+1} - {name}"
3. **Interactive mode:** Ask "Continue with the next step? (yes/no)". If yes -> back to step 4. If no -> section 7 (Cleanup), then show "To resume: `/run {id}`".
4. **Auto mode:** Do NOT ask. Loop straight back to step 4 with the next pending step until all 9 steps are `done`, then proceed to section 7 (Cleanup) and stop. If step 09 emits `RECHECK_FAILED`, stop immediately and surface the failure. Do NOT proceed to cleanup.

### 7. Cleanup

After the pipeline completes (all steps done) or when the user declines to continue, clean up the cloned repository:

```bash
REPO_DIR="tasks/{date}/{id}/work/repo"
if [ -d "$REPO_DIR" ]; then
  rm -rf "$REPO_DIR"
  echo "Cleaned up repo clone at $REPO_DIR"
fi
```

This cleanup runs regardless of whether all steps completed or the user stopped early.
