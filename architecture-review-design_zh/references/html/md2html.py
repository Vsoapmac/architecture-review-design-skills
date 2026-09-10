# -*- coding: utf-8 -*-
"""md2html.py - restricted Markdown → spec HTML converter (Tier 1, pure stdlib).

Usage:
    python md2html.py <draft.md> <output.html> [--lang en|zh] [--keep-src]
    By default the draft is deleted after a successful conversion; pass
    --keep-src to keep it (it is also the deliverable when the user asks for
    the .md source next to the .html).

Language: --lang chooses the report language and drives the UI chrome of the
generated HTML (<html data-lang>, menu labels) as well as the language-specific
section→component role matching and figure captions. Always pass --lang: it is
the only path on which body language and menu language cannot disagree. Without
it the language is guessed from the draft's *prose* (fenced blocks and inline
code are ignored, so a code-heavy Chinese draft is still detected as Chinese);
that fallback is a convenience, not the contract.

Reads report-shell.html next to this script and substitutes the
<!--T:TITLE--> / <!--T:META--> / <!--T:BODY--> tokens to assemble the final
single-file HTML.

Dialect: ATX headings h1-h4, GFM tables, flat unordered/ordered lists, fenced
code blocks (a mermaid fence is special-cased as figure.arch), block quotes
(>), bold/italic/inline code/links/images, hr. Any other syntax is HTML-escaped
into plain text (style lost, content kept).
Section→component mapping: see html-output-spec.md §5 (the template is the contract).
"""
import argparse
import sys
import html as _html
import re
from pathlib import Path

# h2 heading prefixes (numbering already stripped, parentheticals cut) → component
# role. Both the English and the Chinese template outlines are accepted, so the
# same generator serves both languages; longer keys are matched first. Keys are
# matched in lowercase, so a trailing parenthetical like "(As-Is)" is already
# removed by the time we get here - never add a key that carries one.
ROLE_KEYS = [
    ("architecture views", "arch-sec"),
    ("architecture overview", "arch-sec"),
    ("architecture diagrams", "arch-sec"),
    ("system architecture", "arch-sec"),
    ("as-is architecture", "arch-sec"),
    ("架构视图", "arch-sec"),
    ("架构总览", "arch-sec"),
    ("架构概览", "arch-sec"),
    ("架构图", "arch-sec"),
    ("系统架构", "arch-sec"),
    ("adr records", "adr"),
    ("adr 决策记录", "adr"),
    ("架构决策记录", "adr"),
    ("决策记录", "adr"),
    ("8-dimension self-check", "selftest"),
    ("8 dimension self-check", "selftest"),
    ("8 维度自检", "selftest"),
    ("8维度自检", "selftest"),
    ("维度自检", "selftest"),
    ("evolution roadmap", "roadmap"),
    ("演进路线图", "roadmap"),
    ("演进规划", "roadmap"),
    ("overview", "overview"),
    ("总览", "overview"),
    ("概览", "overview"),
]
CHIP_MAP = [("🔴", "chip-red"), ("🟡", "chip-yellow"), ("⚪", "chip-gray"),
            ("✅", "chip-ok"), ("⚠️", "chip-warn")]
FENCE = re.compile(r"^```(\w*)\s*$")

# UI strings that the generator itself writes into the document (the rest of the
# menu chrome lives in report-shell.html and follows <html data-lang>).
LANG_STRINGS = {
    "en": {
        "tgl": "Toggle section",
        "arch_note": "The diagram renders when online; the source is embedded below for copying.",
        "radar": "8-dimension score radar",
    },
    "zh": {
        "tgl": "折叠章节",
        "arch_note": "联网后可查看渲染图；源码已内嵌，可复制后自行渲染。",
        "radar": "8 维度评分雷达图",
    },
}
LOCALES = {"en": "en", "zh": "zh-CN"}

# Static UI literals shipped inside report-shell.html. The shell's runtime I18N
# table already switches these by <html data-lang>, but a generated Chinese file
# must also be correct when read statically (no JS, plain text diff, print
# preview), so the generator rewrites the markup itself. Every source literal is
# verified to exist, which turns any shell edit into a loud failure instead of a
# silently stale label.
SHELL_LITERALS = [
    ('aria-label="Toggle light/dark theme"', 'aria-label="切换深/浅色主题"'),
    ('aria-label="Print or save as PDF"', 'aria-label="打印或另存为 PDF"'),
    ('aria-label="Collapse all sections"', 'aria-label="折叠全部章节"'),
    ('aria-label="Expand all sections"', 'aria-label="展开全部章节"'),
    ('aria-label="Open table of contents"', 'aria-label="打开目录"'),
    ('aria-label="Table of contents"', 'aria-label="目录"'),
    ('aria-label="Search"', 'aria-label="搜索"'),
    ('aria-label="Back to top"', 'aria-label="回到顶部"'),
    ('aria-label="Zoom out"', 'aria-label="缩小"'),
    ('aria-label="Zoom in"', 'aria-label="放大"'),
    ('aria-label="Reset zoom"', 'aria-label="恢复原始大小"'),
    ('aria-label="Close"', 'aria-label="关闭"'),
    ('placeholder="🔍 Search sections &amp; content…"', 'placeholder="🔍 搜索章节与内容…"'),
    (">Collapse all<", ">折叠全部<"),
    (">Expand all<", ">展开全部<"),
    (">↑ Top<", ">↑ 顶部<"),
]
_CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
_FENCE_BLOCK_RE = re.compile(r"```.*?```", re.S)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_HTML_TAG_RE = re.compile(r"<html\b[^>]*>", re.I)
_LANG_ATTR_RE = re.compile(r'(?<![-\w])lang="[^"]*"')
_DATA_LANG_ATTR_RE = re.compile(r'data-lang="[^"]*"')


def esc(s):
    return _html.escape(s, quote=True)


def ui_string(lang, key):
    return LANG_STRINGS.get(lang, LANG_STRINGS["en"]).get(key, LANG_STRINGS["en"][key])


def detect_lang(text):
    """Detect the language of the *prose*, used only when --lang is absent.
    Fenced blocks and inline code are removed first: code (identifiers, URLs,
    mermaid source) is Latin-heavy and would otherwise flip a Chinese document
    with a large diagram listing to "en"."""
    t = _INLINE_CODE_RE.sub(" ", _FENCE_BLOCK_RE.sub(" ", text or ""))
    cjk = len(_CJK_RE.findall(t))
    latin = len(re.findall(r"[A-Za-z]", t))
    if cjk == 0 and latin == 0:
        return "en"
    return "zh" if cjk * 2 >= latin else "en"


def role_of(title):
    t = strip_heading_no(title)
    t = re.split(r"[（(]", t)[0].strip().lower()
    for key, role in sorted(ROLE_KEYS, key=lambda kv: -len(kv[0])):
        if t.startswith(key):
            return role
    return "generic"


_SAFE_SCHEMES = ("http", "https", "mailto")
_SAFE_IMG_SCHEMES = ("http", "https")

# URLs may nest one level of parentheses ([x](a(b))), with no whitespace; deeper nesting falls back to plain text for the whole link
_LINK_RE = re.compile(r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))*)\)")
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(((?:[^()\s]|\([^()\s]*\))*)\)")


def _scheme_of(url):
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", url.strip())
    return m.group(1).lower() if m else None


def safe_href(url):
    """Link protocol whitelist: only http/https/mailto, '#' anchors, '/' prefixes
    and relative/bare paths pass; executable protocols such as javascript:/data:
    return None (the caller renders them as plain text).

    Ordering contract: the argument must already be text escaped with
    esc(quote=True) - immunity to '&'-entity obfuscation (e.g.
    javascript&colon:) depends on the call site escaping first; never call
    this function before escaping."""
    u = url.strip()
    if u.startswith(("#", "/", "./", "../")):
        return u
    scheme = _scheme_of(u)
    if scheme is None:
        return u  # no scheme: relative/bare path
    return u if scheme in _SAFE_SCHEMES else None


def safe_img_src(url):
    """Image source whitelist: http/https, relative/absolute paths, and
    data:image/* (self-contained reports embed local pictures). data:text/html
    and javascript: are rejected; a rejected image degrades to its alt text."""
    u = url.strip()
    if u.startswith(("#", "/", "./", "../")):
        return u
    scheme = _scheme_of(u)
    if scheme is None:
        return u
    if scheme in _SAFE_IMG_SCHEMES:
        return u
    if scheme == "data" and re.match(r"^data:image/(png|jpe?g|gif|webp|svg\+xml|avif);", u, re.I):
        return u
    return None


def inline(s):
    """Inline markdown. Code spans, images and links are first replaced by
    placeholders so that later passes (bold/italic, and the nesting of an image
    inside a link label) never rewrite their contents; the placeholders are then
    expanded to a fixpoint, which is what makes `[![alt](img)](url)` work."""
    s = esc(s)
    toks = []

    def tok(html_text):
        toks.append(html_text)
        return "\x00LINK%d\x00" % (len(toks) - 1)

    s = re.sub(r"`([^`]+)`", lambda m: tok("<code>%s</code>" % m.group(1)), s)

    def img_repl(m):
        alt = m.group(1)
        src = safe_img_src(m.group(2))
        return tok(alt if src is None else
                   '<img class="fig-img" src="%s" alt="%s" loading="lazy">' % (src, alt))

    def link_repl(m):
        lab = m.group(1)
        lab = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", lab)
        lab = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", lab)
        url = safe_href(m.group(2))
        return tok(lab if url is None else '<a href="%s">%s</a>' % (url, lab))

    s = _IMG_RE.sub(img_repl, s)
    s = _LINK_RE.sub(link_repl, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    for _ in range(6):                       # nesting is at most 2 deep in practice
        if "\x00LINK" not in s:
            break
        expanded = re.sub(r"\x00LINK(\d+)\x00",
                          lambda m: toks[int(m.group(1))] if int(m.group(1)) < len(toks) else "",
                          s)
        if expanded == s:
            break
        s = expanded
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
    """GFM table: if line 2 is a separator row, line 1 is the header."""
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
        # overview: the average row is emitted as an ordinary row; the radar JS excludes it via the "average/avg" text
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


def fence_html(lang, code, ui="en"):
    if lang == "mermaid":
        return ('<figure class="arch"><div class="arch-src" hidden>%s</div>'
                '<div class="arch-out" role="img"></div>'
                '<figcaption class="arch-note">%s</figcaption></figure>'
                % (esc(code.strip()), esc(ui_string(ui, "arch_note"))))
    return '<pre class="code"><code>%s</code></pre>' % esc(code.rstrip())


def heading(line, role):
    m = re.match(r"^(#{1,4})\s+(.*)$", line)
    level = len(m.group(1))
    text = m.group(2).strip()
    if level == 1:
        return ("h1", "<h1>%s</h1>" % inline(text))
    if level == 2:
        return ("h2", None)  # h2 headings are consumed by the caller's section slicing (section_html emits them uniformly)
    if level == 3:
        if role == "adr" and re.match(r"adr", text, re.I):
            return ("adr", None)
        return ("h3", '<h3 class="sub-h3">%s</h3>' % inline(text))
    return ("h4", "<h4>%s</h4>" % inline(text))


def parse_meta(lines):
    chips, i = [], 0
    while i < len(lines) and not lines[i].strip():
        i += 1  # tolerate blank lines between the title and the metadata
    while i < len(lines):
        m = re.match(r"^\s*-\s*\*\*([^*]+?)\s*[：:]\s*\*\*\s*(.*)$", lines[i])
        if not m:
            break
        chips.append('<span class="chip">%s %s</span>'
                     % (esc(m.group(1)), inline(m.group(2))))
        i += 1
    return "".join(chips), lines[i:]


def blocks(lines, role, ui="en"):
    """Render section body lines as HTML (without the surrounding <section>)."""
    # Precondition: the caller must have split sections by h2 first; inside ADR
    # sections, the '### ADR-...' entry headers are stripped by the caller.
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
            i += 1  # skip the closing fence
            out.append(fence_html(lang, "\n".join(buf), ui))
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


# ---------- section assembly and document rendering ----------

def slugify(s):
    s = strip_heading_no(s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w\-]+", "", s, flags=re.UNICODE)
    return s or "sec"


_NO_RE = re.compile(r"^\s*\d+(\.\d+)*[\.、]?\s*")


def strip_heading_no(s):
    """Strip the leading number of an h2 heading (formats like '3. ', '1.2 ', or '3' plus an ideographic comma); shared by role matching and slugging."""
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
    """Split lines into chunks at '### ADR-n:' headings (the prefix_re regex).
    Returns [(title|None, body-lines)]; a None title means leading content
    before the first entry (must be kept, never dropped)."""
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


_SEPARATOR_ROW_RE = re.compile(r"^\|[\s:|-]+\|$")
_SCORE_CELL_RE = re.compile(r"^\**\s*\d+(?:\.\d+)?\s*\**$")
_SCORE_HEADER_RE = re.compile(r"score|评分|分值|得分|0\s*[-~～]\s*5", re.I)


def looks_like_score_table(lines):
    """True when the section holds a score table: either three or more rows whose
    second column is a number, or a header that names a score column (a review may
    legitimately evaluate only one or two dimensions). The Overview role has side
    effects (radar wrapper + `table.tbl-scores`), so an unrelated table under an
    "Overview" heading must not silently become a radar page."""
    rows = [ln.strip() for ln in lines if ln.lstrip().startswith("|")]
    if len(rows) < 2:
        return False
    if _SCORE_HEADER_RE.search(rows[0]):
        return True
    if len(rows) < 4:
        return False
    sep = next((i for i, ln in enumerate(rows) if _SEPARATOR_ROW_RE.match(ln)), None)
    body = rows[sep + 1:] if sep is not None else rows
    numeric = 0
    for ln in body:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 2 and _SCORE_CELL_RE.match(cells[1]):
            numeric += 1
    return numeric >= 3


def section_html(title, lines, forced_id=None, ui="en"):
    role = role_of(title)
    if role == "overview" and not looks_like_score_table(lines):
        role = "generic"   # an "Overview" heading without scores must not claim the radar
    tgl = ('<h2 class="sec-title"><span>%s</span>'
           '<button class="tgl" type="button" aria-label="%s" '
           'aria-expanded="true">↕</button></h2>' % (inline(title), esc(ui_string(ui, "tgl"))))
    if role == "adr":
        body = ""
        for t, blk in split_h3(lines, re.compile(r"^###\s+adr", re.I)):
            if t is None:
                body += blocks(blk, "adr", ui)
            else:
                body += ('<details class="adr"><summary>%s</summary>'
                         '<div class="adr-body">%s</div></details>'
                         % (inline(re.sub(r"^###\s+", "", t).strip()), blocks(blk, "adr", ui)))
    else:
        body = blocks(lines, role, ui)
        if role == "overview":
            body = ('<div class="radar-wrap" role="img" aria-label="%s"></div>'
                    % esc(ui_string(ui, "radar"))) + body
    sid = forced_id or slugify(title)
    return ('<section class="sec %s" id="%s">%s<div class="sec-body">%s</div></section>'
            % (role, sid, tgl, body))


def set_html_lang(shell, lang):
    """Point the shell at the document language (drives every menu label and the
    CJK webfont). Fails loudly when the shell loses its <html> tag."""
    loc = LOCALES.get(lang, "en")

    def repl(m):
        tag = m.group(0)
        if _LANG_ATTR_RE.search(tag):
            tag = _LANG_ATTR_RE.sub('lang="%s"' % loc, tag, count=1)
        else:                                  # attribute missing entirely
            tag = re.sub(r"<html\b", '<html lang="%s"' % loc, tag, count=1, flags=re.I)
        if _DATA_LANG_ATTR_RE.search(tag):
            tag = _DATA_LANG_ATTR_RE.sub('data-lang="%s"' % lang, tag, count=1)
        else:
            tag = tag[:-1] + ' data-lang="%s">' % lang
        return tag

    new, n = _HTML_TAG_RE.subn(repl, shell, count=1)
    if n != 1:
        raise ValueError("report-shell.html is missing its <html> tag")
    tag = _HTML_TAG_RE.search(new).group(0)
    if not _LANG_ATTR_RE.search(tag) or _LANG_ATTR_RE.search(tag).group(0) != 'lang="%s"' % loc:
        raise ValueError("failed to set lang on <html>")
    if not _DATA_LANG_ATTR_RE.search(tag) or _DATA_LANG_ATTR_RE.search(tag).group(0) != 'data-lang="%s"' % lang:
        raise ValueError("failed to set data-lang on <html>")
    return new


def localize_shell(shell, lang):
    """Rewrite the shell's static UI literals for the target language and make
    sure the shell still contains them (drift between shell and generator must
    fail loudly, never degrade into a half-translated artifact)."""
    missing = [src for src, _ in SHELL_LITERALS if src not in shell]
    if missing:
        raise ValueError("report-shell.html no longer contains %s; sync SHELL_LITERALS in md2html.py"
                         % ", ".join(missing))
    if lang == "en":
        return shell
    for src, dst in SHELL_LITERALS:
        shell = shell.replace(src, dst)
    return shell


def render_document(title, meta, body, lang="en"):
    shell = Path(__file__).with_name("report-shell.html").read_text(encoding="utf-8")
    shell = localize_shell(set_html_lang(shell, lang), lang)
    return (shell.replace("<!--T:TITLE-->", title)
                 .replace("<!--T:META-->", meta)
                 .replace("<!--T:BODY-->", body)
                 .replace("<!--T:EXTRA-->", ""))


def render_document_from_md(md_text, lang=None):
    """Render a draft. `lang` (en|zh) forces the document language; when omitted
    it is detected from the draft text so body and menu always agree."""
    ui = lang or detect_lang(md_text)
    if ui not in LANG_STRINGS:
        raise ValueError("unsupported language: %r (use en or zh)" % ui)
    lines = md_text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Draft must start with '# Title'")
    title = lines[0][2:].strip()
    meta, rest = parse_meta(lines[1:])
    parts, sec_lines = [], []
    used = set()

    def flush():
        if not sec_lines:
            return
        if sec_lines[0].startswith("## "):
            title = sec_lines[0][3:].strip()
            parts.append(section_html(title, sec_lines[1:], unique_slug(title, used), ui))
        else:  # foreword lines before the first '## ' section
            parts.append(blocks(sec_lines, "generic", ui))
        sec_lines.clear()

    for ln in rest:
        if ln.startswith("## ") and sec_lines:
            flush()
        sec_lines.append(ln)
    flush()
    return render_document(esc(title), meta, "\n".join(parts), ui)


def main():
    ap = argparse.ArgumentParser(description="Restricted Markdown → spec HTML (reads report-shell.html next to this script)")
    ap.add_argument("src", type=Path, help=".md draft path")
    ap.add_argument("out", type=Path, help="output .html path")
    ap.add_argument("--lang", choices=["en", "zh"], default=None,
                    help="document/UI language (default: detect from the draft)")
    ap.add_argument("--keep-src", action="store_true", help="keep the draft (default: delete the draft after a successful conversion)")
    a = ap.parse_args()
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        if a.out.resolve() == a.src.resolve():
            raise ValueError("Output path equals the source path; aborted (it would destroy the draft)")
        shell = Path(__file__).with_name("report-shell.html")
        if not shell.exists():
            raise FileNotFoundError("Missing %s (report-shell.html must sit next to md2html.py)" % shell)
        out_html = render_document_from_md(a.src.read_text(encoding="utf-8"), a.lang)
        a.out.write_text(out_html, encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print("Conversion failed: %s" % e, file=sys.stderr)
        sys.exit(1)
    if not a.keep_src:
        try:
            a.src.unlink()
        except OSError as e:
            print("Note: failed to remove the draft (ignorable): %s" % e, file=sys.stderr)
    print("OK -> %s" % a.out)


if __name__ == "__main__":
    main()
