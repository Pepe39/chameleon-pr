# Code Review Labeling — Step-by-Step Workflow Guide

This guide walks you through the complete workflow for labeling a single code review comment, from opening the task to submitting your final labels.

---

## Prerequisites

Before starting, make sure you have:
- Access to the annotation platform with assigned tasks
- A GitHub account (to browse PRs and repos)
- The labeling guidelines open for reference

---

## Step-by-Step Workflow

### Step 0: Receive and Open the Task

1. Open your assigned task in the annotation platform.
2. You will see a JSON object with fields like:
   ```json
   {
     "pull_request_url": "https://github.com/org/repo/pull/123",
     "nwo": "org/repo",
     "head_sha": "abc123...",
     "file_path": "src/api/handlers/user.py",
     "diff_line": 45,
     "body": "This null check should happen before the dereference...",
     "discussion_url": "https://github.com/org/repo/pull/123#discussion_r...",
     "repo_url": "https://github.com/org/repo/tree/abc123..."
   }
   ```
3. Read the `body` field — this is the review comment you need to label.

---

### Step 1: Open the PR

1. Click on `pull_request_url` to open the Pull Request on GitHub.
2. Read the **PR title** and **description** to understand:
   - What repository/project this is
   - What the PR is changing and why
3. This gives you the high-level context for evaluating the review comment.

---

### Step 2: Go to the Discussion

1. Click on `discussion_url` — this takes you directly to the review comment in context.
2. You will see the comment alongside its surrounding diff hunk.
3. **Checkpoint:** Verify that the comment shown on GitHub matches the `body` field in your input data. If it doesn't match, flag the task.

---

### Step 3: Review the Diff and Changed Files

1. From the discussion view, click on the **file name** at the top of the diff hunk.
2. This takes you to the PR's **"Files Changed"** tab.
3. Use the `diff_line` value to locate the specific line where the comment is anchored.
4. Read through **all diff hunks** across all changed files to build a comprehensive understanding of the PR.
5. Pay attention to:
   - What code was added/removed/modified
   - How the changes relate to each other across files
   - The overall intent of the PR

---

### Step 4: Browse the Repository (Only If Needed)

> This step is only needed when the comment references or requires knowledge beyond the changed files.

1. Click on `repo_url` to browse the repository at the exact commit (`head_sha`).
2. Explore files that the comment references or implies:
   - Imports and shared utilities
   - Base classes or interfaces
   - Configuration files
   - Test files
   - API contracts in other modules
3. This ensures you're looking at the correct snapshot of the code.

---

### Step 5: Re-read and Deeply Understand the Comment

1. Go back to the `body` field in your input data.
2. Now that you have full context, re-read the comment carefully.
3. Ask yourself:
   - What specific issue is this comment pointing out?
   - Is the claim in the comment factually correct?
   - What code context would a reviewer need to make this comment?
4. **If still unclear**, repeat Steps 2-4 as needed. Navigate between the diff, the discussion, and the repo until you fully understand.

> **Tip:** Don't rush to label. Re-reading the comment after understanding the full diff often changes your initial impression.

---

### Step 6: Label Axis 1 — Quality

Decide: Is this comment **helpful**, **unhelpful**, or **wrong**?

Use this decision tree:

```
1. Is the comment factually incorrect or would following it introduce a bug?
   → Yes: WRONG

2. Does the comment identify a genuine issue, catch a real bug,
   or suggest a meaningful improvement?
   → Yes: HELPFUL

3. Otherwise (pedantic, obvious, stylistic without substance):
   → UNHELPFUL
```

**Key reminders:**
- Wrong = factually false, not "I disagree"
- Unhelpful = technically true but no practical value
- Verify claims against the actual code before labeling as Wrong

---

### Step 7: Label Axis 2 — Severity

Decide: How severe is the **issue itself** (not the comment)?

| Label | Question to Ask | Examples |
|---|---|---|
| **nit** | Can this safely be ignored or deferred? | Style, naming, cosmetic, docs |
| **moderate** | Should this be improved but won't cause serious harm? | Missing edge cases on uncommon paths, suboptimal logic |
| **critical** | Would a senior engineer insist this be fixed before merge? | Security vulnerabilities, data corruption, build-breaking errors |

**Key reminders:**
- Rate the **issue**, not the **tone** of the comment
- If multiple issues mentioned, rate by the **most severe**
- Same code pattern can be different severities depending on context

---

### Step 8: Label Axis 3 — Context Scope

Decide: What level of context did the reviewer **need** to make this comment?

| Level | What Was Needed |
|---|---|
| **diff** | Only the changed lines in the PR (can span multiple files) |
| **file** | Code beyond the diff but within PR-touched files (surrounding functions, imports, class definitions) |
| **repo** | Files NOT changed by the PR (shared utilities, base classes, config, tests) |
| **external** | Knowledge outside the repo entirely (API docs, RFCs, business requirements) |

**Pick the broadest level needed.** If both diff and file context were needed → `file`.

Then fill in the `context` array:
```json
{
  "context_scope": "file",
  "context": [
    {
      "diff_line": "168",
      "file_path": "src/monitors/incident.py",
      "why": "The bug line where untransformed config is returned"
    },
    {
      "diff_line": "161-163",
      "file_path": "src/monitors/incident.py",
      "why": "Where config is created and transformed — needed to understand the bug"
    }
  ]
}
```

---

### Step 9: Label Axis 4 — Advanced

Decide: Does this comment go **beyond what is obvious** from the changed lines?

**Label `true` if ANY of these apply:**
- References repo-specific conventions or architectural decisions
- Requires knowledge from files NOT touched by the PR
- Requires awareness of recent/non-obvious language or library behavior
- Suggests a fundamentally better implementation approach

**Label `false` if:**
- The issue is visible directly in the diff (typos, syntax errors, obvious logic bugs)
- A reviewer could make this comment by only reading the changed lines
- Even if the comment is insightful, if it's derivable from the diff alone → `false`

---

### Step 10: Record and Submit

Compile your labels into the output format:

```json
{
  "quality": "helpful",
  "severity": "critical",
  "context_scope": "file",
  "context": [
    {
      "diff_line": "168",
      "file_path": "src/monitors/incident.py",
      "why": "Bug line — returns untransformed config"
    },
    {
      "diff_line": "161-163",
      "file_path": "src/monitors/incident.py",
      "why": "Config is created and transformed here"
    }
  ],
  "advanced": false
}
```

**Final checklist before submitting:**
- [ ] Verified the comment matches the `body` field
- [ ] Quality is based on factual correctness and usefulness
- [ ] Severity rates the issue, not the comment's tone
- [ ] Context scope reflects the broadest level needed
- [ ] Context array lists all evidence the reviewer used
- [ ] Advanced is based on knowledge requirements, not difficulty
- [ ] All four axes are evaluated independently

---

## Quick Reference Card

| Axis | Values | Key Rule |
|---|---|---|
| **Quality** | helpful / unhelpful / wrong | Wrong = factually false, not "I disagree" |
| **Severity** | nit / moderate / critical | Rate the issue, not the comment |
| **Context Scope** | diff / file / repo / external | Pick the broadest level needed |
| **Advanced** | true / false | Could the comment be made from the diff alone? |

### Independence Rule

All four axes are **independent**. Any combination is valid:
- Helpful + Nit + Diff + false (good comment about a minor style issue)
- Wrong + Critical + File + false (incorrect claim about a severe issue)
- Helpful + Critical + Repo + true (catches a real bug using deep repo knowledge)
