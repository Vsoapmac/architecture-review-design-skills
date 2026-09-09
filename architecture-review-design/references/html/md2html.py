# -*- coding: utf-8 -*-
"""md2html.py - restricted Markdown → spec HTML converter (Tier 1, pure stdlib).

Usage:
    python md2html.py <draft.md> <output.html> [--keep-src]
    By default the draft is deleted after a successful conversion; pass
    --keep-src to keep it.

Reads report-shell.html next to this script and substitutes the
<!--T:TITLE--> / <!--T:META--> / <!--T:BODY--> tokens to assemble the final
single-file HTML.

Dialect: ATX headings h1-h4, GFM tables, flat unordered/ordered lists, fenced
code blocks (a mermaid fence is special-cased as figure.arch), block quotes
(>), bold/italic/inline code/links, hr. Any other syntax is HTML-escaped into
plain text (style lost, content kept).
Section→component mapping: see html-output-spec.md §4 (the template is the contract).
"""
import argparse
import sys
import html as _html
import re
from pathlib import Path

DESIGN_ROLES = {
    "Architecture Overview": "arch-sec",
    "ADR Records": "adr",
    "8-Dimension Self-Check": "selftest",
    "Evolution Roadmap": "roadmap",
}
REVIEW_ROLES = {"Overview": "overview"}
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

# URLs may nest one level of parentheses ([x](a(b))), with no whitespace; deeper nesting falls back to plain text for the whole link
_LINK_RE = re.compile(r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))*)\)")


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
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", u)
    if not m:
        return u  # no scheme: relative/bare path
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


def fence_html(lang, code):
    if lang == "mermaid":
        return ('<figure class="arch"><div class="arch-src" hidden>%s</div>'
                '<div class="arch-out" role="img"></div>'
                '<figcaption class="arch-note">The diagram renders when online; the source is embedded below for copying.</figcaption></figure>'
                % esc(code.strip()))
    return '<pre class="code"><code>%s</code></pre>' % esc(code.rstrip())


def heading(line, role):
    m = re.match(r"^(#{1,4})\s+(.*)$", line)
    level = len(m.group(1))
    text = m.group(2).strip()
    if level == 1:
        return ("h1", "<h1>%s</h1>" % inline(text))
    if level == 2:
        return ("h2", None)  # h2 headings are consumed by the caller's section slicing (section_html emits them uniformly; added in task 4)
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


def blocks(lines, role):
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


def section_html(title, lines, forced_id=None):
    role = role_of(title)
    tgl = ('<h2 class="sec-title"><span>%s</span>'
           '<button class="tgl" type="button" aria-label="Toggle section" '
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
            parts.append(section_html(title, sec_lines[1:], unique_slug(title, used)))
        else:  # foreword lines before the first '## ' section
            parts.append(blocks(sec_lines, "generic"))
        sec_lines.clear()
    for ln in rest:
        if ln.startswith("## ") and sec_lines:
            flush()
        sec_lines.append(ln)
    flush()
    return render_document(esc(title), meta, "\n".join(parts))


def main():
    ap = argparse.ArgumentParser(description="Restricted Markdown → spec HTML (reads report-shell.html next to this script)")
    ap.add_argument("src", type=Path, help=".md draft path")
    ap.add_argument("out", type=Path, help="output .html path")
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
        out_html = render_document_from_md(a.src.read_text(encoding="utf-8"))
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
