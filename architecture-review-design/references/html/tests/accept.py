# -*- coding: utf-8 -*-
"""End-to-end acceptance: verify rendered output against content assertions and
consistency with the existing artifacts (golden files).

Run: python accept.py            (from references/html/tests; paths normalized via __file__)
     python accept.py --write    (explicitly refresh the sample artifacts covered by the assertions)

On failure the artifacts under test are never rewritten; --write only persists
after every content assertion passes. When existing artifacts diverge from a
fresh render, non--write mode fails without rewriting; with --write, once the
content assertions (anchors/tokens) pass, the stale artifact is refreshed to
the current render.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import md2html as M

# Anchored attribute shapes, so plain shell CSS/JS text cannot satisfy them
NEEDLES = {
    "sample-design": ['<section class="sec arch-sec"', '<figure class="arch">',
                      '<div class="arch-src"', "ADR-2", '<details class="adr">',
                      '<span class="chip chip-warn"', '<table class="tbl">',
                      "Evolution Roadmap"],
    "sample-review": ['<section class="sec overview"', '<table class="tbl tbl-scores">',
                      '<div class="radar-wrap">', '<span class="chip chip-red"',
                      '<span class="chip chip-yellow"', "Remediation Roadmap"],
}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    write_mode = "--write" in sys.argv
    ok = True
    for stem, needles in NEEDLES.items():
        md, out = HERE / (stem + ".md"), HERE / (stem + ".html")
        text = M.render_document_from_md(md.read_text(encoding="utf-8"))
        bad = [k for k in needles if k not in text]
        if "<!--T:" in text:
            bad.append("residual token <!--T:")
        stale = out.exists() and out.read_text(encoding="utf-8") != text
        if stale and not write_mode:
            bad.append("out of sync with existing artifact (pass --write to refresh)")
        # Persist only when the content assertions pass: generate the artifact
        # when it is missing; with --write, refresh the stale golden file.
        if not bad and (not out.exists() or (write_mode and stale)):
            out.write_text(text, encoding="utf-8")
        print(stem + ".html", "PASS" if not bad else "FAIL " + str(bad))
        ok = ok and not bad
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # missing sample / invalid source etc.: keep the script's own 0/1 contract, no bare traceback
        print("Acceptance failed: %s" % e, file=sys.stderr)
        sys.exit(1)
