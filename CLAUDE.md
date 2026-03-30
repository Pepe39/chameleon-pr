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
- **Em-dashes** (`—`): Use commas, semicolons, parentheses, or split into two sentences instead
- **En-dashes** (`–`): Use hyphens (`-`) for ranges (e.g., "lines 83-120")
- **Ellipsis character** (`…`): Use three dots (`...`) if needed
- **Smart/curly quotes** (`""''`): Use straight quotes (`""''`) only

### Preferred Style
- Write in plain, direct English
- Prefer short sentences over long compound ones
- Use semicolons or periods to separate independent clauses, not dashes
