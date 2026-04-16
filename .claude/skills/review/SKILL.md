---
description: Validate deliverables for a completed task. Re-evaluates labels, reasoning, and format.
user_invocable: true
---

# /review - Validate deliverables for a task

Reviews a task's deliverables: re-evaluates each axis label against the evidence, validates reasoning quality, and checks format consistency.

Deliverables are the 4 axis `.md` files copied from the annotation platform.

## Arguments
- `$ARGUMENTS` (positional): Task ID, optionally followed by a mode token: `auto` or `reevaluate`. E.g.: `/review 2937204136`, `/review 2937204136 auto`, `/review 2937204136 reevaluate`.
- **`auto` mode (bypass):** When the second token is `auto`, the skill runs the full review non-interactively. Do NOT ask the user any questions, do NOT wait for confirmations. Apply every recommended fix directly into `fixed_deliverables/`, write `feedback_to_cb.md` and `review_meta.json`, then stop. The API/extension invokes the skill in this mode. Manual console runs (no token) keep the interactive prompts.
- **`reevaluate` mode (sanity-check existing fixes):** When the second token is `reevaluate`, the skill does NOT run the full pipeline. Instead it loads the existing `fixed_deliverables/`, `feedback_to_cb.md`, and `review_meta.json`, and verifies that each proposed fix is internally consistent and supported by the original deliverables, the PR diff at `head_sha`, and the comment under review. The skill behaves non-interactively (no prompts). It must:
  1. Bypass the idempotency check at the top of the skill (do not stop just because `feedback_to_cb.md` exists; that file is the input to reevaluate).
  2. Skip phases 01-06 of the regular pipeline; the only work is validating the proposed fixes.
  3. For each proposed fix, re-derive the answer from scratch using the original deliverables + diff + comment, then compare to the proposed fix.
  4. If every proposed fix is correct: leave `fixed_deliverables/`, `feedback_to_cb.md` and `review_meta.json` UNCHANGED. Do NOT append any reevaluation marker, parenthetical, or trailer to the feedback text. The feedback stays exactly as it was.
  5. If any proposed fix is wrong: rewrite that specific file in `fixed_deliverables/` with the corrected version, and update `feedback_to_cb.md` and `review_meta.json` so the prose reflects the corrected adjustments in past tense, plain prose. Do NOT append any reevaluation marker or trailer.
  6. Always update `review_progress.md` with a new row or set of rows scoped to the reevaluation, so the user can see it ran.
- **Idempotency:** If `feedback_to_cb.md` already exists in the task directory and is non-empty, print `Review already completed for {id}. Skipping.` and STOP immediately. Do not re-run any check. **Exception:** when invoked in `reevaluate` mode, ignore this idempotency rule (the existing feedback is the input to reevaluate, not a reason to skip).
- **Friendly tone:** `feedback_to_cb.md` MUST be written in natural, friendly English, as if you were a colleague leaving a kind note. Avoid jargon dumps and report-style headings.
- **Mandatory `review_meta.json`:** Every review MUST also write `review_meta.json` in the review directory with this exact shape:
  ```json
  {
    "quality_score": <int 1-5>,
    "feedback_text": "<friendly note that will be pasted into the platform Feedback textarea>"
  }
  ```
  Scoring rubric: 5 = Excellent (no fixes needed), 4 = Very Good (minor wording/format), 3 = Good (one label or one reasoning fix), 2 = Needs Work (multiple label fixes or weak reasoning), 1 = Poor (most axes wrong). The `feedback_text` should be a self-contained, plain paragraph (no markdown headings) suitable to paste verbatim into the platform's "Feedback *" field. It can be the same as `feedback_to_cb.md` if that file is already plain prose, or a condensed version of it.

## Progress tracking (mandatory)

Every review run (interactive or auto) MUST maintain a `review_progress.md` file inside the review directory (next to `inputs.md`). Create it on first entry and update it as you advance through each phase.

```markdown
# Review Progress: {id}

**Current Phase:** {phase name}
**Status:** pending|in-progress|done|error
**Last Updated:** {timestamp ISO 8601}

| # | Phase | Status | Started | Completed |
|---|------|--------|---------|-----------|
| 01 | Locate task / load deliverables | pending | | |
| 02 | Repo clone (comment_commit)       | pending | | |
| 03 | Data consistency (C0-C3)          | pending | | |
| 04 | Content validation (V1-V5)        | pending | | |
| 05 | Reasoning validation (R1-R5)      | pending | | |
| 06 | Format & wording checks           | pending | | |
| 07 | Apply fixes (fixed_deliverables/) | pending | | |
| 07A | Consistency recheck (step-09-recheck) | pending | | |
| 08 | Feedback to tasker (+ review_meta.json) | pending | | |
| 09 | Cleanup                           | pending | | |
```

Update the row's `Status`, `Started`, `Completed` columns and the top `Current Phase` line as you progress. Mark `done` only when the phase actually finished. Keep the file even if the review ends in error so the user can see how far it got.

### How to update review_progress.md (mandatory, not optional)

This is a hard requirement. The file MUST be updated using the Edit tool at TWO points for every single phase:

1. **Before** starting phase N: Edit `review_progress.md` to set that phase's `Status` column to `in-progress`, fill its `Started` cell with the current ISO 8601 timestamp, and update the top `**Current Phase:**` line to phase N's name. Also bump `**Last Updated:**`.
2. **After** finishing phase N (right before moving on to phase N+1): Edit `review_progress.md` to flip the phase's `Status` to `done` and fill its `Completed` cell with the current timestamp. Also bump `**Last Updated:**`.

Do NOT batch multiple phase updates at the end of the review. Each phase MUST be flipped to in-progress when it starts and to done when it finishes, before any other tool call for the next phase. If the auto worker dies mid-phase, the progress file must show exactly which phase was in-flight.

Phase-to-section mapping (so you know which phase you are in while reading the instructions below):

| Phase | Section in this file |
|---|---|
| 01 Locate task / load deliverables | Sections 1, 1a, 2 (excluding 2b) |
| 02 Repo clone (comment_commit)      | Section 2b |
| 03 Data consistency (C0-C3)         | Section 3 |
| 04 Content validation (V1-V5)       | Section 4 |
| 05 Reasoning validation (R1-R5)     | Section 5 |
| 06 Format & wording checks          | Sections 6, 7 |
| 07 Apply fixes (fixed_deliverables) | Sections 8, 9, 10, 11 |
| 07A Consistency recheck (step-09-recheck) | Section 11A |
| 08 Feedback to tasker (+ review_meta.json) | Section 12 |
| 09 Cleanup                          | Section 13 |

If a phase is skipped because there is nothing to do (e.g., no fixes to apply), still flip it to `done` with the same Started/Completed timestamp and a note in the Current Phase line.

## Instructions

### 1. Locate task

First check if a review workspace already exists in `reviews/` (the API pre-creates it there):
```bash
find reviews/ -maxdepth 2 -type d -name "$ARGUMENTS" 2>/dev/null
```

- **If found in `reviews/`** -> use that directory, go to step 2 (load and review).

If not found in `reviews/`, check `tasks/`:
```bash
find tasks/ -maxdepth 2 -type d -name "$ARGUMENTS" 2>/dev/null
```

- **If found in `tasks/`** -> go to step 2 (load and review).
- **If NOT found in either** -> go to step 1a (create review scaffold).

---

### 1a. Create review scaffold (task not found)

The task does not exist locally. Create a review workspace so the user can paste the deliverables from the annotation platform.

1. Get current date in YYYY-MM-DD format.
2. Create the directory structure:
   ```bash
   mkdir -p reviews/{date}/$ARGUMENTS/deliverables
   mkdir -p reviews/{date}/$ARGUMENTS/work
   ```

3. Generate `reviews/{date}/$ARGUMENTS/inputs.md`:

```markdown
# Review Inputs

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

## Deliverables to Review

Paste the content of each deliverable file (copy-paste from the annotation platform):

### quality.md
Paste into: `reviews/{date}/$ARGUMENTS/deliverables/quality.md`

### severity.md
Paste into: `reviews/{date}/$ARGUMENTS/deliverables/severity.md`

### context_scope.md
Paste into: `reviews/{date}/$ARGUMENTS/deliverables/context_scope.md`

### advanced.md
Paste into: `reviews/{date}/$ARGUMENTS/deliverables/advanced.md`
```

4. Generate empty placeholder deliverables:

   - `reviews/{date}/$ARGUMENTS/deliverables/quality.md` (empty file)
   - `reviews/{date}/$ARGUMENTS/deliverables/severity.md` (empty file)
   - `reviews/{date}/$ARGUMENTS/deliverables/context_scope.md` (empty file)
   - `reviews/{date}/$ARGUMENTS/deliverables/advanced.md` (empty file)

5. Tell the user:

```
Review workspace created at reviews/{date}/$ARGUMENTS/

Please paste the following into the corresponding files:
  1. Task variables     -> inputs.md
  2. quality.md         -> deliverables/quality.md
  3. severity.md        -> deliverables/severity.md
  4. context_scope.md   -> deliverables/context_scope.md
  5. advanced.md        -> deliverables/advanced.md

Confirm when ready to continue.
```

6. **Wait for user confirmation.** Do NOT proceed until the user confirms.

7. After confirmation, read `inputs.md` and validate all fields are filled (same rules as step-01-parse-inputs). If any field is missing, tell the user and wait.

8. Once inputs are valid, build a `task_info.md` in the review directory by:
   - Populating Input Data from the inputs
   - Fetching PR info and diff using `gh` CLI (same as step-02-analyze-pr)
   - Saving diff to `reviews/{date}/$ARGUMENTS/work/pr_diff.txt`
   - Running comment analysis (same as step-03-analyze-comment) to populate Comment Analysis

9. Resolve `comment_commit` and clone the repository (same as step-02-analyze-pr sections 2 and 5):

   First, resolve the exact commit the comment was anchored to:
   ```bash
   gh api repos/{nwo}/pulls/comments/{comment_id} --jq '.original_commit_id'
   ```
   Save the result as `comment_commit` in `task_info.md`. If the call fails, fall back to `head_sha` and log a warning.

   Then clone at `comment_commit`:
   ```bash
   rm -rf "reviews/{date}/$ARGUMENTS/work/repo"
   # IMPORTANT: Use git -C to avoid changing the working directory.
   # Do NOT cd into the repo dir — see step-02 for rationale.
   git init "reviews/{date}/$ARGUMENTS/work/repo"
   git -C "reviews/{date}/$ARGUMENTS/work/repo" remote add origin "https://github.com/{nwo}.git"
   git -C "reviews/{date}/$ARGUMENTS/work/repo" fetch --depth=1 origin {comment_commit}
   git -C "reviews/{date}/$ARGUMENTS/work/repo" checkout FETCH_HEAD
   ```

   **Verify SHA after checkout:**
   ```bash
   ACTUAL_SHA=$(git -C "reviews/{date}/$ARGUMENTS/work/repo" rev-parse HEAD)
   if [ "$ACTUAL_SHA" != "{comment_commit}" ]; then
     echo "SHA MISMATCH: expected {comment_commit}, got $ACTUAL_SHA"
   fi
   ```

   Record result in task_info.md (same as step-02: `OK - verified at {comment_commit}` / `SHA MISMATCH` / `FAILED`).

10. Continue to step 2, using the `reviews/{date}/$ARGUMENTS/` path as the task directory.

---

### 2. Load deliverables

Determine the task directory (either `tasks/{date}/$ARGUMENTS/` or `reviews/{date}/$ARGUMENTS/`).

If coming from `tasks/`, read `progress.md`. If not all 8 steps are "done", warn: "Task is incomplete (step {N} pending). Review may be partial."

Read all files needed for review:
- `task_info.md` (inputs, comment body, PR context, comment analysis)
- `work/pr_diff.txt` (the actual diff)
- `deliverables/quality.md`
- `deliverables/severity.md`
- `deliverables/context_scope.md`
- `deliverables/advanced.md`

If any deliverable file is missing or empty, report which ones and STOP.

#### 2b. Ensure repo clone exists

The review needs local repo access for data consistency verification and context_scope re-evaluation. Check if `work/repo/` exists in the task directory.

Extract `comment_commit` from `task_info.md` (the "Comment Commit" field). If the field is missing or says "(populated after step 02)", fall back to `head_sha`. This ensures compatibility with tasks created before this field was added.

**If `work/repo/` does NOT exist** (cleaned up after task completion, or task was run before clone was added):

Extract `nwo` and `comment_commit` (or `head_sha` fallback) from `task_info.md`, then clone:

```bash
# IMPORTANT: Use git -C to avoid changing the working directory.
# Do NOT cd into the repo dir — see step-02 for rationale.
git init "{task_dir}/work/repo"
git -C "{task_dir}/work/repo" remote add origin "https://github.com/{nwo}.git"
git -C "{task_dir}/work/repo" fetch --depth=1 origin {comment_commit}
git -C "{task_dir}/work/repo" checkout FETCH_HEAD
```

**Verify SHA after checkout:**
```bash
ACTUAL_SHA=$(git -C "{task_dir}/work/repo" rev-parse HEAD)
if [ "$ACTUAL_SHA" != "{comment_commit}" ]; then
  echo "SHA MISMATCH: expected {comment_commit}, got $ACTUAL_SHA"
fi
cd -
```

Record the result. If SHA MISMATCH, warn the user and proceed with caution (cross-check local files against the diff before trusting them).

**If `work/repo/` already exists**, verify it is at the correct commit:
```bash
cd "{task_dir}/work/repo"
ACTUAL_SHA=$(git rev-parse HEAD)
cd -
```
If it does not match `comment_commit`, delete and re-clone.

#### 2a. Parse platform format

The `.md` files are raw copy-pastes from the annotation platform. Parse each one to extract the label and reasoning:

**quality.md** format:
```
Axis 1: Quality *
...prompt text...

{Label}              <-- one of: Helpful, Unhelpful, Wrong
Axis 1: Quality Justification *
{Reasoning text}
```

**severity.md** format:
```
Axis 2: Severity *
...prompt text...

{Label}              <-- one of: Nit, Moderate, Critical
Axis 2: Severity Justification *
{Reasoning text}
```

**context_scope.md** format:
```
{Label}              <-- one of: Diff, File, Repo, External
Axis 3: Context
...prompt text...

#	diff_line	file_path	why
1
{diff_line}
{file_path}
{why}
2
{diff_line}
{file_path}
{why}
...
```

**advanced.md** format:
```
Axis 4: Advanced *
...prompt text...

{Label}              <-- one of: Repo-specific conventions, Context outside changed files, Recent language/library updates, Better implementation approach, False
Axis 4: Advanced Justification
{Reasoning text}
```

Extract and record:
- `quality_label`, `quality_reasoning`
- `severity_label`, `severity_reasoning`
- `context_scope_label`, `context_entries[]` (each with diff_line, file_path, why)
- `advanced_label`, `advanced_reasoning`

Normalize **all** labels to lowercase for comparison, including advanced (e.g., "False" and "false" are the same; "Context outside changed files" and "context outside changed files" are the same). The annotation platform's combo box stores them in lowercase, so lowercase is the canonical form. Never propose a fix that only changes letter casing.

---

### 3. Data consistency verification

Before re-evaluating the axis labels, verify that the task data is internally consistent using the local repo clone from step 2b.

#### 3a. Verify repo clone integrity (C0)
- Extract `comment_commit` from `task_info.md` (the "Comment Commit" field). If missing, fall back to `head_sha`.
- Confirm `work/repo/` exists and is at the correct `comment_commit`:
  ```bash
  cd "{task_dir}/work/repo"
  ACTUAL_SHA=$(git rev-parse HEAD)
  cd -
  ```
- If SHA matches: record `C0: PASS (verified at {comment_commit})`
- If SHA does not match: record `C0: SHA MISMATCH (expected {comment_commit}, got {actual_sha})`. All subsequent file reads from the clone must be cross-checked against the diff.
- If clone does not exist and cannot be created: record `C0: FAILED (no local clone)`. Fall back to `gh api` for all file reads.

#### 3b. Verify the PR matches the comment (C1)
- Does the PR contain the file referenced in file_path?
- Does the PR diff include changes at or near diff_line?
- Is the comment (body) relevant to the changes in this PR?
- If the comment seems unrelated to the PR, flag it.

#### 3c. Verify the comment_commit contains the problem (C2)
- Read the target file from the local clone:
  ```bash
  cat "{task_dir}/work/repo/{file_path}"
  ```
  (Fallback if clone unavailable: `gh api "repos/{nwo}/contents/{file_path}?ref={comment_commit}" --jq '.content' | base64 -d`)
- At comment_commit, does the code exhibit the issue described in the comment?
- If YES: record "Problem confirmed at comment_commit."
- If NO: record this finding. This is critical; it may mean the comment is **wrong** or **unhelpful**. Do not assume automatically; analyze why.
- If already fixed at comment_commit: record "Problem not present at comment_commit; may have been fixed before the comment."
- **If the comment references code outside the target file** (imports, base classes, shared utilities), use the local clone to grep/read those files and verify the claims.

#### 3d. Verify the PR resolves what it claims (C3)
- Does the PR (title, description, changes) address what it claims?
- Are there gaps between what the PR says it does and what the diff shows?

#### 3e. Record and gate

| # | Check | Rule |
|---|---|---|
| C0 | Repo clone verified at comment_commit | SHA MISMATCH = warn, all file reads cross-checked against diff |
| C1 | PR contains file_path in its changed files | Critical mismatch if no |
| C2 | Problem exists at comment_commit | If not found, flag for quality label impact |
| C3 | PR resolves its stated claims | Informational; discrepancies noted |

**If C1 fails** (file not in PR): report to the user and STOP.
**If C2 fails** (problem not at comment_commit): continue but factor this into the quality re-evaluation. A comment claiming an issue that does not exist at comment_commit is likely wrong or unhelpful.

---

### 4. Content validation (re-evaluate each axis)

This is the core of the review. For each axis, independently re-derive what the label should be using the original evidence (comment body, diff, comment analysis). Then compare your independent assessment against the task's label.

**IMPORTANT:** Use the axis definitions from `docs/axis-1-quality.md`, `docs/axis-2-severity.md`, `docs/axis-3-context-scope.md`, and `docs/axis-4-advanced.md` as your evaluation criteria. Also consult `DOCUMENTATION.md` sections 8 (FAQ), 9 (Common Mistakes), and 10 (Tips) for edge cases and pitfalls. Read them if needed.

**IMPORTANT:** Factor in the data consistency findings from step 3. If the problem was not found at comment_commit, this must influence your quality assessment.

---

#### 4a. Re-evaluate Quality

Re-read the comment body and the Comment Analysis from task_info.md. Apply the **full 6-node decision tree** from `.claude/skills/step-04-label-quality/SKILL.md` Section 2. This tree is the single source of truth for quality labeling and must be applied identically in `/run` and `/review`. Do not use a shortened version.

```
1. Is the comment factually incorrect?
   Does it misunderstand the code, suggest something that would
   introduce a bug, or make a false claim about the language/framework?
   -> Yes: WRONG

2. Does ANY part of the comment body contain a non-actionable
   suggestion? Look for hedges like "or use an existing X if the
   repo has one", "if it exists", "if available", "consider",
   "you may want to", "perhaps", "maybe". A truly actionable
   comment tells the attempter WHAT to do, it does not punt the
   discovery work back to the reader.
   -> Yes (any portion is non-actionable): UNHELPFUL
   -> No: continue to 3

3. Is the comment too vague or cryptic to act on without
   investigation? A single word, a bare keyword, or a comment
   that does not specify WHAT to change, WHERE, or HOW is not
   actionable. The developer should not have to guess the
   reviewer's intent or search the codebase to decode the
   suggestion. Examples: "enum", "refactor", "types", "naming".
   -> Yes (vague/cryptic): UNHELPFUL
   -> No: continue to 4

4. Does the comment identify a genuine issue, catch a real bug,
   or suggest a significant improvement? Is it technically correct,
   actionable, and adding value a competent engineer would want
   resolved?
   -> No (pedantic, obvious, stylistic without substance, no real
      issue, restates what the code obviously does): UNHELPFUL
   -> Yes: continue to 5

5. If the comment offers multiple fix options, do those options
   contradict each other, or is one significantly worse than the
   other? The number of options itself does not matter. What
   matters is whether the set of options guides the dev or
   confuses them and risks leading them to a bad path.
   -> Contradictory or uneven options: UNHELPFUL
   -> Single option, or options that are all reasonable: continue to 6

6. Does the proposed fix introduce regressions, incompatibilities,
   or worsen overall code quality? A comment can point at a real
   problem but propose a solution that makes things worse.
   -> Yes: UNHELPFUL
   -> No: HELPFUL
```

**Non-actionable suggestion rule (taint-the-whole-comment):** if even one clause inside the body is non-actionable, the whole comment is `unhelpful`, regardless of how good the rest is. Example: `"replace this with a proper segmented control (or use an existing accessible segmented-control/tabs component if the repo has one)"` is `unhelpful` because the parenthetical punts the repo lookup back to the attempter.

**Common-mistake rules (mirror of step-04-label-quality Section 4, apply them all):**

- Do not label `wrong` just because you disagree. `wrong` means factually false.
- Do not label `helpful` just because it sounds reasonable or is factually correct. `helpful` requires a genuine issue, a technically correct claim, actionability, and a fix with substance.
- The number of proposed options does not decide the label. One option and several options can both be `helpful`. What matters is whether the set guides the dev toward a good resolution.
- Contradictory or uneven options taint the comment as `unhelpful`.
- A good catch with a bad fix is `unhelpful`.
- Do not couple Quality and Severity. A `wrong` comment about a critical issue is still `wrong`. A `helpful` comment about a naming nit is still `helpful`.
- A comment that restates what the code obviously does is `unhelpful`, even if technically correct.
- Vague or cryptic comments are `unhelpful` even if the underlying idea is correct. Correct observation plus zero specificity equals `unhelpful`.
- Non-actionable hedges taint the whole comment.
- Do not label `unhelpful` just because the issue is small. A correct, actionable comment with substance is `helpful` even if minor.
- **Auto-generated files.** If `file_path` points to a generated artifact and the generator or template that produces it is also in the PR's changed files, a comment filed on the generated output targets the symptom, not the root cause. Label as `unhelpful` unless the comment explicitly and primarily addresses the generator. Detect by clues such as `docs/`, `build/`, `dist/`, `output/` paths, the PR also changing a script/template that produces the file, or a "generated by" header.

**Data consistency input (from step 3 of this skill):** factor the C2 finding into the quality decision. If the problem was not found at comment_commit, that pushes toward `wrong` or `unhelpful`.

Record your independent label. Compare against the task's label.

| # | Check | Rule |
|---|---|---|
| V1 | Your independent quality label matches the task's label | If mismatch, explain your reasoning and why you disagree |

---

#### 4b. Re-evaluate Severity

Isolate the underlying issue (regardless of comment correctness). Assess real-world impact:

- Can be safely ignored or deferred? -> `nit`
- Affects behavior but unlikely to cause serious harm? -> `moderate`
- Senior engineer would insist on fixing before merge? -> `critical`

Record your independent label. Compare against the task's label.

| # | Check | Rule |
|---|---|---|
| V2 | Your independent severity label matches the task's label | If mismatch, explain your reasoning and why you disagree |

---

#### 4c. Re-evaluate Context Scope

Ask: "What would the reviewer need to read to make this comment with confidence?"

- Only changed lines (possibly across files)? -> `diff`
- Beyond diff hunks but within PR-touched files? -> `file`
- Files NOT changed by the PR? -> `repo`
- Knowledge outside the repository? -> `external`

**Use the local clone to verify scope claims.** If the context entries reference specific lines or files, read them from `work/repo/` to confirm the evidence exists and is relevant:
```bash
# Verify a context entry's line reference
sed -n '{start},{end}p' "{task_dir}/work/repo/{file_path}"

# Check if the reviewer needed files outside the PR
# (grep for patterns mentioned in the comment across the repo)
grep -rn "{pattern}" "{task_dir}/work/repo/" --include="*.{ext}"
```

**Cross-checks:**
- Check step-03's "Beyond Diff" field against the context_scope label. If "Beyond Diff: No" but context_scope is not `diff`, flag the inconsistency.
- Distinguish between what the analyst consulted (verification) and what the reviewer needed (observation). Context entries based on analyst verification alone should not inflate the scope.

Also validate the context entries: are they the right evidence? Is anything missing or extraneous?

Record your independent label. Compare against the task's label.

| # | Check | Rule |
|---|---|---|
| V3 | Your independent context_scope label matches the task's label | If mismatch, explain your reasoning |
| V4 | Context entries are correct and complete | No missing evidence, no extraneous entries |
| V3b | step-03 "Beyond Diff" is consistent with context_scope | "Beyond Diff: No" should align with `diff`; "Yes" should align with `file`/`repo`/`external` |

---

#### 4d. Re-evaluate Advanced

Advanced is derived from Context Scope using a deterministic mapping:

| Context Scope | Advanced |
|---|---|
| **diff** | False |
| **file** | False |
| **repo** | True (select the specific beyond-diff category) |
| **external** | True (select the specific beyond-diff category) |

If the context_scope from step 4c is `repo` or `external`, select the category that best explains why:

| Category (platform value) | What to look for |
|---|---|
| **Repo-specific conventions** | Comment references patterns, conventions, or architectural decisions specific to this repo |
| **Context outside changed files** | Comment requires knowledge from files not touched by the PR |
| **Recent language/library updates** | Comment requires awareness of recent or non-obvious language/framework behavior |
| **Better implementation approach** | Comment suggests a fundamentally better design, algorithm, or API usage (not just style) |

Record your independent label derived from the mapping. Compare against the task's label.

| # | Check | Rule |
|---|---|---|
| V5 | Your independent advanced label matches the task's label | If mismatch, explain your reasoning. The mapping from context_scope must be respected. |

---

### 5. Reasoning validation

For each axis, evaluate the reasoning extracted from the deliverable .md file:

| # | Check | Rule |
|---|---|---|
| R1 | **Accurate:** Does the reasoning make claims that are true? Verify each factual claim against the code/diff | No false statements |
| R2 | **Sufficient:** Does the reasoning explain WHY this label was chosen, not just restate the label? | Must contain evidence, not just conclusion |
| R3 | **Self-contained:** Could someone reading only the reasoning understand the justification without needing task_info.md or other files? | No references to "see above", "as noted in analysis", etc. |
| R4 | **Concise:** Is the reasoning focused (2-3 sentences for quality/severity, 1-2 for advanced) without filler? | No unnecessary padding |
| R5 | **Aligned:** Does the reasoning actually support the label chosen? (e.g., reasoning describes a critical bug but label is "nit") | Reasoning must logically lead to the label |

---

### 6. Format and consistency checks

Run these as secondary validation:

#### 5a. Label values

| # | Check | Rule |
|---|---|---|
| F1 | quality label is one of: `helpful`, `unhelpful`, `wrong` | Exact match (case-insensitive) |
| F2 | severity label is one of: `nit`, `moderate`, `critical` | Exact match (case-insensitive) |
| F3 | context_scope label is one of: `diff`, `file`, `repo`, `external` | Exact match (case-insensitive) |
| F4 | advanced label is one of: `Repo-specific conventions`, `Context outside changed files`, `Recent language/library updates`, `Better implementation approach`, `False` | **Case-insensitive** match. The platform's combo box uses lowercase (`false`, `context outside changed files`, etc.) and that is the canonical, valid form. NEVER flag a label as wrong just because of casing. Casing is not a defect. |

#### 5b. Context entries

| # | Check | Rule |
|---|---|---|
| F5 | If context_scope is not `external`, at least 1 context entry exists | Array length |
| F6 | Each context entry has diff_line, file_path, and why | Field presence |

#### 5c. diff_line validation

| # | Check | Rule |
|---|---|---|
| D1 | Context entries for files NOT in the PR's changed files have null/empty diff_line | Cross-ref with Changed Files List |
| D2 | Context entries for files IN the PR's changed files have non-empty diff_line | Unless exact line is hard to locate |

#### 5d. Wording rules (CLAUDE.md compliance)

Scan all reasoning sections and `why` fields for prohibited characters:

| # | Check | Prohibited |
|---|---|---|
| W1 | No em-dashes (`\u2014`) | Use commas, semicolons, or split sentences |
| W2 | No en-dashes (`\u2013`) | Use hyphens for ranges |
| W3 | No ellipsis character (`\u2026`) | Use three dots (`...`) |
| W4 | No smart/curly quotes (`\u201c \u201d \u2018 \u2019`) | Use straight quotes |

---

### 7. Report results

Display in this format:

```
== Review: {id} ==

DATA CONSISTENCY
  C0  Repo clone at comment_commit  PASS / SHA MISMATCH / FAILED
  C1  PR contains file_path ...... PASS / FAIL
  C2  Problem at comment_commit .. Confirmed / Not found / Already fixed
  C3  PR resolves its claims ..... Yes / Partially / No

CONTENT VALIDATION (axis re-evaluation)
  V1  quality .................... AGREE / DISAGREE
  V2  severity ................... AGREE / DISAGREE
  V3  context_scope .............. AGREE / DISAGREE
  V4  context entries ............ PASS / FAIL
  V5  advanced ................... AGREE / DISAGREE

  [For each DISAGREE, show:]
  V{N} DISAGREE: Task says "{task_label}", reviewer says "{your_label}"
       Reason: {why you disagree, 1-2 sentences}

REASONING VALIDATION
  R1  Accurate ................... PASS / FAIL (per axis)
  R2  Sufficient ................. PASS / FAIL (per axis)
  R3  Self-contained ............. PASS / FAIL (per axis)
  R4  Concise .................... PASS / FAIL (per axis)
  R5  Aligned .................... PASS / FAIL (per axis)

  [For each FAIL, show which axis and why]

FORMAT & CONSISTENCY
  F1-F4   label values ........... PASS / {N} issues
  F5-F6   context entries ........ PASS / {N} issues
  D1-D2   diff_line .............. PASS / {N} issues
  W1-W4   wording ................ PASS / {N} issues

---
SUMMARY:
  Content:   {N}/5 axes agree, {N} disagree
  Reasoning: {N}/5 axes pass all checks
  Format:    {N} passed, {N} failed
  Overall:   CLEAN / NEEDS REVISION
```

---

### 8. Applying fixes

When the user approves a fix (label change, reasoning rewrite, or format correction), write the corrected file into `fixed_deliverables/` inside the task directory, **not** into `deliverables/`.

```bash
mkdir -p {task_dir}/fixed_deliverables
```

- Copy the original file from `deliverables/` as a starting point.
- Apply the approved change.
- Write the result to `fixed_deliverables/{axis}.md`.
- For `context_scope.md`, also generate `fixed_deliverables/context.json` with the corrected context entries in platform table format (see below).

Only the axes that were actually corrected go into `fixed_deliverables/`. Axes that passed review unchanged stay only in `deliverables/`.

This keeps the original deliverables intact for comparison and gives the user a clean set of corrected files to paste back into the platform.

#### Platform-ready format for fixed_deliverables

Fixed deliverables must be in the **platform copy-paste format**, not the internal markdown format. This is critical because the user pastes them directly into the annotation platform.

**context_scope.md** platform format:
```
{Label}
Axis 3: Context
If context_scope is "external", the context array may be empty ([]) since the knowledge comes from outside the repository (e.g., language docs, framework behavior, RFCs).

#	diff_line	file_path	why
1
{diff_line_1}
{file_path_1}
{why_1}
2
{diff_line_2}
{file_path_2}
{why_2}
```

**context.json** platform format (for the context table):
```json
{
  "rows": [
    {
      "_dshks": "{diff_line_or_empty}",
      "ahMYbl": "{file_path}",
      "dA0ihr": "{why}"
    }
  ]
}
```

**quality.md** platform format:
```
{Label}
Axis 1: Quality Justification *
{Reasoning text}
```

**severity.md** platform format:
```
{Label}
Axis 2: Severity Justification *
{Reasoning text}
```

**advanced.md** platform format:
```
{Label}
Axis 4: Advanced Justification
{Reasoning text}
```

---

### 9. If DISAGREE on any axis

For each disagreement:
1. Show both labels side by side with reasoning
2. Reference the specific evidence (code lines, diff sections) that supports your assessment
3. Ask: "Do you want to update this label? (yes/no/discuss)"
   - **yes** -> Write corrected file to `fixed_deliverables/`, then re-run consistency checks
   - **no** -> Keep the original label, note it as "reviewed, kept as-is"
   - **discuss** -> Present the arguments for and against each label and let the user decide

### 10. If reasoning FAIL on any axis

For each failure:
1. Quote the problematic reasoning
2. Explain what is wrong (inaccurate claim, missing evidence, not self-contained, etc.)
3. Propose a corrected reasoning
4. Ask: "Apply this fix? (yes/no)"
5. If yes, write corrected file to `fixed_deliverables/`

### 11. If format failures exist

For each format FAIL:
1. Show what was expected vs found
2. Ask: "Fix these automatically? (yes/no)"
3. If yes, write corrected files to `fixed_deliverables/` and re-run checks

---

### 11A. Consistency recheck (step-09-recheck)

After all fixes (if any) have been written to `fixed_deliverables/`, invoke the `step-09-recheck` sub-skill in review mode over the task id. This runs the full verification checklist (file integrity, label values, file-path and line-number validation against the repo clone, comment consistency, wording rules, and cross-axis consistency) over `fixed_deliverables/` with `deliverables/` as the baseline.

- Auto mode: run `step-09-recheck {id} review auto`.
- Interactive mode: run `step-09-recheck {id} review`.

If the recheck emits `RECHECK_FAILED`:
- Read `recheck_report.md` from the task directory.
- For wording-only failures, step-09-recheck will have already rewritten the offending files in place under `fixed_deliverables/`. Nothing else to do.
- For label, path, or cross-axis failures that step-09-recheck could not auto-fix, apply corrections to the corresponding file in `fixed_deliverables/` and rerun `step-09-recheck {id} review auto` once. If it still fails, continue to Section 12 but mention the remaining issues in the feedback paragraph and point the user to `recheck_report.md`.

If the recheck emits `RECHECK_PASSED`, continue straight to Section 12.

---

### 12. Generate feedback_to_cb.md and review_meta.json

After all fixes are applied (or if review is CLEAN), generate **two** files in the task directory:
- `feedback_to_cb.md`
- `review_meta.json`

Both must contain the SAME prose in the `feedback_text` / file body. Treat them as a single artifact in two formats.

#### Tone and content rules (mandatory)

- **Past tense, "what was adjusted":** describe what you fixed, not what "needs adjustment". E.g. write "I changed the Quality label to `helpful` because ...", NOT "the Quality label needs to be changed to `helpful`". The attempter receives this AFTER the fix has been applied; the fix is already done.
- **Plain prose paragraphs only.** No `#`/`##` headings, no bullet lists, no `>` blockquotes, no tables. Just natural sentences grouped into one or two short paragraphs. Markdown is only allowed for inline code spans with backticks (e.g. `helpful`, `nth(1)`) when naming a label, function, or file.
- **Concise and concrete:** one or two short paragraphs total. Name the axis, name what changed, name the concrete reason in one sentence each. No preamble ("Hi, hope you're doing well..."), no recap of the rubric, no closing pleasantries beyond a short friendly line.
- **Friendly, colleague-to-colleague:** warm but brief. A short positive opener or closer is fine ("Nice work overall.", "Solid pass on the rest."). Never condescending, never mechanical.
- **Clean case:** if nothing was adjusted, write a single sentence such as "All labels and reasoning looked good, nothing to adjust here. Nice work."
- **No copy of the diff or long code blocks.** Reference functions or files by name, not by quoting them.

#### Format

`feedback_to_cb.md` is just the plain prose, no `# Feedback` heading, no separator lines. Example for a one-fix review:

```
I bumped the Quality label from `wrong` to `helpful`. The reasoning treated `_remove_all_group_entries` as if it lived in old code, but `ha_groups_controller.py` is a brand-new file in this PR (495 additions, 0 deletions), so the function the comment flags really is the incoming behavior. I also tightened the Advanced reasoning to say the issue is in the added lines, not the removed ones. Everything else looked good. Nice work overall.
```

Example for a clean review:

```
All labels and reasoning looked good, nothing to adjust here. Nice work.
```

`review_meta.json` mirrors the same prose:

```json
{
  "quality_score": <int 1-5>,
  "feedback_text": "<the exact same paragraph(s) as feedback_to_cb.md>"
}
```

Keep both files in sync. The extension reads `feedback_text` and pastes it directly into the platform's Feedback textarea, so any markdown noise becomes visible to the attempter and is unacceptable.

---

### 13. Cleanup

After the review is complete (report shown, fixes applied or declined, feedback generated), clean up the cloned repository:

```bash
REPO_DIR="{task_dir}/work/repo"
if [ -d "$REPO_DIR" ]; then
  rm -rf "$REPO_DIR"
  echo "Cleaned up repo clone at $REPO_DIR"
fi
```

This cleanup runs regardless of whether the review found issues or was clean.
