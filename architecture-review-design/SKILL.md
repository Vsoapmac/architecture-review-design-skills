---
name: architecture-review-design
description: Use when the user asks for architecture review ("架构评审", "评审架构", "架构体检", "帮我看看这个架构", "帮我评估一下这个系统", "architecture review", "assess this architecture") or architecture design ("架构设计", "设计架构", "帮我设计系统架构", "怎么设计这个系统", "architecture design", "design the system architecture"). Reviews existing codebases against 8 quality dimensions (functional correctness, portability, maintainability/extensibility, observability, testability, usability, performance/scalability, security) with conversational deep-dive plus a scored report, and designs new architectures with Mermaid diagrams, module responsibility lists, interface definitions, ADR records, 8-dimension self-check, and an evolution roadmap.
---

# Architecture Review & Design

## Overview

A dual-mode skill covering both **reviewing existing architecture** and **designing new architecture**, built on a shared 8-dimension quality framework:

1. **Functional Correctness** — can vague requirements be precisely implemented?
2. **Portability** — how much code changes when switching platforms/environments?
3. **Maintainability / Extensibility** — how many files change for a new business feature?
4. **Observability** — how fast can a 3 AM issue be located?
5. **Testability** — how easy is it to test modules in isolation?
6. **Usability (Onboarding)** — can a newcomer run the core flow within 10 minutes?
7. **Performance / Scalability** — does the architecture hold up at 10x data/concurrency?
8. **Security** — how large is the blast radius of a breach or attack?

Review mode is conversational first and produces a scored report; design mode is requirement-driven and produces a complete design document. Both modes share the same dimension definitions and Mermaid diagram spec.

## When to Use

| Scenario | Example trigger phrases |
|------|-----------|
| Reviewing an existing codebase | "架构评审", "评审一下这个项目的架构", "架构体检", "帮我看看这个架构" |
| Designing a new system | "架构设计", "帮我设计系统架构", "帮我设计一个 xxx 系统" |
| Reviewing a design proposal | "这个设计方案靠谱吗", "帮我评估一下这份设计" |

Do NOT use for: pure business questions, single-function changes, or code review at the file level (see Boundary Rules).

## Shared Foundation (read before either workflow)

Before starting any review or design, read:

1. **`references/8-dimensions.md`** — the authoritative definition of the 8 dimensions: core question, evaluation question sets, evidence checkpoints, common anti-patterns, remediation advice, and the 0-5 scoring rules.
2. **`references/mermaid-spec.md`** — diagram type selection, naming, layering colors, node limits, and consistency rules. Required whenever any architecture diagram is produced.
3. **`references/html/html-output-spec.md`** — HTML output spec (read only when producing/saving HTML): component class registry, .md draft mapping table, both-tier authoring rules, acceptance checklist.

When producing HTML you must also use `references/html/report-shell.html` (skeleton) and `references/html/md2html.py` (generator, pure stdlib) shipped with the skill.

Do NOT re-derive dimension definitions from memory — always work from the reference file.

## Workflow A: Architecture Review

### Step 1 — Recon

Scan the project: directory structure, README, config files, dependency manifests, and the main source layout. For large projects, ask the user to scope the review boundary first (one line, one module, or a specific subsystem). Do not default to scanning the entire repo.

### Step 2 — Dimension Triage

Ask the user which dimensions matter most. Default is all 8, but allow trimming — e.g., a small CLI tool can skip Performance/Scalability. Confirm the final dimension list before deep-diving.

### Step 3 — Conversational Deep-Dive (one dimension at a time)

For each selected dimension:

1. Start with the user's own sense: "For dimension X, do you feel there are any hidden risks?" — gather their perspective first.
2. Then examine code/documentation for evidence using the dimension's checkpoints from `8-dimensions.md`.
3. Discuss findings one at a time. Grade each issue:
   - 🔴 **Must fix** — blocks correctness, security, or future development
   - 🟡 **Should fix** — noticeable pain, low-to-medium cost
   - ⚪ **Worth knowing** — informational, optional
4. Move to the next dimension only after the current one is discussed. Do not dump all findings at once.

### Step 4 — Scored Report

After all dimensions are discussed, summarize into the report template `references/review-report-template.md`:

- 8-dimension radar overview table (score 0-5 + one-line conclusion each)
- Per-dimension details: score, evidence (file paths / line numbers / code snippets), issue list with priorities
- Remediation roadmap ordered 🔴 → 🟡 → ⚪, each item with an effort estimate (low/medium/high)

**Scoring rules (hard requirements):**

- Every score must be backed by evidence (file path + line number or a concrete observation). No evidence → no score; write "not evaluated" instead of guessing.
- Score only dimensions the user selected; unselected ones are marked "skipped".
- After presenting the report, handle it via the "HTML save workflow" below; suggested save path `docs/review/YYYY-MM-DD-<scope>-architecture-review.html`.

**HTML save workflow (shared by Workflows A/B Step 4):**

1. Probe interpreters in order: `py -3` / `python3` / `python` (`py -3` first on Windows). If one is available → **Tier 1**:
   - Assemble the summary into a temporary .md draft (section headings matching the corresponding template, per the `html-output-spec.md` §4 mapping), placed next to the output directory
   - Run: `python <skill references/html path>/md2html.py <draft.md> <out.html>` (locate the skill path by globbing upward from the current project: `**/references/html/md2html.py`)
   - After a successful conversion the draft is deleted by default; verify the output exists and contains no `<!--T:` tokens
2. No interpreter available → **Tier 2**: copy `references/html/report-shell.html` as the output file, fill in the tokens per `html-output-spec.md` §7 (title / meta / body), remove `<!--T:EXTRA-->`
3. In both tiers, self-check against the `html-output-spec.md` §8 checklist
4. Ask only once at the end: "Save as an HTML file? Keep the .md draft too?" (Tier 1: rerun with `--keep-src` if the user wants to keep the draft)

## Workflow B: Architecture Design

### Step 1 — Requirements Clarification

List what is known, then confirm ambiguous points one by one (this is dimension 1 — functional correctness, applied at design time). **Do not draw architecture diagrams before requirements are clarified.** Ask about: core business flows, users/actors, expected outputs, and any known future requirements.

### Step 2 — Constraints Confirmation

Ask once, as a compact list (these directly shape the architecture):

| Constraint | Related dimension |
|------|-----------|
| Target environment/platform (self-hosted / cloud / desktop / embedded) | Portability |
| Estimated data volume and concurrency (now and 1-year horizon) | Performance/Scalability |
| Security requirements (sensitive data, compliance, auth model) | Security |
| Team size and maintenance capability | Maintainability, Usability |
| Existing systems to integrate with | Maintainability |

### Step 3 — Tradeoff Options

Propose 2-3 candidate architecture approaches (e.g., monolith / layered / modular / event-driven / microservices — choose what actually fits the scale). Compare them in a table across the 8 dimensions, state your recommendation and why. Let the user pick or adjust before producing the final document.

### Step 4 — Design Document

Generate per `references/design-doc-template.md`:

1. Overview + Mermaid architecture diagram (component/flowchart per `mermaid-spec.md`)
2. Module list with responsibilities — each module answers: what it does / how to use it / what it depends on
3. Interface definitions (module-level functions / APIs / events)
4. ADR records — every key decision: alternatives, chosen option, reason, cost
5. 8-dimension self-check table — how the design satisfies each dimension; unfulfilled items are explicitly marked as risks
6. Evolution roadmap — MVP first, then staged growth; avoid big-bang design

Once finalized: first present a **structured summary** in the conversation (title, goals/non-goals, the recommended approach in one line, module and ADR lists, self-check risk items, roadmap stages), then handle saving via the "HTML save workflow" above; suggested save path `docs/design/YYYY-MM-DD-<system>-architecture-design.html`. Do not dump the full document in Markdown unless the user asks for it.

## Output Rules

- The **complete deliverable for review reports and design documents is a single-file HTML** (self-contained, double-click to open); the conversation shows only a structured summary.
- HTML artifacts follow `references/html/html-output-spec.md`; every content Mermaid diagram follows `references/mermaid-spec.md` (the `.arch` trio with embedded source + CDN client-side rendering).
- Generation is dual-track: with Python available → render via `md2html.py`; without Python → hand-write against the `report-shell.html` skeleton. Both tracks produce spec-conformant artifacts.
- Ask only once at the end of each run: "Save as an HTML file? Keep the .md draft too?" — never save without asking.

## Boundary Rules

- Large projects: always scope the review/design boundary first; never assume the whole repository.
- If the user asks to "design" for a system that already has code: suggest running the review workflow first, or review the existing code as part of design input.
- If the request is a pure business question or a single-function change: state clearly that this skill does not apply, and answer directly instead.
- If the user requests an architecture diagram outside review/design, the mermaid-spec still governs diagram quality.

## Self-Check After Each Run

- [ ] Every score in a review report has evidence; no invented observations
- [ ] Every content Mermaid diagram conforms to mermaid-spec (≤15 nodes, layered colors, consistent naming)
- [ ] Design documents include all 8 sections of the template (or explicitly marked as intentionally omitted)
- [ ] Saved artifacts are .html and pass the html-output-spec §8 checklist (opens on double-click, theme toggle works, diagrams render or degrade gracefully, no `<!--T:` leftover tokens, no `{}` placeholders); the user was asked before saving
- [ ] Issue grades use 🔴/🟡/⚪ consistently
