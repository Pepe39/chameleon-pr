# Code Review Quality Labeling — Complete Documentation

Label code review comments across four axes — **Quality**, **Severity**, **Context Scope**, and **Advanced** — to build high-quality evaluation datasets for AI code review systems.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Step-by-Step Labeling Workflow](#2-step-by-step-labeling-workflow)
3. [Axis 1: Quality](#3-axis-1-quality)
4. [Axis 2: Severity](#4-axis-2-severity)
5. [Axis 3: Context Scope](#5-axis-3-context-scope)
6. [Axis 4: Advanced](#6-axis-4-advanced)
7. [Labeling Format & Examples](#7-labeling-format--examples)
8. [Frequently Asked Questions](#8-frequently-asked-questions)
9. [Common Mistakes](#9-common-mistakes)
10. [Tips & Best Practices](#10-tips--best-practices)

---

## 1. Project Overview

This document provides step-by-step instructions for labeling code review comments with **Quality**, **Severity**, **Context Scope**, and **Advanced**. Comments may come from either human reviewers or AI code review — the labeling criteria are the same regardless of source.

### Why This Matters

Your labels directly improve AI code review systems used by millions of developers. Each label teaches the model what makes a review comment genuinely useful versus noisy or incorrect. High-quality labels lead to code review AI that catches real bugs, ignores false alarms, and gives feedback engineers actually want to act on. Low-quality or inconsistent labels train models that waste developers' time.

### What You Are Given

For each labeling task, you will receive a JSON object with the following fields:

| Field Group | Fields | Purpose |
|---|---|---|
| **PR Identification** | `pull_request_url`, `nwo`, `head_sha` | Identify and navigate to the PR |
| **Comment Location** | `file_path`, `diff_line` | Exactly which file and line the comment targets |
| **Review Comment** | `body` | The comment text you need to label |
| **Navigation Links** | `discussion_url`, `repo_url` | `discussion_url` → comment on PR; `repo_url` → browse repo tree at correct commit |

### The Four Labeling Axes

Every review comment is labeled across four independent axes. Each axis is evaluated independently — a comment can be helpful but nit-level, or wrong despite pointing at a critical issue.

| # | Axis | Question |
|---|---|---|
| 1 | **Quality** | Is the comment helpful, unhelpful, or wrong? |
| 2 | **Severity** | Is the issue nit, moderate, or critical? |
| 3 | **Context Scope** | What level of context was needed — diff, file, repo, or external? |
| 4 | **Advanced** | Does the comment go beyond what is obvious from the diff? (true / false) |

---

## 2. Step-by-Step Labeling Workflow

### Workflow at a Glance

```
STEP 0: Open PR → STEP 1: Find Comment → STEP 2: Review Diff → STEP 3: Browse Repo → STEP 4: Re-read Comment → STEP 5: Label 4 Axes
```

Steps 1–3 may need to be repeated as you build understanding. Step 3 (Browse Repo) is only needed when the comment requires context beyond the changed files.

### Step 0: Open the PR URL

Open the PR URL. Read the PR title and description to understand what the repository is about and what the PR changes. This gives you the high-level context needed to evaluate any review comment.

### Step 1: Go to the Discussion

Click on `discussion_url`, which takes you directly to the review comment shown alongside its surrounding diff hunk.

> **Checkpoint:** Verify the comment matches the `body` field in the input data before proceeding.

### Step 2: Review the Diff and Changed Files

From the discussion view, click on the file name at the top of the diff to navigate to the PR's **Files Changed** tab. The `diff_line` value from the input data helps you locate the specific line where the comment is anchored. Read through the full diff hunks across multiple changed files to build a comprehensive understanding of this PR.

### Step 3: Browse the Repository (IF NEEDED)

If the comment requires context beyond the changed files, use `repo_url` to browse the repo tree at the PR head commit. Explore the files in the repository at the correct snapshot — look up imports, shared utilities, base classes, or any other file mentioned or implied by the comment at the repo level.

### Step 4: Re-read the Review Comment

Read the `body` field in the input data again. This is the review comment you need to label. To fully understand what issue this comment is pointing out and the specific code context needed to make such a comment, you may need to navigate actively using Steps 1–3 repeatedly.

> **Tip:** Don't rush to label. Re-reading the comment after understanding the full diff often changes your initial impression.

### Step 5: Label the Four Axes

With the diff, comment, and any needed context in hand, assign labels for each axis:

| Axis | Values |
|---|---|
| Quality | `helpful` / `unhelpful` / `wrong` |
| Severity | `nit` / `moderate` / `critical` |
| Context Scope | `diff` / `file` / `repo` / `external` |
| Advanced | `true` / `false` |

Record your labels in the JSON format described in the Labeling Format guide (Section 7).

---

## 3. Axis 1: Quality

Classify the overall quality of the review comment. Choose exactly one label.

### Helpful

**Definition:** Comment identifies a genuine issue, suggests a meaningful improvement, or catches a real bug.

**Example:** "This null check should happen before the dereference on L42, not after."

**Look for:** The comment is technically correct, actionable, and adds value. It points to something a competent engineer would want addressed.

### Unhelpful

**Definition:** Comment is pedantic, stylistic without substance, obvious, or not actionable.

**Example:** "Consider adding a comment here." (on self-documenting code)

**Look for:** The comment may be technically true, but it adds no practical value. It doesn't identify a real issue or provide a meaningful improvement.

### Wrong

**Definition:** Comment is factually incorrect, suggests a change that would introduce a bug, or misunderstands the code.

**Example:** "This will cause an integer overflow" (when the type is actually a long)

**Look for:** The comment is based on a misunderstanding of the code, the language, or the domain. Following the suggestion would make the code worse.

### Decision Guide

Use this flowchart when you're unsure which label to apply:

```
Is the comment factually incorrect? Does it misunderstand the code,
suggest a change that would introduce a bug, or make a false claim
about language/framework behavior?
  → Yes → WRONG
  → No ↓

Does the comment identify a genuine issue, catch a real bug,
or suggest a meaningful improvement? Is it actionable and specific?
  → Yes → HELPFUL
  → No ↓

The comment is technically correct but adds no practical value.
It may be pedantic, obvious, stylistic without substance, or not actionable.
  → UNHELPFUL
```

### Do's and Don'ts

| Scenario | Correct Label | Common Mistake |
|---|---|---|
| "This query is vulnerable to SQL injection — use parameterized queries." | **Helpful** — Identifies a real security issue with a specific fix. | Labeling as Wrong because you think the code is safe. Verify against the actual code before overriding the comment's claim. |
| "Consider renaming x to count." | **Unhelpful** — Naming preference on a local variable in a 3-line function. No impact. | Labeling as Helpful because better names are always good. A naming nit on a trivial local variable adds no practical value. |
| "This will crash on Python 2 — dict.items() returns a list, not a view." (Code is Python 3 only.) | **Wrong** — Factually incorrect about the runtime environment. | Labeling as Unhelpful because it sounds like it could be valid. If the claim is factually false, it's Wrong, not Unhelpful. |

---

## 4. Axis 2: Severity

Assess how severe the issue is that the review comment points out. **Severity measures the issue itself, not the quality of the comment.**

### Nit

**Low impact — safe to defer**

Minor issues that can safely be ignored or deferred. They pose no meaningful risk and do not affect the code's behavior.

**Typical examples:** Style nit-picks, naming preferences, cosmetic suggestions, readability improvements, documentation gaps, minor code smell.

### Moderate

**Medium impact — should improve**

Issues that affect or could affect the code's behavior but are unlikely to cause serious harm. The code works but should be improved.

**Typical examples:** Missing edge case handling that is unlikely to occur, suboptimal but functional logic, missing null checks on uncommon paths.

### Critical

**High impact — must fix before merge**

Severe issues that pose a significant and concrete risk to the code's correctness, security, or stability. A senior engineer would insist this be fixed before merging.

**Typical examples:** SQL injection vulnerability, authentication bypass, data corruption, race conditions in concurrent code, returning wrong results, build-breaking errors.

### Borderline Example: Same Code, Different Severity

The same missing null check can be nit or critical depending on context:

| Severity | Comment | Context |
|---|---|---|
| **NIT** | "Missing null check on user.preferences before accessing .theme." | `preferences` is always populated by the ORM during user creation. The only way it's null is a direct DB edit. No user has ever hit this path. |
| **CRITICAL** | "Missing null check on user.session before accessing .token." | `session` is null for unauthenticated users, and this endpoint is reachable without login. Causes a 500 error on every anonymous request. |

> **Key insight:** Both comments say "missing null check" — the severity depends on the likelihood and impact of the null case, not the wording of the comment.

### Severity Labeling Rules

1. **Focus on the issue itself**, not the comment's wording. Even a well-written comment about a trivial style preference is still "nit."
2. If the comment points out **multiple issues**, rate by the **most severe** issue mentioned.
3. **Quick test when unsure:** "Would a senior engineer insist this be fixed before merging?" If yes → critical.

---

## 5. Axis 3: Context Scope

Determine what level of context a reviewer would need to confidently make this comment. Choose exactly one scope level. Each level includes everything below it. **Pick the broadest scope needed.**

```
EXTERNAL — Outside the repository
    ↑
REPO — Untouched files in the repository
    ↑
FILE — Within PR-touched files, beyond diff
    ↑
DIFF — Only the changed lines
```

### Diff

**Narrowest scope.** The comment can be made by reading only the PR's changed lines (the diff hunks) — possibly across multiple changed files in the same PR. No context beyond the diff is needed.

**Typical examples:** Typos in new code, obvious syntax errors, clearly wrong constants, style violations visible in the diff alone, inconsistency between two diff hunks in different files of the same PR.

### File

The comment requires reading beyond the diff hunks but within the file(s) that the PR touches. The reviewer needed surrounding functions, imports, class definitions, or other code that is in a PR-changed file but outside its changed lines. A PR can touch multiple files, so "file" scope can span several of them.

**Typical examples:** Using a variable defined elsewhere in the file, contradicting a pattern established earlier in the same file, missing an import at the top of the file, duplicating logic already present in a different file that the PR also modifies.

### Repo

The comment requires knowledge from files not changed by the PR — other source files, configuration files, tests, documentation, or build scripts elsewhere in the repository.

**Typical examples:** Inconsistency with a shared utility function in an untouched file, violating a pattern set in a base class the PR doesn't modify, missing an update to a config file not in the PR, breaking an API contract defined in another module.

### External

**Broadest scope.** The comment requires knowledge outside the repository entirely — such as business requirements, customer expectations, or domain-specific constraints that are not documented in the repo.

**Typical examples:** The product team decided this feature must support offline mode but the implementation assumes constant connectivity.

### How to Record Context Scope

Two fields work together:

- **`context_scope`** — A single string (`"diff"`, `"file"`, `"repo"`, or `"external"`) that captures the broadest level of context the reviewer needed.
- **`context`** — An array of objects listing every specific piece of evidence the reviewer used. Each entry has three fields:
  - `diff_line` — A line number or range (e.g., `"42"`, `"42-50"`). Set to `null` if the exact line is hard to locate.
  - `file_path` — Repo-relative path to the file.
  - `why` — A short phrase explaining why this context matters.

**Example — scope: "repo":**

```json
{
  "context_scope": "repo",
  "context": [
    {
      "diff_line": "45",
      "file_path": "src/api/handlers/user.py",
      "why": "The new handler calls validate_email() without importing it"
    },
    {
      "diff_line": null,
      "file_path": "src/utils/validators.py",
      "why": "validate_email() is defined here — not touched by the PR"
    }
  ]
}
```

### Context Labeling Rules

- `context_scope` should reflect the **broadest scope needed**. If the reviewer needed both diff and file context, set it to `"file"`. If they also needed a repo file not touched by the PR, set it to `"repo"`.
- List **all** pieces of context in the `context` array. If only the diff was needed, one entry is enough. If the reviewer also needs to read another part of the file or another file, add those as additional entries.
- If `context_scope` is `"external"`, the `context` array may be empty (`[]`) since the knowledge comes from outside the repository (e.g., language docs, framework behavior, RFCs).

---

## 6. Axis 4: Advanced

Does the comment go beyond what is obvious from reading the changed lines alone? This is a **binary label**.

### When to Label `true`

Label as `true` if the comment meets **one or more** of these criteria:

| Criteria | Description |
|---|---|
| **Repo-Specific Conventions** | Pertains to conventions, patterns, or architectural decisions specific to this repository that are not universally known. |
| **Context Outside Changed Files** | Requires knowledge from files not touched by the PR (base classes, shared utilities, config, API contracts). |
| **Recent Language / Library Updates** | Requires awareness of recent or non-obvious language features, library behavior, deprecations, or framework semantics. |
| **Better Implementation Approach** | Suggests a meaningfully better way to implement — not just style, but a fundamentally improved design, algorithm, or API usage. |

### When to Label `false`

The comment doesn't meet any of the criteria above. Comments that are obvious from reading the diff alone — such as typos, simple style issues, or straightforward logic errors visible in the changed lines — are **not** advanced.

---

## 7. Labeling Format & Examples

### Worked Example 1: Helpful + Critical + File + Not Advanced

**PR Title:** Reorganize incident creation / issue occurrence logic
**Diff:** In `src/sentry/monitors/logic/incident_occurrence.py` (new file), lines 160-171.

| Axis | Label | Reasoning |
|---|---|---|
| **Quality** | HELPFUL | The comment correctly identifies that the code copies and transforms config but then ignores the copy, passing the original untransformed config in the return dict. The fix is clear: replace `monitor_environment.monitor.config` with `config` on line 168. |
| **Severity** | CRITICAL | The `schedule_type` display transformation is silently lost. Downstream consumers (e.g., issue evidence displays for monitor incidents) will receive the raw schedule type integer instead of a human-readable string, producing confusing or broken output. |
| **Scope** | FILE | The bug line (168) is in the diff, but understanding why it is wrong requires reading lines 161-163 of the same file, where `config` is created and transformed. The file is new in this PR, so the reviewer needed to read non-diff-hunk lines within the same file. |
| **Advanced** | FALSE | Noticing that a local variable is created but not used in the return dict is a common code review pattern. |

### Worked Example 2: Unhelpful + Nit + Diff + Not Advanced

**PR Title:** Add dark mode toggle to settings page
**Comment:** "Consider using const instead of let here."
**Code at diff line 23:** `let isDark = false;` (variable is never reassigned)

| Axis | Label | Reasoning |
|---|---|---|
| **Quality** | UNHELPFUL | While technically correct (the variable is never reassigned), this is a trivial linting issue that automated tools catch. No engineering insight required. |
| **Severity** | NIT | Using `let` instead of `const` doesn't affect behavior, security, or correctness. Pure style preference. |
| **Scope** | DIFF | The variable declaration is visible in the diff. No context beyond the changed line is needed. |
| **Advanced** | FALSE | This is a basic linting observation visible directly in the diff. |

### Worked Example 3: Wrong + Critical + File + Not Advanced

**PR Title:** Optimize user search with caching layer
**Comment:** "This Redis cache key doesn't include the tenant ID — different tenants will see each other's data."
**Code at diff line 89:** `cache_key = f"user_search:{query}"`
**Actual code at line 12 (not in diff):** The `query` variable already includes `tenant_id` via the query builder on line 72.

| Axis | Label | Reasoning |
|---|---|---|
| **Quality** | WRONG | The comment claims a data leak, but the query string already contains the tenant ID (built upstream on line 72). The cache key IS tenant-scoped — the comment misunderstands the data flow. |
| **Severity** | CRITICAL | The issue the comment tried to flag (cross-tenant data leak) would be critical if it were real. Rate severity by the issue, not the comment's correctness. |
| **Scope** | FILE | You need to read line 72 (the query builder) in the same file to verify whether `query` already includes the tenant ID. This is beyond the diff hunk but within the same file. |
| **Advanced** | FALSE | Tracing a variable's content back through the same file is a standard code review skill, not deep domain knowledge. |

> **Key lesson:** Quality and Severity are independent. A wrong comment about a nit would be Wrong + Nit. A wrong comment about a critical issue is Wrong + Critical.

---

## 8. Frequently Asked Questions

### How should I distinguish between Quality and Severity?

Quality measures whether the comment is correct and useful. Severity measures how serious the underlying issue is. A comment can be perfectly correct and useful (helpful) while pointing out a minor style preference (nit). Similarly, a comment can be wrong even if the issue it tried to flag would have been critical. **Always evaluate the two axes independently.**

### If context_scope is "diff", does that mean only the diff hunk where the comment was placed?

No. Setting `context_scope` to `"diff"` means the reviewer only needed the PR's changed lines, but a PR can have changed lines across multiple files. If the reviewer needs context from two diff hunks in two different files, the scope is still `"diff"` because no context beyond the changed lines was needed. The `context` array should list entries from both files.

### If I label context_scope as "file", do I still fill in diff_line?

Yes. You still fill in `diff_line` for any context entry that points to a specific line, including lines that are inside the diff. For example, if `context_scope` is `"file"` but both context entries have `diff_line` values (`"168"` and `"161-163"`), that's correct — those are the specific lines the reviewer needed to look at, even though the scope is `"file"` because the reviewer needed to read beyond the diff hunks within the same file.

---

## 9. Common Mistakes

These mistakes reduce dataset quality and hurt model training. Review these patterns to avoid the most common errors.

### Mistake 1: Confusing Unhelpful with Wrong

**The Mistake:** Labeling a comment as Wrong just because you disagree with the suggestion or think it's unnecessary.

**The Fix:** Wrong means **factually incorrect**. If a comment says "add a comment here" and you think it's unnecessary, that's Unhelpful — not Wrong. Wrong is reserved for false claims.

### Mistake 2: Letting Comment Wording Influence Severity

**The Mistake:** Rating a comment as Critical because the reviewer wrote urgently ("This MUST be fixed!") even though the underlying issue is just a style preference.

**The Fix:** Severity rates the **issue**, not the **tone**. An urgently worded comment about a naming preference is still Nit. A calmly worded comment about a SQL injection is still Critical.

### Mistake 3: Defaulting to Diff Scope

**The Mistake:** Choosing Diff scope because the comment is written on a diff line, without considering whether the reviewer needed to read other code to make that comment.

**The Fix:** Context Scope is about **what the reviewer needed to know**, not where the comment appears. A comment on a diff line might require reading the whole file or other files to verify.

### Mistake 3b: Inflating Scope Based on Analyst Verification

**The Mistake:** Choosing File or Repo scope because the analyst browsed the full file or repo to verify the comment's claims, even though the reviewer could have made the comment from the diff alone.

**The Fix:** Context Scope reflects what the **reviewer** minimally needed to make the comment, not what the analyst read during verification. You may read the full file to confirm a pattern, but if the pattern was already visible in the diff's changed lines, the scope is still Diff. Always ask: "Could the reviewer have made this comment from the diff alone?" not "Did I read beyond the diff to check it?"

### Mistake 4: Coupling Quality and Severity

**The Mistake:** Assuming that a Wrong comment must have Nit severity ("since the comment is wrong, the issue doesn't count"), or that Helpful must mean Critical.

**The Fix:** The axes are independent. A Wrong comment about a real security vulnerability is Wrong + Critical. A Helpful comment about a naming nit is Helpful + Nit. Always rate each axis on its own.

### Mistake 5: Marking Everything as Advanced

**The Mistake:** Labeling every non-trivial comment as Advanced = true because it requires some thought to understand.

**The Fix:** Advanced means the comment requires knowledge most reviewers wouldn't have from the diff alone — repo conventions, untouched files, or non-obvious framework behavior. A complex but visible logic error in the diff is still `false`.

---

## 10. Tips & Best Practices

### Quality
- Quality and Severity are independent axes. A comment can be helpful but nit-level, or wrong about a critical issue.
- A comment that restates what the code obviously does is **Unhelpful**, even if technically correct.
- **Wrong** means the comment is factually incorrect or would introduce a bug — not just that you disagree with the suggestion.

### Severity
- Focus on the **issue itself**, not the comment's wording. A well-written comment about a trivial style preference is still nit.
- A missing null check in a rarely-used utility is moderate. The same missing check in a payment handler is critical.

### Context Scope
- Always pick the **broadest level** needed. If the reviewer needed both diff and file context, set it to file.
- `diff` means only the changed lines were needed — but those lines can span multiple files in the same PR.
- `external` means the reviewer relied on knowledge outside the repo entirely — API docs, RFCs, language specs, etc.

### Advanced
- Advanced = true requires deeper knowledge beyond the diff: repo conventions, untouched files, recent library changes, or better implementation approaches.
- If the comment could have been written by seeing only the changed lines, Advanced is false — even if the comment is insightful.

### General Workflow
- Always double-check that the comment in the discussion matches the `body` field in the input data before labeling.
- When unsure between two values, re-read the definitions — the answer is almost always in the exact wording of the axis rules.
