# HTML 产物规范(html-output-spec)

本文件是评审报告/设计文档 HTML 产物的**单一事实源**。Tier 1(Python 脚本)与 Tier 2(AI 手写)都必须产出符合本规范的 HTML。样式与交互代码只存在于 `report-shell.html`,正文结构规则见下文。

## 1. 产物要求

- 单文件自包含(样式、脚本、内容全内嵌),双击可开;文件名:
  - 设计:`docs/design/YYYY-MM-DD-<系统>-architecture-design.html`
  - 评审:`docs/review/YYYY-MM-DD-<范围>-architecture-review.html`
- 两处渐进增强联网依赖,断网必须优雅降级:
  1. Mermaid CDN(`https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js`)
  2. Google Fonts Noto Sans SC(**仅非苹果设备**,JS 检测后注入)
- 无未替换 `{花括号}` 占位符;标题/作者/日期等元信息必须真实。

## 2. 页面结构(硬性顺序)

```
<header id="topbar"><div class="topbar-inner"> : h1#doc-title + .meta-chips + 工具按钮(#theme-btn #print-btn #collapse-all #expand-all #menu-btn)
<div id="overlay">(移动端抽屉遮罩)
<div id="layout">
  <aside id="sidebar"><div class="side-inner"> : .search-wrap(#q) + ul#toc(JS 自动生成,手写模式可留空)
  <main id="main"><div class="wrap"> : section.sec 序列(见 §4)
页尾 #to-top 回到顶部
```

## 3. 双主题与字体(只改 report-shell.html,正文不得写死颜色)

- `html[data-theme="dark|light"]` 切换;CSS 变量定义全部在 shell 内。
- JS 顺序:localStorage → 无则 prefers-color-scheme → 手动 🌓 覆盖并记忆。
- 深色下 Mermaid 以 theme=dark 重新渲染。
- 字体:正文 Apple-first 系统栈;代码 `ui-monospace, "Cascadia Code", Consolas, "SF Mono", Menlo, monospace`;非苹果设备在线时注入 Noto Sans SC(400/500/700),成功后给 `<body>` 加 `wf-noto` 类(与 shell CSS 选择器 `body.wf-noto` 一致)。
- 排版硬性:正文 ≥14px(设计值 15px)、行高 ~1.75、正文常规字重(400)、标题 600-700。禁止细体 + 浅灰小字组合。

## 4. 正文组件与 Markdown 源稿映射(模板即契约)

md 源稿 h2 标题去掉序号后按**前缀匹配**映射;两个模板文件(`design-doc-template.md` / `review-report-template.md`)的 h2 标题改动必须同步本表:h2 **展示文本保留源稿原文(含序号)**,仅匹配时去序号;slug/id 生成时去序号与标点。

| 源稿 h2 前缀(设计) | 产出组件 |
|---|---|
| 背景与目标 | `section.sec` 普通卡(列表自动徽章化,见 §5) |
| 需求 | `section.sec` 普通卡 |
| 架构概览 | `section.sec arch-sec`;mermaid 围栏 → `figure.arch` 三件套 |
| 模块清单与职责 | `section.sec`;首个表格 → `table.tbl` |
| 接口定义 | `section.sec`;代码围栏 → `pre.code` |
| ADR 决策记录 | `section.sec adr`;每个 `### ADR-n:标题` → `details.adr`(默认收起),内容直至下一个同级标题 |
| 8 维度自检表 | `section.sec selftest`;首表 → `table.tbl`,状态列整格按 §5 徽章表徽章化(含记号即整格入 chip) |
| 演进路线图 | `section.sec roadmap`;首表放入 `<div class="roadmap">` |

| 源稿 h2 前缀(评审) | 产出组件 |
|---|---|
| 总览 | `section.sec overview`;评分表 → `table.tbl.tbl-scores`(含"平均"行,JS 排除后取前 8 行画雷达);表前插入 `<div class="radar-wrap">` |
| 各维度详情 | `section.sec`;`### 维度 n:…` → `h3.sub-h3` 分组连续排布 |
| 整改路线图 | `section.sec`;首表 → `table.tbl` |
| 速赢 | `section.sec` 普通卡 |

未匹配标题一律 `section.sec`(generic);h3 → `.sub-h3`;普通围栏 → `pre.code`;普通表格 → `table.tbl`。`### ADR-…` 标题出现在非 ADR 角色节内时按普通 h3(`.sub-h3`)处理,不被吞掉。所有 section 结构:

```html
<section class="sec {role}" id="{slug}">
  <h2 class="sec-title"><span>{标题}</span><button class="tgl" type="button" aria-label="折叠章节" aria-expanded="true">↕</button></h2>
  <div class="sec-body">…内容…</div>
</section>
```

### figure.arch 三件套(所有 Mermaid 图必须这样写)

```html
<figure class="arch">
  <div class="arch-src" hidden>Mermaid 源码(HTML 转义后)</div>
  <div class="arch-out" role="img"></div>
  <figcaption class="arch-note">联网后可查看渲染图,源码已内嵌可复制。</figcaption>
</figure>
```

JS 读取 `.arch-src` 的 textContent 调 `mermaid.render()`;断网/失败时给 `<html>` 加 `no-net`,显示 `.arch-note` 并把源码以 `pre.code` 展示在 `.arch-out` 内。**不得**用 `<pre class="mermaid">` 直挂(无法安全重渲染)。

## 5. 文本自动徽章化规则

适用上下文仅两处:**列表项整项**与**自检表状态列整格**——其文本开头(允许前导空格)是以下记号之一时,记号与后续正文**整个条目包入同一个 chip**(chip 允许换行,不得只包记号);其余位置(普通表格单元格、段落中部)不自动徽章化:

| 记号 | 类 |
|---|---|
| 🔴(严重度:必须修复) | `.chip-red` |
| 🟡 | `.chip-yellow` |
| ⚪ | `.chip-gray` |
| ✅ | `.chip-ok` |
| ⚠️ | `.chip-warn` |

### 链接协议红线(两 tier 共同)

- 禁止产出 `javascript:` / `data:` 等可执行协议链接;仅放行 `http`/`https`/`mailto`、`#` 锚点、`/` 开头的绝对路径与相对/裸路径。
- 不合规链接渲染为纯文本(去掉 <a>),不得保留可点击的脚本入口。

## 6. 无障碍与打印

- 按钮有 aria-label;折叠按钮维护 aria-expanded;图区有 role="img"。
- `@media print`:强制浅色、隐藏 #sidebar 与工具按钮、单栏、.arch/.tbl/li 避免断页、chip 用 print-color-adjust: exact。

## 7. Tier 2(AI 手写)补充规则

1. 复制 `report-shell.html` 为最终文件,**不删除任何 CSS/JS/令牌结构**;令牌替换:标题入 `<!--T:TITLE-->`,元信息 chips 入 `<!--T:META-->`,全部正文入 `<!--T:BODY-->`;`<!--T:EXTRA-->` 不需要则整体删除。
2. 元信息 chip 文案格式:字段名去冒号 + 一个空格 + 值,例如 `日期 2026-09-09`。
3. 令牌 `<!--T:TITLE-->` 在 shell 中位于 `<title>` 与 `h1#doc-title` 两处,两处都替换为同一标题值;`<!--T:EXTRA-->` 不需要则整体删除。
4. `ul#toc` 可留空(JS 自动生成),但标题与各 section 必须保留 §4 结构类。
5. 自查清单见 §8。

## 8. 产出验收清单(两 tier 通用)

- [ ] 浏览器双击可开;无控制台报错
- [ ] 浅/深主题切换生效且刷新后记忆;系统偏好首次生效
- [ ] 联网时 Mermaid 渲染成功;屏蔽 CDN 后显示降级提示且源码可复制
- [ ] 搜索框能过滤章节并高亮命中(mark);折叠按钮与"折叠全部/展开全部"可用
- [ ] 评审报告:雷达图与总览表 1-8 行分值一致;"平均"行不影响雷达
- [ ] 打印预览:浅色、无侧栏、无按钮,分页干净
- [ ] 无 `{` 占位符、无 `<!--T:` 残留令牌
- [ ] ADR 折叠卡默认收起且可展开;列表项/自检列的徽章化(chip 含记号与正文)渲染正确
- [ ] 元信息 chips 显示真实字段(日期/作者/状态/范围等);标题与正文 h2 保留源稿序号
- [ ] 两 tier 产物结构互比一致(章节卡/arch 三件套/表格/徽章类名同规范);非苹果设备联网时 Noto 注入生效、断网回退正常
