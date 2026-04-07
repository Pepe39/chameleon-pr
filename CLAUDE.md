# Project Instructions

## Task Isolation Rule

During task execution (steps 01-08), focus exclusively on the task at hand: the PR, the diff, the comment, and the labeling. Do NOT:
- Modify project documentation, guides, commands, or templates
- Refactor or improve the labeling pipeline itself
- Update CLAUDE.md, DOCUMENTATION.md, axis docs, or step commands
- Fix issues found in guides or commands mid-task

If you notice a problem with the guides or pipeline during a task, finish the task first, then report the issue to the user. Meta-work (improving docs, fixing commands, adding features to the pipeline) must be requested explicitly by the user outside of task execution.

## Wording Rules

These rules apply to ALL text output: reasoning fields, deliverable .md files, task_info.md, and any user-facing text.

**The `## Reasoning` section in each deliverable file is the justification the user pastes directly into the annotation platform. It must be self-contained, clear, and ready to copy-paste as-is.**

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
