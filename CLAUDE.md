# Project Instructions

## Task Isolation Rule

During task execution (steps 01-08), focus exclusively on the task at hand: the PR, the diff, the comment, and the labeling. Do NOT:
- Modify project documentation, guides, commands, or templates
- Refactor or improve the labeling pipeline itself
- Update CLAUDE.md, DOCUMENTATION.md, axis docs, or step commands
- Fix issues found in guides or commands mid-task

If you notice a problem with the guides or pipeline during a task, finish the task first, then report the issue to the user. Meta-work (improving docs, fixing commands, adding features to the pipeline) must be requested explicitly by the user outside of task execution.

## Empty-row validation flags

When the user pastes a validation error that is ONLY about empty context rows, meaning `context-entries-have-file-path` or `context-entries-have-why` whose failing row is literally `{"why":"","diff_line":"","file_path":""}`, treat it as a known client-side issue. The fix lives in `extension/background.js` (scraper skips blank rows, fill reuses empty rows, post-fill sweep deletes strays).

Do NOT touch the task's deliverables for this flag. Just acknowledge it in one line and wait for the next instruction. Only dig into the task if the user explicitly asks, or if the validation error is about something other than an empty row.

## Nested-comment tasks

Some tasks arrive with a body that is a **nested reply** inside an existing GitHub review thread. The reply alone is often ambiguous. The intent only becomes clear when you read the ancestor chain from the root of the thread down to the body.

Detection and scope are handled automatically by the pipeline. You do not need to detect threading by hand. What you need to know:

- **Step 02** queries `in_reply_to_id` for the comment. If the body is a reply, it walks the ancestors and writes `work/thread.md` with the full chain, root first, body last. It also stamps `task_info.md` Input Data with `Comment Type: top-level` or `Comment Type: nested reply (see work/thread.md, {N} ancestors)`.
- **Scope of the thread:** ancestors only. Sibling replies that came after the body, and other threads in the same PR, are out of scope. The thread exists to explain what the body is replying to, nothing else.
- **Steps 03-07 treat the body as the only target.** The ancestors are context for intent. They are never labeled, never evaluated for correctness, and never added to the context array. If the body looks vague in isolation but is a clear answer to a question from the thread, treat it as clear.
- **Step 08 generates `to_report.md`** at the root of the task directory, but only when `work/thread.md` exists. Top-level tasks never get a `to_report.md`.
- **`/review` regenerates `to_report.md`** from the effective deliverables (fixed overlay on top of original) whenever `work/thread.md` exists. It also deletes any stray `to_report.md` that appears on a top-level task.
- **`to_report.md` layout:** a single-row markdown table with six columns in this order: Task Number, Summary, Workaround, Axis and Justification, Status, Other task with the same issue / case. The Status is always `done`. The Other task column is always empty, the user fills it manually. The Axis and Justification cell lists all four axes in order, concatenated with periods between sentences, no semicolons, no dashes, no colons outside file paths.
- **Wording rules apply everywhere.** The Axis and Justification cell, the Summary, and the Workaround are user-facing text. All ZERO-TOLERANCE rules from the Wording section apply.

If you are working on a task and you see `work/thread.md` in the task directory, read it before labeling. If you see `Comment Type: nested reply` in `task_info.md` but no `work/thread.md`, something went wrong in step 02. Flag it to the user rather than guessing.

## Comment references another comment (skip, release, flag)

The batch coordinator asked to skip, release, and flag any task whose body **explicitly references another comment** instead of reviewing code. The rule is narrow on purpose. A body that is just vague or low quality is NOT a skip case, that is a normal labeling job (usually `unhelpful`).

Example bodies that match: `@alice good catch`, `I agree with the suggestion above`, `see my earlier comment`, `replying to @bob, the other file is fine`, `as noted in the previous comment`. What they share is an explicit handle to another comment: an at-mention of a reviewer in a discussion sense, a pointer like "above" or "previous comment" or "earlier", or a quote of another comment, with no independent code observation of the body itself.

When the gate matches in step 02 section 2d:

- Step 02 stops immediately. The pipeline does NOT fetch the diff, does NOT clone the repo, and does NOT run steps 03-08. This saves the expensive work for a task that will never be labeled.
- `task_info.md` is stamped with `- **Comment Type:** references another comment (skip, release, flag)` and carries a `SKIP AND FLAG` note under the `## Status` heading.
- `skip_flag.md` is written at the root of the task directory with the reason. Its presence is the contract between the pipeline, the API, and the extension. Do not rename it, do not move it, do not delete it by hand.
- `progress.md` marks step 02 as `skipped` and steps 03-08 as `skipped` too. No deliverables are produced.
- The API returns `status: "skipped"` with the reason on `/run/status/{id}` and `/state/{id}`. The extension shows an amber skip-and-release banner so the attempter knows to act on the platform.

Detection rule. Read the body and, when present, `work/thread.md`. Apply TWO cumulative tests in this order:

1. **The body contains an explicit reference to another comment.** Look for at-mentions of a reviewer in a discussion sense (`@alice`), spatial or temporal pointers like `above`, `below`, `previous comment`, `earlier`, `before`, `as X said`, a quote of another comment's text, or a reply whose meaning collapses without the ancestor (nested `yes`/`no`/`agreed`/`thanks` ONLY qualifies if the thread ancestor made the reference unambiguous).
2. **The body, read on its own, adds no code observation about `file_path:diff_line`.** No claim about the code, no bug report, no concrete suggestion, no specific observation.

Skip ONLY when BOTH tests are true. If test 1 fails (no explicit reference to another comment), the task goes through the normal pipeline, even if the body is vague or low quality. If test 2 fails (the body says something substantive about the code), proceed normally too. The reference to another comment is just context.

When working on a task and you see `skip_flag.md` in the task directory, do not run any step. Relay the flag message to the user and stop. `/run` respects this as an idempotency signal so re-invocations of a flagged task never resume labeling.

## Comment not found in discussion (skip, release, flag)

If the comment cannot be located at `discussion_url`, the task cannot be labeled. The body that the platform pasted has no anchor on GitHub, which means the diff line, the surrounding context, and the thread are all unverifiable. Without that anchor every axis becomes guesswork.

Two sub-cases trigger this gate:

1. The GitHub API returns 404 for `gh api repos/{nwo}/pulls/comments/{comment_id}`. The comment ID points to nothing. Reasons range from a deleted comment to a wrong ID in the task package.
2. The API returns a body that does NOT match the `body` field from the task package. The pasted body and the live comment are different content, so we cannot tell which one is the target.

In either case the pipeline must skip the task and flag it. The mechanism reuses the same `skip_flag.md` contract used for comment-references-another-comment.

When the gate matches:

- The detecting step writes `skip_flag.md` at the task root with `**Reason:** Comment not found at discussion_url`.
- `task_info.md` Status section gets a `SKIP AND FLAG` note explaining whether the comment was missing or mismatched.
- `progress.md` marks remaining steps as `skipped`.
- The API returns `status: skipped` with the reason on `/run/status/{id}`.
- The extension shows the amber skip banner so the attempter releases the task on the platform.

When working on a task and you see `skip_flag.md` mentioning a missing or mismatched comment, do NOT relabel from memory or from the platform's pasted body alone. The contract is to release the task on the platform, not to fabricate evidence. The `body` field cannot be trusted in isolation because we have nothing to verify it against.

## Platform flags can be over-flagged

The annotation platform's validation rules are regex/heuristic based and can fire on legitimate text. Before editing a deliverable to satisfy a flag, VERIFY the flag is warranted by reading the actual text the validator matched against.

Examples of over-flag to watch for:
- A `no-line-numbers` rule that hits a substring inside a quoted code snippet, file path, or code identifier (e.g. `line-1` in a CSS class name) rather than a real coordinate in prose.
- A `no-axis-mixing` rule that hits a forbidden word used in a non-axis sense (e.g. "critical path" in a performance argument is not the severity axis).
- A validator reporting a failing row that is actually empty from a stale client state rather than a content problem.

If the flag looks like a false positive, tell the user in one short sentence ("looks like overflag: the match is inside a code quote") and wait for confirmation before editing. Only edit when the flag is clearly warranted.

## Wording Rules

These rules apply to ALL text output: reasoning fields, deliverable .md files, task_info.md, and any user-facing text.

**The `## Reasoning` section in each deliverable file is the justification the user pastes directly into the annotation platform. It must be self-contained, clear, and ready to copy-paste as-is.**

### ZERO TOLERANCE characters

The following characters MUST NEVER appear in any justification, reasoning, feedback, or explanation text. This is a hard rule, not a preference. Before writing any justification or feedback file, and again before saving it, scan the text and remove every instance of:

- Em-dash `—`
- En-dash `–`
- Hyphen `-` used as a sentence connector (hyphens are only allowed inside compound words like `focus-loss` or numeric ranges like `lines 83-120`, never as a substitute for a comma or em-dash)
- Semicolon `;`
- Colon `:` (except inside file paths like `src/foo.ts:42`)

If you catch yourself typing one of these to join clauses or introduce an aside, stop and rewrite as two separate sentences. After writing any feedback or reasoning, do a final pass searching for `—`, `–`, `;`, and stray `:` and rewrite those sentences before saving.

### Prohibited
- **Em-dashes** (`—`): split into two sentences or use commas instead
- **En-dashes** (`–`): use hyphens (`-`) for ranges (e.g., "lines 83-120")
- **Ellipsis character** (`…`): use three dots (`...`) if needed
- **Smart/curly quotes** (`""''`): use straight quotes (`""''`) only

### Punctuation that sounds machine-generated

Real people writing technical prose rarely lean on these. Avoid them by default and rewrite into plain sentences:

- **Parentheses** (`(...)`): do NOT wrap clarifications, asides, or examples in parentheses. If the parenthetical is important, promote it to its own sentence; if it is not important, drop it.
- **Semicolons** (`;`): do NOT join independent clauses with a semicolon. Use a period and start a new sentence.
- **Colons** (`:`): do NOT use a colon to introduce an explanation, list, or example inside a justification. Rewrite as a normal sentence.

These three are only allowed when they are **strictly necessary** for the claim itself, for example a colon inside a file path (`src/foo.ts:42`), parentheses inside a function signature being quoted from code (`fn(a, b)`), or a semicolon inside a code snippet. Outside of code-like fragments, do not use them.

### Preferred Style
- Plain, direct English. Keep technical vocabulary in the justifications, just write it as natural prose.
- Short sentences over long compound ones. When in doubt, split.
- Separate independent clauses with periods, not semicolons or em-dashes.
