# Axis 2: Severity

Assess how severe the **issue itself** is that the review comment points out. Severity measures the issue, NOT the quality of the comment.

---

## Possible Values

| Value | Impact | Definition |
|---|---|---|
| **nit** | Low — safe to defer | Minor issues that can be safely ignored or deferred. They pose no meaningful risk and do not affect the code's behavior. E.g.: style nit-picks, naming preferences, cosmetic suggestions, documentation gaps, minor code smell. |
| **moderate** | Medium — should improve | Issues that affect or could affect the code's behavior but are unlikely to cause serious harm. The code works but should be improved. E.g.: missing edge case handling on uncommon paths, suboptimal but functional logic. |
| **critical** | High — must fix before merge | Severe issues with significant and concrete risk to correctness, security, or stability. A senior engineer would insist on fixing this before merging. E.g.: SQL injection, authentication bypass, data corruption, race conditions. |

---

## How to Evaluate

1. **Focus on the issue itself**, not how the comment is worded. A well-written comment about a trivial style preference is still `nit`.
2. If the comment flags **multiple issues**, rate by the **most severe** one.
3. **Quick test:** "Would a senior engineer insist this be fixed before merging?" If yes -> `critical`.

### Key Rules

- Severity is independent of Quality. A `wrong` comment about a SQL injection is `wrong + critical`.
- The same code pattern can have different severities depending on context (see example).
- Do not let the comment's urgent tone ("MUST fix!") inflate the severity.

---

## Example

**Same pattern, different severity:**

| Comment | Context | Severity |
|---|---|---|
| "Missing null check on `user.preferences` before accessing `.theme`." | `preferences` is always populated by the ORM during user creation. It has never been null in production. | **nit** |
| "Missing null check on `user.session` before accessing `.token`." | `session` is null for unauthenticated users, and this endpoint is reachable without login. Causes a 500 error on every anonymous request. | **critical** |

Both comments say "missing null check" — the severity depends on the likelihood and impact of the null case, not the wording of the comment.
