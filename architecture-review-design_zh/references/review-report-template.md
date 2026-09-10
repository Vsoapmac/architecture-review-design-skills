# Architecture Review Report Template

Fill every section with real content. Do not keep placeholder text. Placeholders in `{curly braces}` must be replaced or removed. All diagrams follow `mermaid-spec.md`.

> **Rules for this template**
> 1. **Pick ONE outline below (A = English, B = 中文) and use it for the whole document.** Never mix languages: headings, body, table headers, meta chips, diagram labels, captions and the HTML menu must all be in the same language. The language is confirmed with the user before authoring (see SKILL.md "Step 0").
> 2. **Two duties:** ① the section outline for the conversational digest; ② the outline for the .md draft that `md2html.py` renders into the HTML deliverable (each h2 maps to a component — see `html/html-output-spec.md` §5). **If you change an h2 heading, update the mapping table in html-output-spec.md and the role keys in md2html.py.** The score table in section 1 feeds the radar chart; the page JS excludes the Average row and ignores rows whose score is not a number.
> 3. The score table in section 1 must stay the **first table of that section** and keep the `Dimension | Score (0-5) | One-line conclusion` shape, otherwise the radar cannot be drawn.
> 4. **Section 2 documents the system as it actually is** — the five mandatory views plus every conditional view whose trigger holds (mermaid-spec.md §1), each backed by recon evidence. This is what makes the deliverable an architecture document rather than only a score sheet. Run `python check_views.py <draft.md>` before delivering: it fails on a missing view, a node set that differs between the component and layered views, an unlabeled data-flow/swimlane edge, an unused store, or a runtime view without a failure branch.

## A. Section outline — English

```markdown
# Architecture Review Report: {project/scope}

- **Date:** {YYYY-MM-DD}
- **Scope:** {module / subsystem / whole repo}
- **Dimensions evaluated:** {list}
- **Dimensions skipped:** {list, with reason}
- **Language:** English

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

> Scoring rule: every score is backed by evidence in section 3. No evidence → "not evaluated".

## 2. System Architecture (As-Is)

The five mandatory views are 2.1-2.5; draw a conditional view (2.6-2.8) only when its trigger holds. All of them are reconstructed from the code (recon evidence in each note), not from documentation claims. Edge direction convention: component/layered edges are dependencies, runtime edges are time, data-flow edges are data movement (mermaid-spec.md §8).

### 2.1 System Context
{Read this for: what the system is responsible for at its boundary, and what crosses it. Evidence: {entry points / integration config}}
{Mermaid flowchart LR: one system box + `Ext:` nodes — mermaid-spec.md §2.1}

### 2.2 Component View
{Read this for: the real components, the stores, and the current coupling. Evidence: {main modules / dependency manifest}}
{Mermaid flowchart LR with entry/service/data/external — mermaid-spec.md §2.2}

### 2.3 Layered View
{Read this for: what the layers really are, and where the dependency direction is violated. Evidence: {directory layout / import graph}}
{Mermaid flowchart TB, one subgraph per layer, same node set as 2.2 — mermaid-spec.md §2.3}
{Layer table: layer → actual content (paths) → observed violations}

### 2.4 Runtime View: {core flow} (As-Is)
{Read this for: how the flow actually runs today, and where it hurts. Evidence: {entry function / call chain / latency data}}
{Mermaid sequenceDiagram with at least one alt/else failure branch — mermaid-spec.md §2.4}

### 2.5 Data Flow View
{Read this for: where data actually lives, who can reach it, and which boundary it crosses unprotected. Evidence: {storage config / data access code}}
{Mermaid flowchart LR with data-labeled edges and trust boundaries — mermaid-spec.md §2.5}
{Ownership and retention as they are today, including violations (say explicitly when the diagram shows a defect)}

### 2.6 Deployment View — conditional: more than one node, zone or environment
{Read this for: what runs where, and how much redundancy the critical path has. Evidence: {deploy manifests}}
{Mermaid flowchart LR with environment subgraphs and protocol labels — mermaid-spec.md §3.1}

### 2.7 State Machine — conditional: a core entity has ≥4 states or state-dependent rules
{Read this for: the states the code actually implements, and where they disagree with the documented lifecycle. Evidence: {model/enum definitions}}
{Mermaid stateDiagram-v2 with event-labelled transitions — mermaid-spec.md §3.2}

### 2.8 Data Model — conditional: the data model is the main coupling point
{Read this for: which entities more than one module writes, and who owns each. Evidence: {schema / DAO layer}}
{Mermaid erDiagram with the key fields only — mermaid-spec.md §3.3}

{On request only: a swimlane view is NOT part of the catalogue — draw it only if the user asks (mermaid-spec.md §3.4). In a review its only justification is showing what the other views cannot: manual workarounds, on-call repairs, cross-team hand-offs. If it would just re-state the runtime view, skip it and call out those steps in the text instead.}

## 3. Per-Dimension Details

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

## 4. Remediation Roadmap

Ordered by priority (🔴 first), each with an effort estimate.

| # | Priority | Issue | Dimension | Effort (low/med/high) | Suggested fix |
|---|---|---|---|---|---|
| 1 | 🔴 | {issue summary} | {dimension} | {effort} | {fix in one line} |
| 2 | 🟡 | {issue summary} | {dimension} | {effort} | {fix in one line} |
| 3 | ⚪ | {issue summary} | {dimension} | {effort} | {fix in one line} |

**Suggested order of execution:** {1-2-3 reasoning — what unblocks what}

## 5. Quick Wins (do this week)

- {low-cost fixes with big impact}
```

## B. 章节大纲 — 中文

```markdown
# 架构评审报告：{项目/范围}

- **日期：** {YYYY-MM-DD}
- **评审范围：** {模块 / 子系统 / 全仓库}
- **已评估维度：** {列表}
- **已跳过维度：** {列表 + 原因}
- **语言：** 中文

## 1. 总览（8 维度雷达）

| 维度 | 评分（0-5） | 一句话结论 |
|---|---|---|
| 1. 功能正确性 | {n} | {一句话} |
| 2. 可移植性 | {n} | {一句话} |
| 3. 可扩展性 / 可维护性 | {n} | {一句话} |
| 4. 可观测性 | {n} | {一句话} |
| 5. 可测试性 | {n} | {一句话} |
| 6. 易用性 | {n} | {一句话} |
| 7. 性能 / 可伸缩性 | {n} | {一句话} |
| 8. 安全性 | {n} | {一句话} |
| **平均** | **{avg}** | **{总体结论，一句话}** |

> 评分规则：每个分数都在第 3 节有证据支撑。没有证据 → 写"未评估"。

## 2. 系统架构（现状）

五类必需视图为 2.1-2.5；条件视图（2.6-2.8）只在触发条件成立时画。所有图都由代码还原（每张图注明取证来源），而不是照抄文档里的说法。边的方向约定：组件图/分层图表示依赖，运行时图表示时间顺序，数据流图表示数据流动（mermaid-spec.md §8）。

### 2.1 系统上下文
{看图重点：系统在边界上承担什么、什么东西穿过边界。取证：{入口代码 / 集成配置}}
{Mermaid flowchart LR：一个系统框 + `Ext:` 节点 —— mermaid-spec.md §2.1}

### 2.2 组件视图（架构图）
{看图重点：真实组件、存储，以及当前耦合。取证：{主要模块 / 依赖清单}}
{Mermaid flowchart LR，entry/service/data/external 四色 —— mermaid-spec.md §2.2}

### 2.3 分层视图（分层图）
{看图重点：真实分层是什么、依赖方向在哪里被破坏。取证：{目录结构 / import 关系}}
{Mermaid flowchart TB，每层一个 subgraph，节点集合与 2.2 相同 —— mermaid-spec.md §2.3}
{分层表：层 → 实际内容（路径） → 观察到的越层情况}

### 2.4 运行时视图：{核心流程}（现状）
{看图重点：这条流程今天实际怎么跑、卡在哪里。取证：{入口函数 / 调用链 / 延迟数据}}
{Mermaid sequenceDiagram，至少含一个 alt/else 失败分支 —— mermaid-spec.md §2.4}

### 2.5 数据流视图（数据流图）
{看图重点：数据实际存在哪、谁都能碰、跨了哪条无保护边界。取证：{存储配置 / 数据访问代码}}
{Mermaid flowchart LR，每条边标注数据名并标出信任边界 —— mermaid-spec.md §2.5}
{按现状写归属与保留策略；如果图里画的就是缺陷，正文必须点名，不能默认它是对的}

### 2.6 部署视图 —— 条件：多节点/多区域/多环境
{看图重点：什么跑在哪里、关键路径的冗余度如何。取证：{部署清单}}
{Mermaid flowchart LR，环境作为 subgraph，边上标注协议 —— mermaid-spec.md §3.1}

### 2.7 状态机视图 —— 条件：核心实体 ≥4 个状态或存在状态相关规则
{看图重点：代码里实际实现的状态，以及哪里与文档口径不一致。取证：{模型/枚举定义}}
{Mermaid stateDiagram-v2，迁移标注触发事件 —— mermaid-spec.md §3.2}

### 2.8 数据模型（ERD）—— 条件：数据模型是主要耦合点
{看图重点：哪些实体被多个模块写入、各自归属谁。取证：{表结构 / DAO 层}}
{Mermaid erDiagram，只画关键字段 —— mermaid-spec.md §3.3}

{按需才画：泳道图**不属于视图清单**，只有用户明确要求时才画（规则见 mermaid-spec.md §3.4）。评审里它唯一的理由是能画出别的视图画不出来的东西——人工绕行、值班手工修复、跨团队交接；如果只是把运行时图横过来重画一遍，就别画，改为在正文里点出那几个步骤。}

## 3. 各维度详情

### 维度 {n}：{名称} —— 评分 {x}/5

**证据：**
- {文件路径}:{行号} —— {具体观察或代码片段}
- {文件路径}:{行号} —— {具体观察或代码片段}

**发现的问题：**
- 🔴 {描述}（{位置}）
- 🟡 {描述}（{位置}）
- ⚪ {描述}（{位置}）

**做得好的地方（可选）：**
- {值得保留的做法}

---

（对每个已评估维度重复）

## 4. 整改路线图

按优先级排序（🔴 优先），每项附工作量估级。

| # | 优先级 | 问题 | 维度 | 工作量（低/中/高） | 建议改法 |
|---|---|---|---|---|---|
| 1 | 🔴 | {问题摘要} | {维度} | {工作量} | {一句话改法} |
| 2 | 🟡 | {问题摘要} | {维度} | {工作量} | {一句话改法} |
| 3 | ⚪ | {问题摘要} | {维度} | {工作量} | {一句话改法} |

**建议执行顺序：** {1-2-3 的推理——什么先做完能解锁什么}

## 5. 快速见效项（本周可做）

- {低成本、高收益的修复}
```

## C. Heading map (role matching contract)

`md2html.py` maps sections to components by heading prefix (numbering stripped, parentheticals cut). Both columns are accepted, so a document may use either outline — but only one per document.

| Component role | English heading prefix | 中文标题前缀 |
|---|---|---|
| `overview` (radar + score table) | `Overview` | `总览`、`概览` |
| `arch-sec` (diagram section) | `System Architecture`, `Architecture Views` | `系统架构`、`架构视图` |
| `adr` (only when you add ADR-style decision records) | `ADR Records` | `ADR 决策记录` |
| anything else | plain generic card | 通用卡片 |

**Deliberately NOT role-mapped in this template:** `Per-Dimension Details` / `各维度详情`, `Remediation Roadmap` / `整改路线图` and `Quick Wins` / `快速见效项` all render as plain cards — in particular **do not rename the remediation roadmap to "Evolution Roadmap"** (`演进路线图`), which would silently turn it into the design template's `roadmap` role with a different layout. The documentation-only variant (SKILL.md, Workflow A) reuses the `arch-sec` + `adr` rows above; its module list, interface definitions and risk list are plain cards.

Subsections inside the As-Is section (`2.1`-`2.9`) are plain h3 group boxes; their wording does not affect the component role, but `check_views.py` matches them to classify each figure.

## D. Writing notes (both languages)

- Every score needs evidence (file path + line, or a direct observation); this includes the views in section 2 — say where the structure was read from.
- When a view exposes a defect (a bypassed module, a store with two writers, a manual workaround), the text next to the diagram must name it as a finding — a defect shown in a diagram but not written down reads like the intended design.
- Grades are 🔴 must fix / 🟡 should fix / ⚪ worth knowing, used consistently in prose, lists and tables.
- The rapid score table stays compact: one line per dimension, the verdict in the Average row.
- If a dimension was skipped, say so and why in section 1 and do not score it ("not evaluated").
