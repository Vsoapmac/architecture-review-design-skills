# Architecture Design Document Template

Fill every section with real content. Do not keep placeholder text. Placeholders in `{curly braces}` must be replaced or removed. All diagrams follow `mermaid-spec.md`.

> **Rules for this template**
> 1. **Pick ONE outline below (A = English, B = 中文) and use it for the whole document.** Never mix languages: headings, body, table headers, meta chips, diagram labels, captions and the HTML menu must all be in the same language. The language is confirmed with the user before authoring (see SKILL.md "Step 0").
> 2. **Two duties:** ① the section outline for the conversational digest; ② the outline for the .md draft that `md2html.py` renders into the HTML deliverable (each h2 maps to a component — see `html/html-output-spec.md` §5). **If you change an h2 heading, update the mapping table in html-output-spec.md and the role keys in md2html.py.**
> 3. **The five mandatory views in section 3 must all be present** — system context, component, layered, runtime, data flow (mermaid-spec.md §1) — and every conditional view whose trigger holds must be drawn. Merging the layered view into the component view is allowed only with an explicit "merged because…" line; a mandatory view that truly cannot be drawn keeps its heading plus one line `Not applicable because …`. Run `python check_views.py <draft.md>` before delivering: it fails on a missing view, a node set that differs between the component and layered views, an unlabeled data-flow/swimlane edge, an unused store, or a runtime view without a failure branch.

## A. Section outline — English

```markdown
# Architecture Design: {system name}

- **Date:** {YYYY-MM-DD}
- **Author:** {who}
- **Status:** Draft / Approved
- **Language:** English

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

## 3. Architecture Views

The **five mandatory views are 3.1-3.5**; keep a conditional view (3.6-3.8) only when its trigger holds. Each figure is followed by a one-line "read this for" note, and all diagrams share one colour vocabulary (mermaid-spec.md §6). Edge direction convention: component/layered edges are dependencies, runtime edges are time, data-flow edges are data movement (mermaid-spec.md §8).

### 3.1 System Context
{Read this for: the system boundary and what crosses it.}
{Mermaid flowchart LR: one system box + `Ext:` nodes — mermaid-spec.md §2.1}
{State each external party's failure impact in one line}

### 3.2 Component View
{Read this for: which parts exist, which are stores, and who depends on whom.}
{Mermaid flowchart LR with entry/service/data/external — mermaid-spec.md §2.2}
{The node set must equal the module list in section 4}

### 3.3 Layered View
{Read this for: which layer owns what, and whether the dependency direction is legal.}
{Mermaid flowchart TB, one subgraph per layer, externals in an external band — mermaid-spec.md §2.3}
{Same node set as 3.2; draw real violations dashed and list them in the table}
{Layer table: layer → responsibility → allowed dependencies}

### 3.4 Runtime View: {key flow}
{Read this for: the order of interactions, what is asynchronous, and what happens on failure.}
{Mermaid sequenceDiagram for the most important runtime path, with at least one alt/else failure branch — mermaid-spec.md §2.4}
{Sync/async and compensation per hop, in one line each}

### 3.5 Data Flow View
{Read this for: where data comes from, what transforms it, where it is stored, and which boundary it crosses.}
{Mermaid flowchart LR with data-labeled edges and trust boundaries — mermaid-spec.md §2.5}
{Data ownership and retention per store, in one line each}

### 3.6 Deployment View — conditional: more than one node, zone or environment
{Read this for: what runs where and which zones talk to each other.}
{Mermaid flowchart LR with environment subgraphs and protocol labels — mermaid-spec.md §3.1}

### 3.7 State Machine — conditional: a core entity has ≥4 states or state-dependent rules
{Read this for: the lifecycle of the core entity, in business terms.}
{Mermaid stateDiagram-v2 with event-labelled transitions — mermaid-spec.md §3.2}

### 3.8 Data Model — conditional: the data model is the main coupling point
{Read this for: which entities more than one module touches, and who owns each of them.}
{Mermaid erDiagram with the key fields only — mermaid-spec.md §3.3}

{On request only: a cross-functional swimlane view is NOT part of the catalogue. Draw it only if the user asks, following mermaid-spec.md §3.4 — and only when it shows something the other views cannot (manual steps, off-system workarounds, cross-team responsibility). If it would just re-state the runtime view, say so and skip it.}

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

## B. 章节大纲 — 中文

```markdown
# 架构设计文档：{系统名称}

- **日期：** {YYYY-MM-DD}
- **作者：** {姓名/角色}
- **状态：** 草稿 / 已评审通过
- **语言：** 中文

## 1. 背景与目标

- **问题陈述：** {这个系统解决什么问题，2-3 句话}
- **目标：** {必须达成的结果，编号列表}
- **非目标：** {明确不做的范围，防止范围蔓延}

## 2. 需求（已与干系人确认）

- **功能需求：** {已确认的核心流程，每条附验收标准}
  - {流程 1}：{验收标准}
  - {流程 2}：{验收标准}
- **约束条件：** {目标平台、数据量与并发预估、安全要求、团队规模}
- **假设前提：** {假定成立的条件，便于日后回看}

## 3. 架构视图

**五类必需视图为 3.1-3.5**；条件视图（3.6-3.8）只在触发条件成立时保留。每张图后必须写一句"看图重点"，所有图共用一套配色（mermaid-spec.md §6）。边的方向约定：组件图/分层图表示依赖，运行时图表示时间顺序，数据流图表示数据流动（mermaid-spec.md §8）。

### 3.1 系统上下文
{看图重点：系统边界在哪、什么东西穿过边界。}
{Mermaid flowchart LR：一个系统框 + `Ext:` 节点 —— mermaid-spec.md §2.1}
{逐个外部参与方说明故障影响，各一句话}

### 3.2 组件视图（架构图）
{看图重点：系统由哪些部件组成、哪些是存储、谁依赖谁。}
{Mermaid flowchart LR，entry/service/data/external 四色 —— mermaid-spec.md §2.2}
{节点集合必须与第 4 节模块清单一致}

### 3.3 分层视图（分层图）
{看图重点：每一层放什么职责、依赖方向是否合法。}
{Mermaid flowchart TB，每层一个 subgraph，外部节点放"外部"带 —— mermaid-spec.md §2.3}
{节点集合与 3.2 完全相同；真实的越层调用画虚线并在表里列出}
{分层表：层 → 职责 → 允许依赖谁}

### 3.4 运行时视图：{关键流程}
{看图重点：交互先后顺序、哪些是异步、失败时发生什么。}
{Mermaid sequenceDiagram，画最重要的运行路径，至少含一个 alt/else 失败分支 —— mermaid-spec.md §2.4}
{逐跳说明同步/异步与补偿动作，每跳一句话}

### 3.5 数据流视图（数据流图）
{看图重点：数据从哪来、经谁处理、存到哪、跨了哪条信任边界。}
{Mermaid flowchart LR，每条边标注数据名，并标出信任边界 —— mermaid-spec.md §2.5}
{逐个数据存储说明：归属模块与保留策略，各一句话}

### 3.6 部署视图 —— 条件：多节点/多区域/多环境
{看图重点：什么跑在哪里、哪些区域之间通信。}
{Mermaid flowchart LR，环境作为 subgraph，边上标注协议 —— mermaid-spec.md §3.1}

### 3.7 状态机视图 —— 条件：核心实体 ≥4 个状态或存在状态相关规则
{看图重点：核心实体的生命周期，用业务口径的状态。}
{Mermaid stateDiagram-v2，迁移标注触发事件 —— mermaid-spec.md §3.2}

### 3.8 数据模型（ERD）—— 条件：数据模型是主要耦合点
{看图重点：哪些实体被多个模块触碰、各自归属谁。}
{Mermaid erDiagram，只画关键字段 —— mermaid-spec.md §3.3}

{按需才画：泳道图**不属于视图清单**，只有用户明确要求时才画，规则见 mermaid-spec.md §3.4；而且只在它能画出别的视图画不出来的东西时才值得画（人工步骤、系统外绕行、跨团队责任）。如果它只是把运行时图横过来重画一遍，就直说不画。}

## 4. 模块清单与职责

每个模块都要回答：做什么 / 怎么用 / 依赖什么。

| 模块 | 职责 | 对外入口（怎么用） | 依赖 |
|---|---|---|---|
| {模块名} | {做什么} | {API/函数/事件} | {依赖哪些模块} |
| ... | | | |

## 5. 接口定义

### 模块级 API
- `{模块}.{函数}({参数}) -> {返回值}` —— {一句话语义与错误行为}

### 事件 / 消息（如有）
- `{事件名}` —— {发布者} → {订阅者}，载荷 `{结构}`，投递保证 `{至少一次/恰好一次/尽力而为}`

### 数据契约（如适用）
- {实体}：{关键字段与约束} —— 归属 {模块}

## 6. ADR 决策记录

格式：一个决策一个块，按决策时间排序。

### ADR-{n}：{决策标题}

- **日期：** {YYYY-MM-DD}
- **状态：** 已接受 / 被 ADR-{m} 取代
- **背景：** {这个决策要解决什么问题}
- **备选方案：** {方案 A —— 优缺点；方案 B —— 优缺点}
- **决策：** {选定的方案}
- **理由：** {为什么这个方案胜出}
- **代价 / 影响：** {后续要付出什么成本或满足什么前提}

## 7. 8 维度自检

设计如何满足每个维度；未满足的项是风险，不是遗漏。

| 维度 | 设计如何满足 | 状态 |
|---|---|---|
| 1. 功能正确性 | {需求 → 模块映射，验收标准覆盖情况} | ✅ / ⚠️ 风险 |
| 2. 可移植性 | {配置外置情况、环境假设} | ✅ / ⚠️ 风险 |
| 3. 可扩展性 / 可维护性 | {模块边界，新增一个业务功能预计改动几个文件} | ✅ / ⚠️ 风险 |
| 4. 可观测性 | {日志/追踪/指标/告警方案} | ✅ / ⚠️ 风险 |
| 5. 可测试性 | {依赖注入、各模块测试策略} | ✅ / ⚠️ 风险 |
| 6. 易用性 | {上手路径、文档、示例数据方案} | ✅ / ⚠️ 风险 |
| 7. 性能 / 可伸缩性 | {容量估算，10 倍压力下的瓶颈分析} | ✅ / ⚠️ 风险 |
| 8. 安全性 | {输入校验、密钥管理、最小权限、影响面} | ✅ / ⚠️ 风险 |

**需要跟踪的风险：** {所有 ⚠️ 项，每条一句话展开}

## 8. 演进路线图

按阶段推进，MVP 优先；每个阶段单独就有价值。

| 阶段 | 范围 | 退出标准 |
|---|---|---|
| MVP | {最小可用纵向切片} | {必须跑通什么} |
| 阶段 2 | {下一个增量} | {必须跑通什么} |
| 阶段 3 | {后续演进} | {必须跑通什么} |

**明确推迟：** {本次设计有意不做的内容，以及重新评估的触发条件}
```

## C. Heading map (role matching contract)

`md2html.py` maps sections to components by heading prefix (numbering stripped, parentheticals cut). Both columns are accepted, so a document may use either outline — but only one per document.

| Component role | English heading prefix | 中文标题前缀 |
|---|---|---|
| `arch-sec` (diagram section) | `Architecture Views`, `System Architecture (As-Is)` | `架构视图`、`系统架构（现状）` |
| `adr` | `ADR Records` | `ADR 决策记录`、`架构决策记录` |
| `selftest` | `8-Dimension Self-Check` | `8 维度自检` |
| `roadmap` | `Evolution Roadmap` | `演进路线图` |
| `overview` (review reports only, drives the radar) | `Overview (8-Dimension Radar)` | `总览（8 维度雷达）` |
| anything else | generic card | 通用卡片 |

Subsections inside the diagram section (`3.1`-`3.9`) are plain h3 group boxes — their wording does not affect the component role, but `check_views.py` matches them to classify each figure.

## D. Writing notes (both languages)

- Every `###` under `ADR Records` / `ADR 决策记录` starting with `ADR` becomes a collapsed card; keep the `ADR-{n}: {title}` shape.
- Every figure in section 3 gets a one-line "read this for" note (看图重点) — a diagram without a stated question is decoration.
- The component view is the anchor: its node set is what the module list, the layered view and the data-flow stores are checked against.
- Keep tables to the columns shown; `md2html.py` renders the first table of a section as `table.tbl` (the self-check status column is auto-badged, the roadmap table is wrapped in a scroll container).
- Numbers over adjectives: capacity figures, file counts, latency budgets. "Fast" is not evidence.
