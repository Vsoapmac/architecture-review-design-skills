# -*- coding: utf-8 -*-
"""check_views.py - validate the architecture views of a Markdown draft.

Implements the structural rules of mermaid-spec.md §1-§8 as a runnable gate, so
"the views must agree" is a check instead of a good intention.

Usage:
    python check_views.py <draft.md> [--quiet]

Exit codes: 0 = no errors (warnings may exist), 1 = errors found, 2 = usage/IO error.

Checks (ERROR unless marked WARN):
  1. All five mandatory views exist (context, component, layered, runtime, data
     flow) or one line explains per view why it is merged/not applicable.
  2. The layered view's node set equals the component view's node set.
  3. Every `Ext:` node of any view appears in the system context view.
  4. Every store of the data flow view exists in the component view.
  5. Stores are alive: in component/layered views (dependency direction) a store
     needs at least one inbound edge; in the data flow view (data movement) it
     needs both an inbound and an outbound edge.
  6. Data flow and swimlane edges carry a data/artifact name (a swimlane is
     optional — on request only — but is validated like any other view when drawn).
  7. The runtime view shows at least one failure branch (alt/else/opt/Note).
  8. subgraph/end balance, node cap (15 per diagram), and — when a swimlane is
     drawn — its lane cap (6) and numbered steps (WARN); every diagram has a
     "read this for" note (WARN).
"""
import argparse
import re
import sys
from pathlib import Path

ERROR, WARN = "ERROR", "WARN"

MANDATORY = ["context", "component", "layered", "runtime", "dataflow"]
VIEW_LABEL = {
    "context": "System context", "component": "Component view", "layered": "Layered view",
    "runtime": "Runtime view", "dataflow": "Data flow view", "swimlane": "Swimlane view",
    "deployment": "Deployment view", "state": "State machine", "erd": "Data model (ERD)",
}
# Longest/most specific first: "分层架构图" must classify as layered, not component.
VIEW_KEYWORDS = [
    ("context", [r"system context", r"context view", r"上下文"]),
    ("dataflow", [r"data\s*flow", r"\bdfd\b", r"数据流"]),
    ("runtime", [r"runtime view", r"sequence", r"运行时", r"时序", r"key flow", r"关键流程"]),
    ("layered", [r"layered", r"分层"]),
    ("component", [r"component view", r"container view", r"architecture diagram", r"组件视图",
                   r"组件图", r"架构图"]),
    ("deployment", [r"deployment", r"部署"]),
    ("swimlane", [r"swimlane", r"泳道"]),
    ("state", [r"state machine", r"state diagram", r"状态机"]),
    ("erd", [r"\berd\b", r"data model", r"数据模型"]),
]
EXCUSE = [r"不适用", r"不涉及", r"not applicable", r"\bn/?a\b", r"合并", r"merged because", r"merged into"]
NOTE_WORDS = [r"看图重点", r"read this for", r"reading focus"]
ARROW_RE = re.compile(r"(?:-\.-+>|={2,3}>|-{2,3}>|--[ox]|~~~|-{2,3})")
FENCE_RE = re.compile(r"^\s*```(\w*)\s*$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
CLASS_RE = re.compile(r":::[\w\-]+")
DIAGRAM_TYPE_RE = re.compile(r"^(flowchart|graph|sequenceDiagram|stateDiagram(-v2)?|erDiagram|"
                             r"classDiagram|journey|gantt|pie|mindmap|timeline|block-beta|C4\w*)\b", re.I)
SHAPES = [("[(", ")]"), ("([", "])"), ("[[", "]]"), ("{{", "}}"),
          ("[", "]"), ("(", ")"), ("{", "}")]
SEQ_FAIL_BRANCH = re.compile(r"^\s*(alt|else|opt|par|critical|break)\b|^\s*Note\b", re.I)


def strip_quotes(s):
    s = (s or "").strip()
    if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
        return s[1:-1].strip()
    return s


def label_of(rest):
    rest = CLASS_RE.sub("", rest or "").strip()
    for op, cl in sorted(SHAPES, key=lambda kv: -len(kv[0])):
        if rest.startswith(op) and rest.endswith(cl) and len(rest) > len(op) + len(cl) - 1:
            return strip_quotes(rest[len(op):-len(cl)])
    return strip_quotes(rest)


def shape_of(rest):
    rest = CLASS_RE.sub("", rest or "").strip()
    for op, _ in sorted(SHAPES, key=lambda kv: -len(kv[0])):
        if rest.startswith(op):
            return op
    return ""


def is_external(label):
    l = (label or "").strip().lower()
    return l.startswith("ext:") or l.startswith("ext：") or l.startswith("外部")


def is_store(shape):
    return shape in ("[(", "{{")


def classify(heading):
    h = (heading or "").lower()
    for view, patterns in VIEW_KEYWORDS:
        for p in patterns:
            if re.search(p, h):
                return view
    return None


# ---------- document parsing ----------

def parse_sections(text):
    """Split into sections: [{level, title, line, lines}] (lines exclude the heading)."""
    sections, cur = [], None
    for i, ln in enumerate(text.splitlines(), 1):
        m = HEAD_RE.match(ln)
        if m:
            cur = {"level": len(m.group(1)), "title": m.group(2).strip(), "line": i, "lines": []}
            sections.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)
    return sections


def parse_diagrams(sections):
    """Every mermaid fence with its heading and the surrounding prose."""
    out = []
    for sec in sections:
        lines = sec["lines"]
        prose = "\n".join(lines)
        i = 0
        while i < len(lines):
            m = FENCE_RE.match(lines[i])
            if m and m.group(1) == "mermaid":
                start = i + 1
                buf = []
                i += 1
                while i < len(lines) and not FENCE_RE.match(lines[i]):
                    buf.append(lines[i])
                    i += 1
                out.append({"heading": sec["title"], "heading_line": sec["line"],
                            "code": "\n".join(buf), "prose": prose,
                            "line": sec["line"] + start})
            i += 1
    return out


def parse_flowchart(code):
    nodes, edges, subs, stack = {}, [], [], []
    for i, raw in enumerate(code.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        if DIAGRAM_TYPE_RE.match(line):
            continue
        if re.match(r"^(classDef|class|style|linkStyle|click|direction)\b", line):
            continue
        m = re.match(r"^subgraph\s+(.*)$", line)
        if m:
            spec = m.group(1).strip()
            mm = re.match(r'^([A-Za-z_][\w\-]*)\s*(.*)$', spec)
            sid = mm.group(1) if mm else spec
            sg = {"id": sid, "label": label_of(mm.group(2)) if mm and mm.group(2) else spec,
                  "line": i, "members": []}
            subs.append(sg)
            stack.append(sg)
            continue
        if line == "end":
            if stack:
                stack.pop()
            continue

        def record(part):
            part = part.strip()
            if not part or part in ("&",):
                return None
            mm = re.match(r"^([A-Za-z_][\w\-]*)\s*(.*)$", part)
            if not mm:
                return None
            nid, rest = mm.group(1), mm.group(2).strip()
            if rest.startswith(":::"):
                rest = CLASS_RE.sub("", rest).strip()
            if nid not in nodes:
                nodes[nid] = {"id": nid, "label": "", "shape": "", "line": i, "subgraph": None}
            node = nodes[nid]
            if rest:
                node["label"] = label_of(rest) or node["label"]
                node["shape"] = shape_of(rest) or node["shape"]
            if stack and node["subgraph"] is None:
                node["subgraph"] = stack[-1]["id"]
                stack[-1]["members"].append(nid)
            return nid

        clean = re.sub(r"\|[^|]*\|", " ", line)          # drop edge labels before splitting
        parts = ARROW_RE.split(clean)
        if len(parts) > 1:
            ids = [record(p) for p in parts]
            ids = [x for x in ids if x]
            for a, b in zip(ids, ids[1:]):
                lab = ""
                lm = re.search(r"\|([^|]*)\|", line)
                if lm:
                    lab = strip_quotes(lm.group(1))
                edges.append({"src": a, "dst": b, "label": lab, "line": i})
        else:
            record(line)
    return {"nodes": nodes, "edges": edges, "subgraphs": subs,
            "subgraph_balance": len(stack)}


def parse_sequence(code):
    participants, messages, failure = {}, [], False
    for i, raw in enumerate(code.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        m = re.match(r"^participant\s+([\w\-]+)(?:\s+as\s+(.*))?$", line, re.I)
        if m:
            participants[m.group(1)] = strip_quotes(m.group(2) or m.group(1))
            continue
        if SEQ_FAIL_BRANCH.match(line):
            failure = True
            continue
        m = re.match(r"^([\w\-]+)\s*(-{1,2}[)>x]|--?>>|-\))\s*([\w\-]+)\s*:(.*)$", line)
        if m:
            messages.append({"src": m.group(1), "dst": m.group(3),
                             "label": m.group(4).strip(), "line": i,
                             "async": "-)" in m.group(2) or "-->>" in m.group(2)})
    return {"participants": participants, "messages": messages, "failure": failure}


def parse_plain(code, pattern):
    return [m.group(1) for m in (re.match(pattern, ln.strip()) for ln in code.splitlines()) if m]


# ---------- checks ----------

def mentions(line, view):
    h = (line or "").lower()
    return any(re.search(p, h) for p in dict(VIEW_KEYWORDS)[view])


def excused(text, view):
    """A one-line 'merged because / not applicable' note that mentions this view.
    The note may sit on the heading line or on one of the two lines after it."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if not mentions(ln, view):
            continue
        window = " ".join(lines[i:i + 3]).lower()
        if any(re.search(p, window) for p in EXCUSE):
            return True
    return False


def check(text):
    findings = []
    sections = parse_sections(text)
    diagrams = parse_diagrams(sections)
    views = {}
    for d in diagrams:
        v = classify(d["heading"])
        if v:
            views.setdefault(v, []).append(d)

    def add(level, msg):
        findings.append((level, msg))

    # 1. mandatory presence
    for v in MANDATORY:
        if v not in views and not excused(text, v):
            add(ERROR, "missing mandatory view: %s (draw it, or add a one-line "
                       "'merged because / not applicable' note next to its heading)" % VIEW_LABEL[v])

    # parse every diagram once
    parsed = {}
    for v, items in views.items():
        for d in items:
            code = d["code"]
            if v in ("context", "component", "layered", "dataflow", "swimlane", "deployment"):
                parsed[(v, d["line"])] = parse_flowchart(code)
            elif v == "runtime":
                parsed[(v, d["line"])] = parse_sequence(code)
            else:
                parsed[(v, d["line"])] = {"raw": code}

    # 2. layered node set == component node set
    comp = next((parsed[k] for k in parsed if k[0] == "component"), None)
    lay = next((parsed[k] for k in parsed if k[0] == "layered"), None)
    if comp and lay:
        c, l = set(comp["nodes"]), set(lay["nodes"])
        for nid in sorted(l - c):
            add(ERROR, "layered view has node '%s' that the component view does not define "
                       "(the layered view must arrange the same nodes)" % nid)
        for nid in sorted(c - l):
            add(ERROR, "component node '%s' is missing from the layered view "
                       "(every component must sit in a layer or the external band)" % nid)

    # 3. externals defined once, in the context view
    ctx = next((parsed[k] for k in parsed if k[0] == "context"), None)
    ctx_ext = {n for n, d in (ctx["nodes"].items() if ctx else []) if is_external(d["label"])}
    ctx_nodes = set(ctx["nodes"]) if ctx else set()
    for (v, line), data in parsed.items():
        for nid, node in data.get("nodes", {}).items():
            if is_external(node["label"]) or is_external(nid):
                if ctx and nid not in ctx_nodes:
                    add(ERROR, "%s view defines external '%s' (%s) that is missing from the "
                               "system context view" % (VIEW_LABEL[v], nid, node["label"]))

    # 4/5. stores exist in the component view and are actually used
    comp_stores = {n for n, d in (comp["nodes"].items() if comp else []) if is_store(d["shape"])}
    for (v, line), data in parsed.items():
        for nid, node in data.get("nodes", {}).items():
            if is_store(node["shape"]) and v == "dataflow" and comp and nid not in comp["nodes"]:
                add(ERROR, "data flow view uses store '%s' that the component view does not "
                           "define" % nid)
    if comp:
        inbound = {e["dst"] for e in comp["edges"]}
        for nid in sorted(comp_stores):
            if nid not in inbound:
                add(ERROR, "store '%s' has no inbound edge in the component view "
                           "(no module depends on or writes it)" % nid)
    for (v, line), data in parsed.items():
        if v != "dataflow":
            continue
        inbound = {e["dst"] for e in data["edges"]}
        outbound = {e["src"] for e in data["edges"]}
        for nid, node in data["nodes"].items():
            if not is_store(node["shape"]):
                continue
            if nid not in inbound:
                add(ERROR, "data flow view: store '%s' is never written" % nid)
            if nid not in outbound:
                add(ERROR, "data flow view: store '%s' is never read" % nid)

    # 6. labeled edges where the data matters
    for (v, line), data in parsed.items():
        if v in ("dataflow", "swimlane"):
            for e in data.get("edges", []):
                if not e["label"]:
                    add(ERROR, "%s view line %d: edge %s -> %s has no %s label"
                        % (VIEW_LABEL[v], e["line"], e["src"], e["dst"],
                           "data" if v == "dataflow" else "hand-off artifact"))

    # 7. runtime view shows a failure branch
    for (v, line), data in parsed.items():
        if v == "runtime" and not data.get("failure"):
            add(ERROR, "runtime view (heading line %d) has no failure branch: add an "
                       "alt/else/opt block or a Note covering timeout/retry/compensation" % line)

    # 8. structural hygiene
    for (v, line), data in parsed.items():
        if "nodes" in data:
            if data["subgraph_balance"]:
                add(ERROR, "%s view: %d subgraph block(s) are not closed with 'end'"
                    % (VIEW_LABEL[v], data["subgraph_balance"]))
            if len(data["nodes"]) > 15:
                add(ERROR, "%s view has %d nodes (max 15 per diagram, see mermaid-spec §7)"
                    % (VIEW_LABEL[v], len(data["nodes"])))
            if v == "swimlane":
                lanes = [s for s in data["subgraphs"]]
                if len(lanes) < 2:
                    add(ERROR, "swimlane view needs at least two lanes (subgraphs)")
                if len(lanes) > 6:
                    add(ERROR, "swimlane view has %d lanes (max 6)" % len(lanes))
                for nid, node in data["nodes"].items():
                    if node["label"] and not re.match(r"^\s*\d", node["label"]):
                        add(WARN, "swimlane step '%s' (%s) is not numbered in its label"
                            % (nid, node["label"]))
    for v, items in views.items():
        for d in items:
            if not any(re.search(p, d["prose"], re.I) for p in NOTE_WORDS):
                add(WARN, "%s: no 'read this for' line above the diagram (line %d)"
                    % (VIEW_LABEL[v], d["line"]))
    return findings, views


def main():
    ap = argparse.ArgumentParser(description="Validate the architecture views of a .md draft")
    ap.add_argument("src", type=Path, help=".md draft path")
    ap.add_argument("--quiet", action="store_true", help="print only the summary line")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        text = a.src.read_text(encoding="utf-8")
    except OSError as e:
        print("Cannot read %s: %s" % (a.src, e), file=sys.stderr)
        return 2
    findings, views = check(text)
    errors = [f for f in findings if f[0] == ERROR]
    warns = [f for f in findings if f[0] == WARN]
    if not a.quiet:
        for level, msg in findings:
            print("%-5s %s" % (level, msg))
    found = ", ".join(sorted(views)) or "none"
    print("views: %s" % found)
    print("check_views: %s (%d error(s), %d warning(s))"
          % ("FAIL" if errors else "PASS", len(errors), len(warns)))
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                      # keep the 0/1/2 contract, no bare traceback
        print("check_views crashed: %s" % e, file=sys.stderr)
        sys.exit(2)
