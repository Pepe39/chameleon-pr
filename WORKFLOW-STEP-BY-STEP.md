# Code Review Labeling. Step-by-Step Workflow Guide

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

### Step 6: Label Axis 1. Quality

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

### Step 7: Label Axis 2. Addressed

> Always runs. The platform exposes a 4-value enum on every task. The fourth value `empty` is the active selection ONLY for OPEN PRs. Closed PRs, whether merged or closed without merge, are evaluated against the decision tree.

Decide. What is the state of the comment on the PR?

| Label | When to pick it | Examples |
|---|---|---|
| **empty** | The PR is OPEN. The final state needed to choose between the other three values does not exist yet | PR `state == OPEN` only. A PR closed without merging is NOT empty, it evaluates like merged |
| **addressed** | Merged PR. The merged code changed in a way that resolves the underlying concern | Reviewer's exact suggestion was applied, a different fix that solves the same problem, or an author reply promising to fix later or in another PR |
| **ignored** | Merged PR. The merged code is unchanged on this concern and no discussion dismissed the comment | The comment was posted and nobody touched the code or replied to it |
| **false_positive** | Merged PR. The PR author or another reviewer explicitly rebutted the comment | Reply explains the comment is based on a misunderstanding, points at code that already handles the case, or calls the concern non-applicable |

**Key reminders:**
- `empty` is not the same as not selecting. It is an active selection.
- Silence on a closed PR (merged or not) is not a false positive. Without an explicit rebuttal, the default is `ignored`.
- The fix does not have to match the reviewer's suggestion. Any change that resolves the underlying concern counts as `addressed`.
- Compare against the **merged** state, not HEAD of the branch at the time of the comment. Follow the thread all the way to what landed.

---

### Step 8: Label Axis 3. Severity

Decide. How severe is the **issue itself**, not the comment?

| Label | Question to Ask | Examples |
|---|---|---|
| **nit** | Can this safely be ignored or deferred? | Style, naming, cosmetic, docs |
| **moderate** | Should this be improved but will not cause serious harm? | Missing edge cases on uncommon paths, suboptimal logic |
| **critical** | Would a senior engineer insist this be fixed before merge? | Security vulnerabilities, data corruption, build-breaking errors |

**Key reminders:**
- Rate the **issue**, not the **tone** of the comment.
- If multiple issues mentioned, rate by the **most severe**.
- Same code pattern can be different severities depending on context.

---

### Step 9: Label Axis 4. Context Scope

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

### Step 10: Label Axis 5. Advanced

Decide. Which kind of beyond-diff knowledge did the reviewer rely on?

**Advanced is a 5-value string enum, not `true/false`.** Pick exactly one:

| Value | When to pick it |
|---|---|
| **False** | The comment could be made by reading only the changed lines. Typos, syntax errors, obvious logic bugs, style visible in the diff. |
| **Repo-specific conventions** | Relies on a convention, pattern, or architectural decision specific to this repository. |
| **Context outside changed files** | Requires reading files the PR did not touch. Base classes, shared utilities, configs, API contracts. |
| **Recent language / library updates** | Requires knowing a recent or non-obvious language feature, library behavior, deprecation, or framework semantic. |
| **Better implementation approach** | Suggests a meaningfully better design, algorithm, or API usage. Not a style preference, a fundamentally different approach. |

**Advanced is derived from Context Scope.** The mapping:

| Context Scope | Advanced |
|---|---|
| `diff` | `False` |
| `file` | `False` |
| `repo` | one of the four non-False values |
| `external` | one of the four non-False values |

**Hard rule.** `repo` or `external` scope with `advanced = "False"` is invalid. If you reach that combination, one of the two labels is wrong. Go back and re-check scope.

---

### Step 11: Record and Submit

Compile your labels into the output format. The `addressed` field is only present when the PR is merged.

```json
{
  "quality": "helpful",
  "addressed": "addressed",
  "severity": "critical",
  "context_scope": "file",
  "context": [
    {
      "diff_line": "168",
      "file_path": "src/monitors/incident.py",
      "why": "Bug line. Returns untransformed config"
    },
    {
      "diff_line": "161-163",
      "file_path": "src/monitors/incident.py",
      "why": "Config is created and transformed here"
    }
  ],
  "advanced": "False"
}
```

**Final checklist before submitting:**
- [ ] Verified the comment matches the `body` field
- [ ] Quality is based on factual correctness and usefulness
- [ ] Addressed is one of the four enum values. `empty` ONLY on OPEN PRs, otherwise one of `addressed`, `ignored`, `false_positive` (this includes closed-without-merge)
- [ ] Severity rates the issue, not the comment's tone
- [ ] Context scope reflects the broadest level needed
- [ ] Context array lists all evidence the reviewer used
- [ ] Advanced is the string enum value, not `true/false`
- [ ] `repo` or `external` scope is never paired with `advanced = "False"`
- [ ] All five axes are evaluated independently

---

## Quick Reference Card

| Axis | Values | Key Rule |
|---|---|---|
| **Quality** | helpful / unhelpful / wrong | Wrong means factually false, not "I disagree" |
| **Addressed** | empty / addressed / ignored / false_positive | `empty` ONLY on OPEN PRs. Closed PRs (merged or closed-no-merge) get one of the other three. Silence on a closed PR is not a false positive, default is `ignored` |
| **Severity** | nit / moderate / critical | Rate the issue, not the comment |
| **Context Scope** | diff / file / repo / external | Pick the broadest level needed |
| **Advanced** | False / Repo-specific conventions / Context outside changed files / Recent language / library updates / Better implementation approach | Derived from scope. `diff` or `file` maps to `False`. `repo` or `external` maps to one of the four non-False values |

### Independence Rule

All five axes are **independent**. Any combination is valid:
- Helpful plus Nit plus Diff plus `False`. Good comment about a minor style issue
- Wrong plus Critical plus File plus `False`. Incorrect claim about a severe issue
- Helpful plus Critical plus Repo plus `Context outside changed files`. Catches a real bug using knowledge from an untouched file
- Helpful plus Moderate plus Repo plus `Repo-specific conventions` plus `addressed`. On a merged PR where the team followed the convention in a later commit
