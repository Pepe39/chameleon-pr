# /review - Validate deliverables for a task

Reviews a task's deliverables: re-evaluates each axis label against the evidence, validates reasoning quality, and checks format consistency.

Deliverables are the 4 axis `.md` files copied from the annotation platform.

## Arguments
- `$ARGUMENTS` (positional): Task ID. E.g.: `/review 2937204136`

## Instructions

### 1. Locate task

First check if the task exists in `tasks/`:
```bash
find tasks/ -maxdepth 2 -type d -name "$ARGUMENTS" 2>/dev/null
```

- **If found** -> go to step 2 (load and review).
- **If NOT found** -> go to step 1a (create review scaffold).

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

9. Clone the repository at head_sha (same as step-02-analyze-pr section 5):

   ```bash
   rm -rf "reviews/{date}/$ARGUMENTS/work/repo"
   git init "reviews/{date}/$ARGUMENTS/work/repo"
   cd "reviews/{date}/$ARGUMENTS/work/repo"
   git remote add origin "https://github.com/{nwo}.git"
   git fetch --depth=1 origin {head_sha}
   git checkout FETCH_HEAD
   ```

   **Verify SHA after checkout:**
   ```bash
   ACTUAL_SHA=$(git rev-parse HEAD)
   if [ "$ACTUAL_SHA" != "{head_sha}" ]; then
     echo "SHA MISMATCH: expected {head_sha}, got $ACTUAL_SHA"
   fi
   cd -
   ```

   Record result in task_info.md (same as step-02: `OK - verified at {head_sha}` / `SHA MISMATCH` / `FAILED`).

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

**If `work/repo/` does NOT exist** (cleaned up after task completion, or task was run before clone was added):

Extract `nwo` and `head_sha` from `task_info.md`, then clone:

```bash
git init "{task_dir}/work/repo"
cd "{task_dir}/work/repo"
git remote add origin "https://github.com/{nwo}.git"
git fetch --depth=1 origin {head_sha}
git checkout FETCH_HEAD
```

**Verify SHA after checkout:**
```bash
ACTUAL_SHA=$(git rev-parse HEAD)
if [ "$ACTUAL_SHA" != "{head_sha}" ]; then
  echo "SHA MISMATCH: expected {head_sha}, got $ACTUAL_SHA"
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
If it does not match `head_sha`, delete and re-clone.

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

{Label}              <-- one of: True, False
Axis 4: Advanced Justification
{Reasoning text}
```

Extract and record:
- `quality_label`, `quality_reasoning`
- `severity_label`, `severity_reasoning`
- `context_scope_label`, `context_entries[]` (each with diff_line, file_path, why)
- `advanced_label`, `advanced_reasoning`

Normalize labels to lowercase for comparison (e.g., "Helpful" -> "helpful", "Nit" -> "nit", "True" -> "true").

---

### 3. Data consistency verification

Before re-evaluating the axis labels, verify that the task data is internally consistent using the local repo clone from step 2b.

#### 3a. Verify repo clone integrity (C0)
- Confirm `work/repo/` exists and is at the correct `head_sha`:
  ```bash
  cd "{task_dir}/work/repo"
  ACTUAL_SHA=$(git rev-parse HEAD)
  cd -
  ```
- If SHA matches: record `C0: PASS (verified at {head_sha})`
- If SHA does not match: record `C0: SHA MISMATCH (expected {head_sha}, got {actual_sha})`. All subsequent file reads from the clone must be cross-checked against the diff.
- If clone does not exist and cannot be created: record `C0: FAILED (no local clone)`. Fall back to `gh api` for all file reads.

#### 3b. Verify the PR matches the comment (C1)
- Does the PR contain the file referenced in file_path?
- Does the PR diff include changes at or near diff_line?
- Is the comment (body) relevant to the changes in this PR?
- If the comment seems unrelated to the PR, flag it.

#### 3c. Verify the head_sha contains the problem (C2)
- Read the target file from the local clone:
  ```bash
  cat "{task_dir}/work/repo/{file_path}"
  ```
  (Fallback if clone unavailable: `gh api "repos/{nwo}/contents/{file_path}?ref={head_sha}" --jq '.content' | base64 -d`)
- At head_sha, does the code exhibit the issue described in the comment?
- If YES: record "Problem confirmed at head_sha."
- If NO: record this finding. This is critical; it may mean the comment is **wrong** or **unhelpful**. Do not assume automatically; analyze why.
- If already fixed at head_sha: record "Problem not present at head_sha; may have been fixed before the comment."
- **If the comment references code outside the target file** (imports, base classes, shared utilities), use the local clone to grep/read those files and verify the claims.

#### 3d. Verify the PR resolves what it claims (C3)
- Does the PR (title, description, changes) address what it claims?
- Are there gaps between what the PR says it does and what the diff shows?

#### 3e. Record and gate

| # | Check | Rule |
|---|---|---|
| C0 | Repo clone verified at head_sha | SHA MISMATCH = warn, all file reads cross-checked against diff |
| C1 | PR contains file_path in its changed files | Critical mismatch if no |
| C2 | Problem exists at head_sha | If not found, flag for quality label impact |
| C3 | PR resolves its stated claims | Informational; discrepancies noted |

**If C1 fails** (file not in PR): report to the user and STOP.
**If C2 fails** (problem not at head_sha): continue but factor this into the quality re-evaluation. A comment claiming an issue that does not exist at head_sha is likely wrong or unhelpful.

---

### 4. Content validation (re-evaluate each axis)

This is the core of the review. For each axis, independently re-derive what the label should be using the original evidence (comment body, diff, comment analysis). Then compare your independent assessment against the task's label.

**IMPORTANT:** Use the axis definitions from `docs/axis-1-quality.md`, `docs/axis-2-severity.md`, `docs/axis-3-context-scope.md`, and `docs/axis-4-advanced.md` as your evaluation criteria. Also consult `DOCUMENTATION.md` sections 8 (FAQ), 9 (Common Mistakes), and 10 (Tips) for edge cases and pitfalls. Read them if needed.

**IMPORTANT:** Factor in the data consistency findings from step 3. If the problem was not found at head_sha, this must influence your quality assessment.

---

#### 4a. Re-evaluate Quality

Re-read the comment body and the Comment Analysis from task_info.md. Apply the decision tree:

1. Is the comment factually incorrect? (misunderstands code, would introduce a bug, false claim) -> `wrong`
2. Does it identify a genuine issue, catch a real bug, or suggest a meaningful improvement? Is it actionable and specific? -> `helpful`
3. Technically correct but no practical value? (pedantic, obvious, not actionable) -> `unhelpful`

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

Ask: "Could a reviewer make this comment by looking only at the changed lines in the diff?"

Label `true` if the comment meets one or more:
- Repo-specific conventions
- Context outside changed files
- Recent language/library updates
- Better implementation approach (not just style)

Label `false` if the issue is visible directly in the diff.

Record your independent label. Compare against the task's label.

| # | Check | Rule |
|---|---|---|
| V5 | Your independent advanced label matches the task's label | If mismatch, explain your reasoning |

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
| F4 | advanced label is one of: `true`, `false` | Exact match (case-insensitive) |

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
  C0  Repo clone at head_sha ..... PASS / SHA MISMATCH / FAILED
  C1  PR contains file_path ...... PASS / FAIL
  C2  Problem at head_sha ........ Confirmed / Not found / Already fixed
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

### 12. Generate feedback_to_cb.md

After all fixes are applied (or if review is CLEAN), generate `{task_dir}/feedback_to_cb.md`.

This file is a brief, friendly note to the person who completed the task, written in English. It must be:

- **Concise:** Only list what was wrong and what the correct answer is. No filler, no preamble.
- **Evidence-backed:** Each error must cite the source that proves it (quote from the review comment, diff line, file content, tsconfig, etc.). Use `>` blockquotes for citations.
- **Natural language:** Write as if you're talking to a colleague, not generating a report.
- **Positive when clean:** If no errors were found, say so in one sentence.

Format:

```markdown
# Feedback

{If CLEAN: "All labels and reasoning passed review. Nice work."}

{If NEEDS REVISION, one section per error:}

## {Axis}: {what was wrong}

{1-2 sentences explaining the error and what is correct.}

Evidence:
> {quote from comment, diff, file, or config that proves the point}
```

Keep the entire file as short as possible. One error = one short section. Do not repeat the full review report here.

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
