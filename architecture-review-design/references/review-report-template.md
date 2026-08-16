# Architecture Review Report Template

Fill every section with real content. Do not keep placeholder text. Placeholders in `{curly braces}` must be replaced or removed.

```markdown
# Architecture Review Report: {project/scope}

- **Date:** {YYYY-MM-DD}
- **Scope:** {module / subsystem / whole repo}
- **Dimensions evaluated:** {list}
- **Dimensions skipped:** {list, with reason}

## 1. Overview (8-Dimension Radar)

| Dimension | Score (0-5) | One-line conclusion |
|---|---|---|
| 1. Functional Correctness | {n} | {one line} |
| 2. Portability | {n} | {one line} |
| 3. Maintainability / Extensibility | {n} | {one line} |
| 4. Observability | {n} | {one line} |
| 5. Testability | {n} | {one line} |
| 6. Usability / Onboarding | {n} | {one line} |
| 7. Performance / Scalability | {n} | {one line} |
| 8. Security | {n} | {one line} |
| **Average** | **{avg}** | **{overall verdict in one sentence}** |

> Scoring rule: every score is backed by evidence in section 2. No evidence → "not evaluated".

## 2. Per-Dimension Details

### Dimension {n}: {name} — Score {x}/5

**Evidence:**
- {file path}:{line} — {concrete observation or snippet}
- {file path}:{line} — {concrete observation or snippet}

**Issues found:**
- 🔴 {description} ({location})
- 🟡 {description} ({location})
- ⚪ {description} ({location})

**Strengths (optional):**
- {what is done well}

---

(repeat for every evaluated dimension)

## 3. Remediation Roadmap

Ordered by priority (🔴 first), each with an effort estimate.

| # | Priority | Issue | Dimension | Effort (low/med/high) | Suggested fix |
|---|---|---|---|---|---|
| 1 | 🔴 | {issue summary} | {dimension} | {effort} | {fix in one line} |
| 2 | 🟡 | {issue summary} | {dimension} | {effort} | {fix in one line} |
| 3 | ⚪ | {issue summary} | {dimension} | {effort} | {fix in one line} |

**Suggested order of execution:** {1-2-3 reasoning — what unblocks what}

## 4. Quick Wins (do this week)

- {low-cost fixes with big impact}
```
