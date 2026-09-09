# -*- coding: utf-8 -*-
"""md2html.py — 受限 Markdown → 规范 HTML 转换器(Tier 1,纯标准库)。

用法:
    python md2html.py <源稿.md> <输出.html> [--keep-src]
    默认转换成功后删除源稿,传 --keep-src 保留。

读取同目录 report-shell.html,替换 <!--T:TITLE--> / <!--T:META--> /
<!--T:BODY--> 令牌组装最终单文件 HTML。

方言:ATX 标题 h1-h4、GFM 表格、平级无序/有序列表、围栏代码
(mermaid 围栏特判为 figure.arch)、块引用(>)、粗/斜/行内代码/链接、hr。
其余语法一律 HTML 转义为普通文本(丢样式不丢内容)。
章节→组件映射见 html-output-spec.md §4(模板即契约)。
"""
import argparse
import sys
import html as _html
import re
from pathlib import Path

DESIGN_ROLES = {
    "架构概览": "arch-sec",
    "ADR 决策记录": "adr",
    "8 维度自检表": "selftest",
    "演进路线图": "roadmap",
}
REVIEW_ROLES = {"总览": "overview"}
CHIP_MAP = [("🔴", "chip-red"), ("🟡", "chip-yellow"), ("⚪", "chip-gray"),
            ("✅", "chip-ok"), ("⚠️", "chip-warn")]
FENCE = re.compile(r"^```(\w*)\s*$")


def esc(s):
    return _html.escape(s, quote=True)


def role_of(title):
    t = strip_heading_no(title)
    t = re.split(r"[（(]", t)[0].strip()
    for key, role in DESIGN_ROLES.items():
        if t.startswith(key):
            return role
    for key, role in REVIEW_ROLES.items():
        if t.startswith(key):
            return role
    return "generic"


_SAFE_SCHEMES = ("http", "https", "mailto")

# URL 内允许单层括号([x](a(b))),不含空白;更深嵌套整体按纯文本降级
_LINK_RE = re.compile(r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))*)\)")


def safe_href(url):
    """链接协议白名单:仅放行 http/https/mailto、'#'锚点、'/'开头与相对/裸路径;
    检测到 javascript:/data: 等可执行协议返回 None(调用方渲染为纯文本)。

    顺序契约:入参必须是 esc(quote=True) 之后的文本——对 '&' 实体混淆
    (如 javascript&colon:) 的免疫依赖调用点先行转义,勿在转义前调用本函数。"""
    u = url.strip()
    if u.startswith(("#", "/", "./", "../")):
        return u
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", u)
    if not m:
        return u  # 无 scheme:相对/裸路径
    return u if m.group(1).lower() in _SAFE_SCHEMES else None


def inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), s)
    toks = []
    def link_repl(m):
        lab = m.group(1)
        lab = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", lab)
        lab = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", lab)
        url = safe_href(m.group(2))
        if url is None:
            toks.append(lab)
        else:
            toks.append('<a href="%s">%s</a>' % (url, lab))
        return "\x00LINK%d\x00" % (len(toks) - 1)
    s = _LINK_RE.sub(link_repl, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    for i, t in enumerate(toks):
        s = s.replace("\x00LINK%d\x00" % i, t)
    return s


def chipify(line):
    line = line.lstrip()
    for mark, cls in CHIP_MAP:
        if line.startswith(mark):
            return '<span class="chip %s">%s</span>' % (cls, esc(line))
    return None


def cell_html(cell):
    c = cell.strip()
    for mark, cls in (("⚠️", "chip-warn"), ("✅", "chip-ok"),
                      ("🔴", "chip-red"), ("🟡", "chip-yellow"),
                      ("⚪", "chip-gray")):
        if mark in c:
            return '<span class="chip %s">%s</span>' % (cls, esc(c))
    return inline(c)


def render_table(lines, role):
    """GFM 表格:第 2 行为分隔行时第 1 行为表头。"""
    rows = []
    for ln in lines:
        rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
    head, body = [], rows
    if len(rows) >= 2 and rows[1] and all(
            re.fullmatch(r":?-{1,}:?", c or "-") for c in rows[1]):
        head, body = rows[0], rows[2:]
    cls = "tbl tbl-scores" if role == "overview" else "tbl"
    thead = ""
    if head:
        thead = "<thead><tr>%s</tr></thead>" % "".join(
            "<th>%s</th>" % inline(h) for h in head)
    trs = []
    for r in body:
        # overview 平均行按普通行输出;雷达 JS 以"平均/avg"文本排除
        if role == "selftest" and len(r) >= 2:
            tds = "".join("<td>%s</td>" % (cell_html(c) if i == len(r) - 1 else inline(c))
                          for i, c in enumerate(r))
        else:
            tds = "".join("<td>%s</td>" % inline(c) for c in r)
        trs.append("<tr>%s</tr>" % tds)
    html_tbl = '<table class="%s">%s<tbody>%s</tbody></table>' % (cls, thead, "".join(trs))
    if role == "roadmap":
        return '<div class="roadmap">%s</div>' % html_tbl
    return html_tbl


def fence_html(lang, code):
    if lang == "mermaid":
        return ('<figure class="arch"><div class="arch-src" hidden>%s</div>'
                '<div class="arch-out" role="img"></div>'
                '<figcaption class="arch-note">联网后可查看渲染图,源码已内嵌可复制。</figcaption></figure>'
                % esc(code.strip()))
    return '<pre class="code"><code>%s</code></pre>' % esc(code.rstrip())


def heading(line, role):
    m = re.match(r"^(#{1,4})\s+(.*)$", line)
    level = len(m.group(1))
    text = m.group(2).strip()
    if level == 1:
        return ("h1", "<h1>%s</h1>" % inline(text))
    if level == 2:
        return ("h2", None)  # h2 标题由调用方切节消费(section_html 统一输出,任务 4 追加)
    if level == 3:
        if role == "adr" and re.match(r"adr", text, re.I):
            return ("adr", None)
        return ("h3", '<h3 class="sub-h3">%s</h3>' % inline(text))
    return ("h4", "<h4>%s</h4>" % inline(text))


def parse_meta(lines):
    chips, i = [], 0
    while i < len(lines) and not lines[i].strip():
        i += 1  # 容忍标题与元数据之间的空行
    while i < len(lines):
        m = re.match(r"^\s*-\s*\*\*([^*]+?)\s*[：:]\s*\*\*\s*(.*)$", lines[i])
        if not m:
            break
        chips.append('<span class="chip">%s %s</span>'
                     % (esc(m.group(1)), inline(m.group(2))))
        i += 1
    return "".join(chips), lines[i:]


def blocks(lines, role):
    """把章节正文行渲染为 HTML(不含 section 包裹)。"""
    # 前置:调用方须先按 h2 切节;ADR 节内 '### ADR-…' 条目头由调用方剥离
    if isinstance(lines, str):
        lines = re.split(r"\r?\n", lines)
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if FENCE.match(ln):
            lang = FENCE.match(ln).group(1)
            buf, i = [], i + 1
            while i < n and not FENCE.match(lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1  # 跳过闭合围栏
            out.append(fence_html(lang, "\n".join(buf)))
            continue
        if ln.startswith(">"):
            buf = [re.sub(r"^>\s?", "", ln)]
            i += 1
            while i < n and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append('<blockquote class="ev">%s</blockquote>' % inline(" ".join(buf)))
            continue
        if re.match(r"^#{1,4}\s", ln):
            kind, h = heading(ln, role)
            if h is not None:
                out.append(h)
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            tag = "ol" if re.match(r"^\s*\d+\.\s+", ln) else "ul"
            items, i = [], i
            while i < n and (re.match(r"^\s*[-*]\s+", lines[i])
                             or re.match(r"^\s*\d+\.\s+", lines[i])):
                item = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])
                c = chipify(item)
                items.append("<li>%s</li>" % (c if c else inline(item)))
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag))
            continue
        if ln.lstrip().startswith("|"):
            buf, i = [], i
            while i < n and lines[i].lstrip().startswith("|"):
                buf.append(lines[i])
                i += 1
            out.append(render_table(buf, role))
            continue
        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        para, i = [ln], i + 1
        while i < n and lines[i].strip() and not (
                FENCE.match(lines[i]) or lines[i].startswith(">")
                or re.match(r"^#{1,4}\s", lines[i])
                or re.match(r"^\s*[-*]\s+", lines[i])
                or re.match(r"^\s*\d+\.\s+", lines[i])
                or lines[i].lstrip().startswith("|")
                or lines[i].strip() == "---"):
            para.append(lines[i])
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(x.strip() for x in para)))
    return "\n".join(out)


# ---------- section 组装与文档渲染 ----------

def slugify(s):
    s = strip_heading_no(s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w\-]+", "", s, flags=re.UNICODE)
    return s or "sec"


_NO_RE = re.compile(r"^\s*\d+(\.\d+)*[\.、]?\s*")


def strip_heading_no(s):
    """去 h2 标题前导序号('3. ' / '1.2 ' / '3、'),供 role 匹配与 slug 共用。"""
    return _NO_RE.sub("", s or "").strip()


def unique_slug(title, used):
    base = slugify(title)
    cand, k = base, 1
    while cand in used:
        k += 1
        cand = "%s-%d" % (base, k)
    used.add(cand)
    return cand


def split_h3(lines, prefix_re):
    """按 '### ADR-n:'(正则 prefix_re)标题切块。返回 [(标题|None, 正文行)]。
    None 标题 = 首个条目之前的节前导内容(必须保留,不得丢弃)。"""
    blocks_, cur_title, cur = [], None, []
    for ln in lines:
        if re.match(prefix_re, ln):
            if cur_title is not None:
                blocks_.append((cur_title, cur))
            elif cur:
                blocks_.append((None, cur))
            cur_title, cur = ln.strip(), []
        else:
            cur.append(ln)
    if cur_title is not None:
        blocks_.append((cur_title, cur))
    elif cur:
        blocks_.append((None, cur))
    return blocks_


def section_html(title, lines, forced_id=None):
    role = role_of(title)
    tgl = ('<h2 class="sec-title"><span>%s</span>'
           '<button class="tgl" type="button" aria-label="折叠章节" '
           'aria-expanded="true">↕</button></h2>' % inline(title))
    if role == "adr":
        body = ""
        for t, blk in split_h3(lines, re.compile(r"^###\s+adr", re.I)):
            if t is None:
                body += blocks(blk, "adr")
            else:
                body += ('<details class="adr"><summary>%s</summary>'
                         '<div class="adr-body">%s</div></details>'
                         % (inline(re.sub(r"^###\s+", "", t).strip()), blocks(blk, "adr")))
    else:
        body = blocks(lines, role)
        if role == "overview":
            body = '<div class="radar-wrap"></div>' + body
    sid = forced_id or slugify(title)
    return ('<section class="sec %s" id="%s">%s<div class="sec-body">%s</div></section>'
            % (role, sid, tgl, body))


def render_document(title, meta, body):
    shell = Path(__file__).with_name("report-shell.html").read_text(encoding="utf-8")
    return (shell.replace("<!--T:TITLE-->", title)
                 .replace("<!--T:META-->", meta)
                 .replace("<!--T:BODY-->", body)
                 .replace("<!--T:EXTRA-->", ""))


def render_document_from_md(md_text):
    lines = md_text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("源稿必须以 '# 标题' 开头")
    title = lines[0][2:].strip()
    meta, rest = parse_meta(lines[1:])
    parts, sec_lines = [], []
    used = set()
    def flush():
        if not sec_lines:
            return
        if sec_lines[0].startswith("## "):
            title = sec_lines[0][3:].strip()
            parts.append(section_html(title, sec_lines[1:], unique_slug(title, used)))
        else:  # ## 之前的引言行
            parts.append(blocks(sec_lines, "generic"))
        sec_lines.clear()
    for ln in rest:
        if ln.startswith("## ") and sec_lines:
            flush()
        sec_lines.append(ln)
    flush()
    return render_document(esc(title), meta, "\n".join(parts))


def main():
    ap = argparse.ArgumentParser(description="受限 Markdown → 规范 HTML(读取同目录 report-shell.html)")
    ap.add_argument("src", type=Path, help=".md 源稿路径")
    ap.add_argument("out", type=Path, help="输出 .html 路径")
    ap.add_argument("--keep-src", action="store_true", help="保留源稿(默认转换成功后删除源稿)")
    a = ap.parse_args()
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        if a.out.resolve() == a.src.resolve():
            raise ValueError("输出路径与源稿路径相同,已中止(会自毁源稿)")
        shell = Path(__file__).with_name("report-shell.html")
        if not shell.exists():
            raise FileNotFoundError("缺少 %s(report-shell.html 必须与 md2html.py 同目录)" % shell)
        out_html = render_document_from_md(a.src.read_text(encoding="utf-8"))
        a.out.write_text(out_html, encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print("转换失败:%s" % e, file=sys.stderr)
        sys.exit(1)
    if not a.keep_src:
        try:
            a.src.unlink()
        except OSError as e:
            print("提示:源稿删除失败(可忽略):%s" % e, file=sys.stderr)
    print("OK -> %s" % a.out)


if __name__ == "__main__":
    main()
