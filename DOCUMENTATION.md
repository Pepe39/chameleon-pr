# Code Review Quality Labeling. Complete Documentation

Label code review comments across five axes. **Quality**, **Addressed**, **Severity**, **Context Scope**, and **Advanced**. The goal is to build high-quality evaluation datasets for AI code review systems.

The `Addressed` axis is a 4-value enum. The values `addressed`, `ignored`, and `false_positive` apply to merged PRs. The fourth value `empty` is selected on PRs that are not merged, as an active selection rather than the absence of a label.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Comment States in GitHub](#2-comment-states-in-github)
3. [Step-by-Step Labeling Workflow](#3-step-by-step-labeling-workflow)
4. [Axis 1: Quality](#4-axis-1-quality)
5. [Axis 2: Addressed](#5-axis-2-addressed)
6. [Axis 3: Severity](#6-axis-3-severity)
7. [Axis 4: Context Scope](#7-axis-4-context-scope)
8. [Axis 5: Advanced](#8-axis-5-advanced)
9. [Justification Quality Standards](#9-justification-quality-standards)
10. [Labeling Format & Examples](#10-labeling-format--examples)
11. [Frequently Asked Questions](#11-frequently-asked-questions)
12. [Common Mistakes](#12-common-mistakes)
13. [Tips & Best Practices](#13-tips--best-practices)

---

## 1. Project Overview

This document provides step-by-step instructions for labeling code review comments with **Quality**, **Addressed**, **Severity**, **Context Scope**, and **Advanced**. Comments may come from either human reviewers or AI code review. The labeling criteria are the same regardless of source.

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

### The Five Labeling Axes

Every review comment is labeled across five independent axes. Each axis is evaluated independently. A comment can be helpful but nit-level, or wrong despite pointing at a critical issue.

| # | Axis | Question |
|---|---|---|
| 1 | **Quality** | Is the comment helpful, unhelpful, or wrong? |
| 2 | **Addressed** | Was the comment addressed, ignored, a false positive, or empty on a non-merged PR? 4-value enum, always present |
| 3 | **Severity** | Is the issue nit, moderate, or critical? |
| 4 | **Context Scope** | What level of context was needed. `diff`, `file`, `repo`, or `external` |
| 5 | **Advanced** | Which kind of beyond-diff knowledge did the comment rely on. Five-value enum. `False`, `Repo-specific conventions`, `Context outside changed files`, `Recent language / library updates`, `Better implementation approach` |

---

## 2. Comment States in GitHub

Code review comments in GitHub are anchored to specific lines in a specific commit (`original_commit_id`). Comments can be in one of four states.

### Possible States

| State | Description | Detection | Automatic/Manual |
|---|---|---|---|
| **Active** | Comment on code that has not been modified and was not marked as resolved | No special badges | -- |
| **Outdated** | The code the comment points to was modified in subsequent commits | Gray "Outdated" badge | Automatic |
| **Resolved** | Someone manually marked the thread as resolved | "Resolved" badge or collapsed thread | Manual |
| **Outdated & Resolved** | Both states combined | Both badges present | Both |

### Evaluation Rules by State

| State | Affects evaluation? | What to do |
|---|---|---|
| Active | No | Evaluate normally |
| Outdated | Yes | Evaluate against original code at `original_commit_id`. Classify outcome (see below) |
| Resolved | No | Ignore the resolved state, evaluate normally |
| Outdated & Resolved | Yes | Treat as Outdated. The Resolved state is just context |

Always evaluate against `original_commit_id`, never against HEAD. The "Resolved" state is UI metadata only and does not mean the technical issue was fixed.

**Common error:** Evaluating against the final code (HEAD) and concluding that "the comment does not make sense" when it was actually valid for the original code.

### Outdated Comment Subcases

When a comment is Outdated, compare the code at `original_commit_id` vs the current code (HEAD) and classify:

1. **Problem was fixed afterwards.** The issue existed at `original_commit_id` but was resolved in a later commit. The comment was valid at the time it was made.
2. **Problem still persists.** Despite the code changing, the issue still exists at HEAD. Evaluate normally.
3. **Change introduced a different problem.** The original issue was resolved but the change introduced a new issue. The comment is no longer relevant to the current code.

In all Outdated cases, evaluate Quality based on whether the comment was correct at the time it was made. Severity is based on the original code. Context Scope is from the original commit.

### How to Find Hidden Comments

When comments disappear from Files Changed (because the anchored lines were modified):

1. **Conversations dropdown** in Files Changed tab. Lists all conversations categorized as unresolved, resolved, outdated.
2. **Conversation tab.** Outdated comments appear with a gray "Outdated" badge. Resolved comments appear collapsed.
3. **Commits tab.** Click on the `original_commit_id` to see the comment in context with the code as it was when the comment was made.

### Force Push Special Case

A force push rewrites branch history. If `original_commit_id` was deleted by a force push, the comment becomes orphaned. Signs: the comment appears in Conversation tab but cannot navigate to its original context, or `original_commit_id` does not appear in the PR Commits tab.

When the original commit does not exist: recover context from the comment body and suggestion block if available. Document in Notes that the original commit does not exist. If information is sufficient, evaluate. If not, do not evaluate.

---

## 3. Step-by-Step Labeling Workflow

### Workflow at a Glance

```
STEP 0: Open PR → STEP 1: Find Comment → STEP 2: Review Diff → STEP 3: Browse Repo → STEP 4: Re-read Comment → STEP 5: Label 5 Axes
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

### Step 5: Label the Five Axes

With the diff, comment, and any needed context in hand, assign labels for each axis:

| Axis | Values |
|---|---|
| Quality | `helpful` / `unhelpful` / `wrong` |
| Addressed | `empty` / `addressed` / `ignored` / `false_positive`. `empty` on non-merged PRs |
| Severity | `nit` / `moderate` / `critical` |
| Context Scope | `diff` / `file` / `repo` / `external` |
| Advanced | `False` / `Repo-specific conventions` / `Context outside changed files` / `Recent language / library updates` / `Better implementation approach` |

Record your labels in the JSON format described in the Labeling Format guide (Section 10).

---

## 4. Axis 1: Quality

**Central Question:** "Does the comment add value to the code review?" It is not about whether the comment is "correct" in some technical sense. It is about whether it helps the developer improve their code.

Classify the overall quality of the review comment. Choose exactly one label.

### Helpful

**Definition:** Comment identifies a genuine issue, suggests a significant improvement, or detects a real bug.

**Example:** "This null check should happen before the dereference on L42, not after."

**Look for:** The comment is technically correct, actionable, and adds value. It points to something a competent engineer would want resolved. It does not matter whether the comment offers one option or several to fix the issue. What defines the label is the quality of the issue detected and whether the suggestion has substance, not the number of proposed paths.

### Unhelpful

**Definition:** Comment is pedantic, stylistic without substance, obvious, or not actionable. Can be technically correct but adds no practical value.

**Example:** "Consider adding a comment here." (on self-documenting code)

**Look for:** The comment may be technically true, but it adds no practical value. It does not identify a real issue or provide a significant improvement. Also Unhelpful when the comment offers multiple fix options that contradict each other or one is significantly worse than the other, so the comment confuses the dev instead of guiding them. Also Unhelpful when the comment points at a real problem but the proposed fix introduces regressions, incompatibilities, or worsens overall code quality.

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

### Mixed Comments Rule

When a comment makes multiple claims, evaluate each part individually. The most problematic part determines the final label:

1. If ANY part is **Wrong** -> the comment is **Wrong**
2. If no part is Wrong but ANY part is **Unhelpful** -> the comment is **Unhelpful**
3. Only if ALL parts add value -> **Helpful**

### Additional Edge Cases

| Situation | Label | Reasoning |
|---|---|---|
| Suggestion already implemented in the same PR | **Unhelpful** | The comment is redundant with the diff. It asks for something that already exists. |
| Comment on unchanged code, issue related to new functionality | **Helpful** | The issue affects the PR's changes even though the code itself was not modified. |
| Comment on unchanged code, issue completely separate from the PR | **Unhelpful** | Out of scope for this review. |
| Style trade-off where both options are valid (for vs forEach) | **Unhelpful** | Preference without objective improvement. Not a real issue. |
| Typo in executable identifier (function name, variable) | **Helpful** | Real issue that affects maintainability. |
| Typo inside a code comment (non-executable text) | **Unhelpful** | Depends on impact, but generally does not affect code behavior. |

---

## 5. Axis 2: Addressed

Determine whether the review comment was addressed. **The platform exposes a 4-value enum on every task.** The fourth value `empty` is selected on PRs that are not merged, since the merge state needed to evaluate the other three values does not exist yet.

Choose exactly one of four values:

| Value | Definition |
|---|---|
| **empty** | The PR is not merged. Selected when `state == OPEN` or the PR is closed without merging. This is an active selection on the platform, not the absence of a label |
| **addressed** | The merged code was changed in a way that addresses the underlying concern raised in the comment. The fix does not have to match the reviewer's exact suggestion. Any change that resolves the issue counts. Also counts when the PR author or a reviewer stated they will fix it later or in another PR |
| **ignored** | The merged code shows no changes related to the comment's concern, and no one dismissed the comment as invalid. The comment was simply not acted upon |
| **false_positive** | The PR author or another participant explicitly pushed back on the comment's validity. They explained why the comment does not apply, is based on a misunderstanding, or points to a non-issue |

### Decision Guide

```
Is the PR open or closed without merging?
  → Yes → EMPTY
  → No, PR is merged ↓

Did someone reply saying the comment was incorrect, invalid, or unnecessary?
  → Yes → FALSE_POSITIVE
  → No ↓

Was the code changed in a way that addresses the concern raised in the comment?
  → Yes → ADDRESSED
  → No ↓

The comment was not acted upon and no one dismissed it.
  → IGNORED
```

### Writing a Good Addressed Justification

Three rules:

1. **Self-contained.** Explain whether and how the comment was addressed using only evidence from the PR discussion and merged code. Do not mention quality, severity, context scope, or advanced. Those are separate axes.
2. **Specific, not generic.** Name the specific commit, code change, or reply that demonstrates how the comment was handled. "The comment was addressed" without evidence is not a justification.
3. **Check the final merged state.** Compare the comment's suggestion against what was actually merged. A comment can be addressed even if the exact suggestion was not followed. What matters is whether the underlying concern was resolved.

---

## 6. Axis 3: Severity

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

## 7. Axis 4: Context Scope

**Central Question:** "What did the reviewer have to read or know to make this comment?" It is NOT about where the comment appears. It is NOT about where the problematic code is. It IS about what information was needed to identify the issue.

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

### New Files Rule

If the target file is completely new in the PR (diff header `@@ -0,0 +1,N @@`, all lines are added), the scope is **diff** even if you need to read multiple parts of the file. There is no "file" scope for files that did not exist before the PR.

### Common Errors

- **Defaulting to Diff.** A simple comment may require broad context. The comment's simplicity does not determine the scope.
- **Choosing File because the file is large.** The file's size is irrelevant. What matters is whether the lines you need are in the diff or not.
- **Choosing Repo because "Copilot must have read other files."** Do not speculate about what Copilot consumed. Evaluate what information was needed to make the comment.
- **Forgetting the new files rule.** New file means everything is diff. There is no "file" scope for files that did not exist.
- **Do not conflate analyst verification with reviewer observation.** You may read the full file or browse the repo to verify the comment's claims. That does not mean the reviewer needed that context to make the comment.

---

## 8. Axis 5: Advanced

Does the comment go beyond what is obvious from reading the files changed in the PR, and if so, which kind of beyond-diff knowledge did the reviewer rely on?

**Advanced is a 5-value string enum, not a boolean.** One of `False`, `Repo-specific conventions`, `Context outside changed files`, `Recent language / library updates`, `Better implementation approach`. The label is derived automatically from Context Scope via the mapping below.

### Mapping Rule

| Context Scope | Advanced |
|---|---|
| **diff** | `False` |
| **file** | `False` |
| **repo** | one of the four beyond-diff values |
| **external** | one of the four beyond-diff values |

You do not need to evaluate Context Scope and Advanced separately. Once you determine the Context Scope, whether Advanced is `False` or one of the four beyond-diff values is automatically determined.

Diff and File are within the PR's files, so no beyond-diff knowledge was needed. Advanced is `False`. Repo and External are outside the PR's files, so beyond-diff knowledge was needed. Advanced is one of the four non-False values.

### Hard Rule

`context_scope = "repo"` with `advanced = "False"` is invalid. Same for `external` with `False`. Crossing the diff boundary is itself beyond-diff knowledge. If you reach that combination, one of the two labels is wrong. This is a blocking inconsistency that gates output generation and triggers a REPLACE in review.

### Beyond-Diff Values

When Context Scope is `repo` or `external`, pick the value that best explains which kind of beyond-diff knowledge the reviewer relied on:

| Value | Description |
|---|---|
| **Repo-specific conventions** | Pertains to conventions, patterns, or architectural decisions specific to this repository that are not universally known. |
| **Context outside changed files** | Requires knowledge from files not touched by the PR. Base classes, shared utilities, config, API contracts. |
| **Recent language / library updates** | Requires awareness of recent or non-obvious language features, library behavior, deprecations, or framework semantics. |
| **Better implementation approach** | Suggests a meaningfully better way to implement. Not just style, but a fundamentally improved design, algorithm, or API usage. |

---

## 9. Justification Quality Standards

Each axis produces its own justification field. These justifications power the feedback layer that helps reviewers calibrate over time. Low-quality justifications degrade the entire dataset.

### A good justification

- Addresses only the axis it belongs to
- Names the specific code element, function, or variable involved
- States the reasoning, not just the conclusion
- Could stand alone as an explanation to a new annotator

### A poor justification

- Copies language from another axis, for example `because it is critical` in a quality justification
- Is a one-word echo of the label, for example `Helpful because it is helpful`
- Is generic enough to apply to any comment
- Is absent or blank

### Self-Containment Rule

Think of the justification fields as independent paragraphs written by independent reviewers, one per axis. Each paragraph may only use information relevant to its axis. If your quality justification mentions severity, or your severity justification mentions context scope, those justifications are invalid.

| Justification field | Only explain | Never mention |
|---|---|---|
| `quality_justification` | Why the comment is correct, incorrect, or useless | Addressed, severity, scope, advanced |
| `addressed_justification` | Whether and how the comment was addressed in the merged code, or for `empty` why the PR's merge state does not allow evaluation | Quality, severity, scope, advanced |
| `severity_justification` | What specific impact or risk the issue poses | Quality, addressed, scope, advanced |
| `context.why` entries | What each piece of evidence showed the reviewer | Quality, addressed, severity, advanced |
| `advanced_justification` | Whether special beyond-diff knowledge was needed, and what it was | Quality, addressed, severity, scope |

### Golden Example

Use this as your calibration anchor. If your justifications are shorter, vaguer, or mix axes, revise them.

**Task input.**

- PR title. Add user search endpoint with pagination
- File. `app/api/users/search.ts`
- Diff line. `const qb = createQueryBuilder(User).where(filters);`
- Comment under review. "This won't apply the tenant scoping. `asUserResponse` assumes the query is already tenant-filtered, so calling it on a global query will leak users from other tenants."

**Labels and justifications.**

`quality = helpful`

> The reviewer correctly identifies that `createQueryBuilder(User).where(filters)` produces a global query. `filters` is a request-derived object and the surrounding handler never injects a `tenantId` predicate before passing it. `asUserResponse` trusts its caller to scope the query, so the comment names a real correctness gap and points at the right fix surface, the query builder, not the serializer.

`severity = moderate`

> The missing tenant predicate in `createQueryBuilder(User).where(filters)` would cause the search endpoint to return user rows that the caller is not entitled to see. The impact is a logically incorrect response set under a non-default code path, not an immediate exfiltration of credentials or destructive write. Moderate fits the framework's definition, that is "could affect behavior but unlikely to cause serious harm in the typical case". The fix is local to the query builder.

`context_scope = repo`

Context entries. Each `why` is standalone, line numbers live in `diff_line`:

```json
[
  {
    "diff_line": "DIFF",
    "file_path": "app/api/users/search.ts",
    "why": "Shows the offending call site. createQueryBuilder is invoked with no tenant predicate before filters are applied"
  },
  {
    "diff_line": null,
    "file_path": "app/serializers/userResponse.ts",
    "why": "asUserResponse is defined here and contains no tenant check. It trusts callers to pass an already-scoped query, which is the convention the comment relies on"
  },
  {
    "diff_line": null,
    "file_path": "app/db/queryBuilder.ts",
    "why": "createQueryBuilder is the generic factory. Verifies that no implicit tenant scope is added at construction time"
  }
]
```

`advanced = Context outside changed files`

> The bug is invisible from the diff alone. Verifying the comment requires opening two files the PR did not touch. `app/serializers/userResponse.ts` to confirm `asUserResponse` has no internal tenant guard and trusts callers to pre-scope the query, and `app/db/queryBuilder.ts` to confirm `createQueryBuilder` does not auto-inject a tenant predicate at construction time. Because the determining knowledge lives in untouched files, the right enum value is `Context outside changed files` rather than `Repo-specific conventions`.

If a justification you write is shorter than the examples above, vaguer about which code element it refers to, or mixes axes, rewrite it before submitting.

---

## 10. Labeling Format & Examples

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

## 11. Frequently Asked Questions

### How should I distinguish between Quality and Severity?

Quality measures whether the comment is correct and useful. Severity measures how serious the underlying issue is. A comment can be perfectly correct and useful (helpful) while pointing out a minor style preference (nit). Similarly, a comment can be wrong even if the issue it tried to flag would have been critical. **Always evaluate the two axes independently.**

### If context_scope is "diff", does that mean only the diff hunk where the comment was placed?

No. Setting `context_scope` to `"diff"` means the reviewer only needed the PR's changed lines, but a PR can have changed lines across multiple files. If the reviewer needs context from two diff hunks in two different files, the scope is still `"diff"` because no context beyond the changed lines was needed. The `context` array should list entries from both files.

### If I label context_scope as "file", do I still fill in diff_line?

Yes. You still fill in `diff_line` for any context entry that points to a specific line, including lines that are inside the diff. For example, if `context_scope` is `"file"` but both context entries have `diff_line` values (`"168"` and `"161-163"`), that's correct — those are the specific lines the reviewer needed to look at, even though the scope is `"file"` because the reviewer needed to read beyond the diff hunks within the same file.

---

## 12. Common Mistakes

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

### Mistake 5: Evaluating Advanced Independently

**The Mistake:** Evaluating Advanced as an independent axis, picking a non-False value for complex or insightful comments even when Context Scope is `diff` or `file`. Or picking a non-False value based on how hard the comment was to write, instead of which beyond-diff knowledge the reviewer actually needed.

**The Fix:** Advanced is derived from Context Scope. `diff` or `file` maps to `False`. `repo` or `external` maps to one of the four beyond-diff values. Do not override this mapping based on the comment's perceived difficulty or insight. Hardness is not the test. What information was required outside the diff is the test.

### Mistake 6: Repo Scope With Advanced `False`

**Hard rule.** If `context_scope = "repo"`, then `advanced` is never `False`. Same for `external`. Repo scope means the reviewer needed information from a file the PR did not touch, and that is by definition one of the four beyond-diff values. Almost always `Context outside changed files`.

**The Mistake:** Marking `context_scope = "repo"` while leaving `advanced = "False"`. That combination is internally inconsistent. You have explicitly stated the reviewer pulled in information from outside the changed files and that no beyond-diff knowledge was needed.

**The Fix:** If you choose `repo` or `external` scope, pick the matching Advanced value. The default is `Context outside changed files`. Use `Repo-specific conventions` if the reviewer relied on a general convention rather than a single specific file. If you cannot articulate which non-False Advanced value applies, the scope is probably not really `repo`. Re-check it.

### Mistake 7: Underrating Context Scope When Multiple Files Were Read

**The Mistake:** Selecting `file` scope when the reviewer actually had to open and read several other files in the repo to verify the comment, just because all the relevant logic happened to fit in one screen.

**The Fix:** If verifying the claim required reading code in any file other than the one being commented on, scope is `repo`, not `file`. The number of files matters. The line count does not. Walk through your own reasoning and list every file you opened. That list determines the scope.

### Mistake 8: Not Checking Out the Correct Commit

**The Mistake:** Reviewing a PR comment against the main branch or any branch other than the exact commit the comment was written on. The file the comment refers to may have shifted, been renamed, or removed entirely since then.

**The Fix:** Always check out the exact commit SHA that the PR comment was made on. The pipeline records this as `original_commit_id` or `comment_commit` in `task_info.md`. Verify your local file matches the diff line in the task. If it does not, you are reviewing the wrong code and your labels will be invalid.

### Mistake 9: Vague Justifications Without Task Evidence

**The Mistake:** Writing justifications that recycle the task title or PR description instead of pointing at the specific code element that drove the label decision.

**The Fix:** Every justification must cite a concrete piece of evidence from the actual code. A variable name, a function, a return value, a contract. If a justification could be copy-pasted across ten unrelated PRs, it is too vague. Rewrite it to name the exact thing that made you choose the label.

**Weak example (recycles PR text):**
```
quality: This is a refactor of the user search endpoint and the comment is helpful for the team.
severity: Tenant leaks are bad.
scope: Multiple files involved.
advanced: Requires experience.
```
None of these would survive review. Each could be pasted into any unrelated PR.

**Strong example (names the exact code element):**
```
quality: createQueryBuilder(User).where(filters) is built from a request-derived filters object with no tenant predicate. The comment correctly names the missing scope and the right fix surface, the query builder, not the serializer.
severity: Returning UserResponse rows from other tenants is a logically incorrect response under a non-default code path. Moderate impact, fix is local to the query builder.
scope: Verifying the bug requires opening userResponse.ts and queryBuilder.ts, neither of which the PR touches.
advanced: Context outside changed files. asUserResponse is defined in an untouched file and trusts callers to pre-scope.
```
Each justification names the actual function or variable that drove the label.

### Mistake 10: Line Numbers in the Wrong Places

**The Rule:** Line numbers belong in `context.diff_line`. They do not belong in `quality_justification`, `addressed_justification`, `severity_justification`, `advanced_justification`, or the `why` field of a context entry. Justifications describe code semantically, by variable, function, or behavior.

**The Mistake, line numbers in prose:**
```
quality_justification: The bug on line 168 ignores the value built on lines 161-163.
```
Line numbers go stale, duplicate the context array, and can drift from the actual `diff_line`.

**The Fix, semantic anchors:**
```
quality_justification: The return statement passes the original monitor_environment.monitor.config instead of the prepared config variable built just above it.
```
Names the elements. The paired context entry holds the exact line.

---

## 13. Tips & Best Practices

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

### Addressed
- 4-value enum, always present. `empty`, `addressed`, `ignored`, `false_positive`.
- `empty` is the active selection for non-merged PRs. Not the absence of a label.
- `addressed` is generous. Any merged change that resolves the underlying concern counts, even if the exact suggestion was not followed.
- `false_positive` requires an explicit rebuttal from the PR author or another participant. Silence is not rebuttal.
- `ignored` is the default when the code did not change and no one dismissed the comment.

### Advanced
- Advanced is a 5-value string enum, not a boolean.
- Advanced is derived from Context Scope. `diff` or `file` maps to `False`. `repo` or `external` maps to one of the four non-False values.
- Do not evaluate Advanced separately. Once Context Scope is set, the mapping is automatic.
- Hard rule. `repo` or `external` with `False` is invalid. If you see that combination, one of the two labels is wrong.

### General Workflow
- Always double-check that the comment in the discussion matches the `body` field in the input data before labeling.
- When unsure between two values, re-read the definitions. The answer is almost always in the exact wording of the axis rules.
