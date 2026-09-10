---
name: architecture-review-design
description: Use when the user asks for architecture review ("架构评审", "评审架构", "架构体检", "帮我看看这个架构", "帮我评估一下这个系统", "architecture review", "assess this architecture"), architecture design ("架构设计", "设计架构", "帮我设计系统架构", "怎么设计这个系统", "architecture design", "design the system architecture"), or wants an existing system's architecture documented ("梳理这个系统的架构", "还原架构文档", "architecture documentation"). Reviews existing codebases against 8 quality dimensions (functional correctness, portability, maintainability/extensibility, observability, testability, usability, performance/scalability, security) with conversational deep-dive plus a scored report, and designs new architectures with five mandatory Mermaid views (system context, component, layered, runtime, data flow) plus trigger-based views (deployment, state machine, data model; a cross-functional swimlane view is produced on request only), module responsibility lists, interface definitions, ADR records, 8-dimension self-check and an evolution roadmap. Every deliverable is a complete architecture document in the user's chosen language (中文 or English), produced as a single-file HTML report with zoomable diagrams and an optional .md source.
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

Review mode is conversational first and produces a scored report **plus the As-Is architecture document**; design mode is requirement-driven and produces the To-Be architecture document. Both modes share the same dimension definitions, the same architecture-view catalogue, and the same single-file HTML deliverable format.

## When to Use

| Scenario | Example trigger phrases |
|------|-----------|
| Reviewing an existing codebase | "架构评审", "评审一下这个项目的架构", "架构体检", "帮我看看这个架构" |
| Designing a new system | "架构设计", "帮我设计系统架构", "帮我设计一个 xxx 系统" |
| Reviewing a design proposal | "这个设计方案靠谱吗", "帮我评估一下这份设计" |
| Documenting an existing system (no scoring) | "帮我梳理这个系统的架构", "还原一份架构文档" (see the documentation-only variant of Workflow A) |

Do NOT use for: pure business questions, single-function changes, or code review at the file level (see Boundary Rules).

## Step 0 — Output Language (ask before doing anything else)

Ask once, at the very start, with a compact question:

> "文档用什么语言？中文 / English（将统一用于正文、图表标签、表格与 HTML 菜单）"

Rules:

- **One language for the whole deliverable**: conversation digest, document body, headings, table headers, meta chips, Mermaid node labels/lane names/edge labels, figure captions, and the HTML menu chrome. A Chinese document with English menus (or the reverse) is a failed artifact — this is verified in the acceptance checklist.
- The answer also selects the template outline (`design-doc-template.md` §A English / §B 中文) and the generator flag (`md2html.py --lang`).
- The answer governs the conversational output too: discuss findings in the chosen language.
- If the user switches language later, re-author the document — do not translate half of it in place.
- If the user has already stated a language preference, confirm it in one line instead of re-asking.

## Shared Foundation (read before either workflow)

Before starting any review or design, read:

1. **`references/8-dimensions.md`** — the authoritative definition of the 8 dimensions: core question, evaluation question sets, evidence checkpoints, common anti-patterns, remediation advice, and the 0-5 scoring rules.
2. **`references/mermaid-spec.md`** — the view catalogue: five mandatory views (system context / component / layered / runtime / data flow) plus trigger-based views (deployment / state machine / data model) and one on-request view (swimlane, §3.4), each with its own rules, and the hard consistency rules (§8). Required whenever any architecture diagram is produced, together with **`references/html/check_views.py`**, the runnable gate for those rules.
3. **`references/html/html-output-spec.md`** — HTML output spec (read only when producing/saving HTML): language & UI chrome (§3), component class registry and heading mapping (§5), zoom/fullscreen figure rules (§8), token rules for the handwritten tier (§10), acceptance checklist (§11).

When producing HTML you must also use `references/html/report-shell.html` (skeleton, bilingual UI, figure zoom built in) and `references/html/md2html.py` (generator, pure stdlib) shipped with the skill.

Do NOT re-derive dimension definitions from memory — always work from the reference file. Do NOT hand-roll a diagram set: the view catalogue is part of the deliverable contract, and `check_views.py` enforces it.

## Workflow A: Architecture Review

### Step 1 — Recon

Scan the project: directory structure, README, config files, dependency manifests, and the main source layout. For large projects, ask the user to scope the review boundary first (one line, one module, or a specific subsystem). Do not default to scanning the entire repo.

Recon output feeds **both** the scores and the As-Is architecture views in Step 4 — record which paths prove the structure (entry points, module boundaries, storage config, call chains).

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

### Step 4 — Scored Report + As-Is Architecture

The deliverable is **the architecture document as it exists today, plus the evaluation** — not just a score sheet. Build it per `references/review-report-template.md` (either language outline):

1. **Overview** — 8-dimension radar table (score 0-5 + one-line conclusion each; feeds the radar chart)
2. **System Architecture (As-Is)** — the **five mandatory views** per `mermaid-spec.md` §1 (system context, component, layered, runtime with a failure branch, data flow) plus every conditional view whose trigger holds (deployment, state machine, data model). Each figure carries a one-line "read this for" note **and its recon evidence** (which paths the structure was read from). Merging the layered view into the component view requires an explicit "merged because…" line; a mandatory view that cannot be drawn keeps its heading plus one line `Not applicable because …`. When a view exposes a defect, the text next to it must name the defect — otherwise the drawing reads like the intended design.
3. **Per-Dimension Details** — score, evidence (file paths / line numbers / code snippets), issue list with priorities
4. **Remediation Roadmap** — ordered 🔴 → 🟡 → ⚪, each item with an effort estimate (low/medium/high)
5. **Quick Wins** — low-cost, high-impact fixes

**Scoring rules (hard requirements):**

- Every score must be backed by evidence (file path + line number or a concrete observation). No evidence → no score; write "not evaluated" instead of guessing.
- Score only dimensions the user selected; unselected ones are marked "skipped".
- The views must agree with each other and with the module list (same node sets, same dependencies, externals defined once in the context view — per `mermaid-spec.md` §8), and `python check_views.py <draft.md>` must pass.
- Then follow the "Deliverable Workflow" below; suggested save path `docs/review/YYYY-MM-DD-<scope>-architecture-review.html`.

### Documentation-only variant (no scoring)

If the user only wants the system's architecture written down — "帮我梳理这个系统的架构", "还原一份架构文档", "document this system's architecture" — do not force them through the 8-dimension deep dive:

1. Run Step 1 (recon) as usual and record the evidence paths.
2. Skip Steps 2 and 3.
3. Produce, from `references/review-report-template.md` (the outline matching the language): section **2. System Architecture (As-Is)** with all five mandatory views (plus the conditional ones whose triggers hold), a module list (roles and dependencies read from the code), interface definitions where they are discoverable, ADR-style notes only for decisions you can defend from the repository, and a short risk list. **Drop section 1 (the score table) entirely** — never invent scores for a run that did not evaluate. (An all-"not evaluated" table would draw no radar, since the page needs at least three numeric scores, but it is dead weight in the document.)
4. Say plainly in the digest that this run documents the As-Is architecture **without** scoring.
5. Deliver through the shared Deliverable Workflow; suggested save path `docs/architecture/YYYY-MM-DD-<scope>-architecture.html`.

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

Generate per `references/design-doc-template.md` (the outline matching the chosen language), which contains:

1. **Background & Goals** and 2. **Requirements** — problem, goals, non-goals, verified requirements
3. **Architecture Views** — the **five mandatory views** per `mermaid-spec.md` §1: system context (boundary and external parties), component (parts, stores, dependencies), layered (must arrange the same node set, with layer responsibilities and allowed dependency direction), runtime (`sequenceDiagram` for the primary flow **including a failure branch**), data flow (data-labeled edges, stores, trust boundaries). Add every conditional view whose trigger holds: deployment, state machine, data model. (A cross-functional swimlane view is on request only — mermaid-spec.md §3.4; skip it unless it shows manual steps the other views cannot.) Each figure carries a one-line "read this for" note; merging the layered view into the component view requires an explicit note.
4. **Module List & Responsibilities** — each module answers: what it does / how to use it / what it depends on
5. **Interface Definitions** (module-level functions / APIs / events / data contracts)
6. **ADR Records** — every key decision: alternatives, chosen option, reason, cost
7. **8-Dimension Self-Check** — how the design satisfies each dimension; unfulfilled items are explicitly marked as risks
8. **Evolution Roadmap** — MVP first, then staged growth; avoid big-bang design

Once finalized: first present a **structured summary** in the conversation (title, goals/non-goals, the recommended approach in one line, the views drawn by name, module and ADR lists, self-check risk items, roadmap stages), then follow the "Deliverable Workflow" below; suggested save path `docs/design/YYYY-MM-DD-<system>-architecture-design.html`. Do not dump the full document in Markdown unless the user asks for it — the full document is the artifact.

## Deliverable Workflow (shared by Workflows A/B Step 4)

The deliverable **is** the architecture document: a single-file HTML, with the `.md` source offered as an optional companion.

1. **Author the complete document** as a `.md` draft in the chosen language, using the matching template outline (all sections; the mandatory views plus every triggered conditional view, with real content — never a summary). Then run the view gate: `python <skill references/html path>/check_views.py <draft.md>` and fix the diagrams until it passes.
2. **Show a short structured digest in the conversation** (headings + key conclusions), not the full text.
3. **Ask once**, in the document language:
   > "保存为 HTML 文件吗？同时保留 .md 源稿吗？保存到哪里？"
   Never save without asking. If the Step 0 language was never settled (e.g. the conversation resumed later), ask it here — **before** generating — and pass an explicit `--lang`.
4. **Generate the HTML:**
   - Probe interpreters in order: `py -3` / `python3` / `python` (`py -3` first on Windows). If one is available → **Tier 1**:
     - Place the draft next to the output directory and run:
       `python <skill references/html path>/md2html.py <draft.md> <out.html> --lang <en|zh>` (locate the skill path by globbing upward from the current project: `**/references/html/md2html.py`)
     - `--lang` must match the language chosen in Step 0; it localizes the HTML menu **and** the figure captions, so the menu can never disagree with the body
     - If the user wants the `.md` source kept, place/keep the draft at the final `.md` path next to the HTML (same basename) and run with `--keep-src`; otherwise the draft is deleted after a successful conversion
     - Verify the output exists, contains `data-lang="<lang>"`, and has no `<!--T:` tokens left
   - No interpreter available → **Tier 2**: copy `references/html/report-shell.html` as the output file, set `<html lang="…" data-lang="…">`, and fill in the tokens per `html-output-spec.md` §10 (title / meta / body); remove `<!--T:EXTRA-->`
5. **Self-check** against the `html-output-spec.md` §11 checklist — especially: one language throughout (including the menu), the view catalogue complete with `check_views.py` passing, figures zoom, no leftover tokens.
6. Report the saved paths (HTML, and the `.md` when kept).

## Output Rules

- The **complete deliverable for review reports and design documents is a single-file HTML architecture document** (self-contained, double-click to open, menu in the document language, zoomable diagrams); the conversation shows only a structured summary.
- The `.md` source is an **optional first-class output**, not merely an intermediate: when the user wants it, it is saved next to the HTML with the same basename.
- HTML artifacts follow `references/html/html-output-spec.md`; every content Mermaid diagram follows `references/mermaid-spec.md` (the view catalogue, the `.arch` triplet with embedded source + CDN client-side rendering) and passes `check_views.py`.
- Generation is dual-track: with Python available → render via `md2html.py --lang`; without Python → hand-write against the `report-shell.html` skeleton (setting `data-lang`). Both tracks produce spec-conformant artifacts.
- Ask only once at the end of each run: "Save as an HTML file? Keep the .md source too?" — never save without asking.

## Boundary Rules

- Large projects: always scope the review/design boundary first; never assume the whole repository.
- If the user asks to "design" for a system that already has code: suggest running the review workflow first, or review the existing code as part of design input.
- If the request is a pure business question or a single-function change: state clearly that this skill does not apply, and answer directly instead.
- If the user requests an architecture diagram outside review/design, the mermaid-spec still governs diagram quality.
- If the user only wants a diagram or only wants the report re-rendered in the other language, do that specific job — no need to rerun the whole workflow (re-rendering means re-authoring content in the target language, never a mixed-language patch).

## Self-Check After Each Run

- [ ] The document language was asked (or confirmed) first, and **everything** — body, headings, table headers, meta chips, diagram labels, captions, HTML menu — is in that one language
- [ ] Every score in a review report has evidence; no invented observations
- [ ] All five mandatory views are present in both modes plus every triggered conditional view (or the merge / not-applicable line is written), each with a one-line "read this for" note, agreeing with the module list, and `check_views.py` passes
- [ ] Every content Mermaid diagram conforms to mermaid-spec (≤15 nodes, one colour palette, consistent naming, ASCII node IDs, localized labels, data-labeled DFD/swimlane edges)
- [ ] Design documents include all 8 template sections (or explicitly marked as intentionally omitted)
- [ ] Saved artifacts are .html and pass the html-output-spec §11 checklist (opens on double-click, `data-lang` set, theme toggle works, diagrams render or degrade gracefully, zoom/pan/fullscreen work, no `<!--T:` leftover tokens, no `{}` placeholders); the user was asked before saving
- [ ] Issue grades use 🔴/🟡/⚪ consistently
