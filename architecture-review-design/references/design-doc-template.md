# Architecture Design Document Template

Fill every section with real content. Do not keep placeholder text. Placeholders in `{curly braces}` must be replaced or removed. All diagrams follow `mermaid-spec.md`.
> **This template has two duties:** ① the section outline for the conversational digest; ② the outline for Tier 1's .md draft (md2html.py maps each h2 heading to components — see `html/html-output-spec.md` §4). **If you change an h2 heading, update the mapping table in html-output-spec.md.**

```markdown
# Architecture Design: {system name}

- **Date:** {YYYY-MM-DD}
- **Author:** {who}
- **Status:** Draft / Approved

## 1. Background & Goals

- **Problem statement:** {what problem this system solves, 2-3 sentences}
- **Goals:** {numbered list of must-achieve outcomes}
- **Non-goals:** {explicitly out of scope — prevents scope creep}

## 2. Requirements (verified with stakeholders)

- **Functional:** {the confirmed core flows, each with acceptance criteria}
  - {flow 1}: {criteria}
  - {flow 2}: {criteria}
- **Constraints:** {target platform, data volume/concurrency estimates, security requirements, team size}
- **Assumptions:** {things assumed true, so they can be revisited}

## 3. Architecture Overview

{Mermaid component diagram per mermaid-spec.md — layers: entry / service / data / external}

### Key flow: {core scenario 1}
{Mermaid sequenceDiagram for the most important runtime path}

### Key flow: {core scenario 2}
{Mermaid sequenceDiagram for the second most important path (if any)}

## 4. Module List & Responsibilities

Each module answers: what it does / how to use it / what it depends on.

| Module | Responsibility | Public entry (how to use) | Depends on |
|---|---|---|---|
| {module name} | {what it does} | {API/functions/events} | {modules it depends on} |
| ... | | | |

## 5. Interface Definitions

### Module-level APIs
- `{module}.{function}({params}) -> {returns}` — {one-line semantics, error behavior}

### Events / Messages (if any)
- `{event name}` — {publisher} → {subscribers}, payload `{shape}`, delivery guarantee `{at-least-once/exactly-once/best-effort}`

### Data contracts (if applicable)
- {entity}: {key fields, constraints} — owned by {module}

## 6. ADR Records

Format: one block per decision. Order by decision date.

### ADR-{n}: {Decision title}

- **Date:** {YYYY-MM-DD}
- **Status:** Accepted / Superseded by ADR-{m}
- **Context:** {the problem this decision addresses}
- **Alternatives considered:** {option A — pros/cons; option B — pros/cons}
- **Decision:** {chosen option}
- **Rationale:** {why this option wins}
- **Consequences / cost:** {what this decision costs or requires later}

## 7. 8-Dimension Self-Check

How the design satisfies each dimension. Unfulfilled items are risks, not omissions.

| Dimension | How the design addresses it | Status |
|---|---|---|
| 1. Functional Correctness | {requirements → module mapping, acceptance criteria coverage} | ✅ / ⚠️ risk |
| 2. Portability | {config externalization, environment assumptions} | ✅ / ⚠️ risk |
| 3. Maintainability / Extensibility | {module boundaries, expected file-change scope for a new feature} | ✅ / ⚠️ risk |
| 4. Observability | {logs/traces/metrics/alerting for this design} | ✅ / ⚠️ risk |
| 5. Testability | {dependency injection, test strategy per module} | ✅ / ⚠️ risk |
| 6. Usability / Onboarding | {setup story, docs, sample data plan} | ✅ / ⚠️ risk |
| 7. Performance / Scalability | {capacity estimates, bottleneck analysis at 10x} | ✅ / ⚠️ risk |
| 8. Security | {input validation, secrets, least privilege, blast radius} | ✅ / ⚠️ risk |

**Known risks to track:** {any ⚠️ items, expanded in one line each}

## 8. Evolution Roadmap

Stage-based, MVP first. Each stage is independently valuable.

| Stage | Scope | Exit criteria |
|---|---|---|
| MVP | {smallest useful vertical slice} | {what must work} |
| Stage 2 | {next increment} | {what must work} |
| Stage 3 | {later growth} | {what must work} |

**Explicitly postponed:** {things intentionally not in this design, with the trigger condition to revisit}
```
