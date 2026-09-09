# -*- coding: utf-8 -*-
"""md2html unit tests. Run: python tests/test_md2html.py -v (working dir references/html)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import md2html as M

class TestInline(unittest.TestCase):
    def test_bold_italic_code(self):
        self.assertEqual(M.inline("**a** *b* `c()` x"),
                         "<strong>a</strong> <em>b</em> <code>c()</code> x")
    def test_link(self):
        self.assertEqual(M.inline("[doc](../specs/x.md)"), '<a href="../specs/x.md">doc</a>')
    def test_escape_html(self):
        self.assertEqual(M.inline("a<b>&c"), "a&lt;b&gt;&amp;c")
    def test_no_double_escape(self):
        self.assertEqual(M.inline("`<b>`"), "<code>&lt;b&gt;</code>")
    def test_link_url_with_asterisk(self):
        self.assertEqual(M.inline("[x](http://a*b*c)"),
                         '<a href="http://a*b*c">x</a>')
    def test_bold_inside_link_text(self):
        self.assertEqual(M.inline("[**b**](u)"),
                         '<a href="u"><strong>b</strong></a>')
    def test_javascript_url_rejected(self):
        self.assertEqual(M.inline("[click me](javascript:alert(1))"), "click me")
    def test_data_url_rejected(self):
        self.assertEqual(M.inline("[x](data:text/html,hi)"), "x")
    def test_mixed_case_scheme_rejected(self):
        self.assertEqual(M.inline("[x](JaVaScRiPt:alert(1))"), "x")
    def test_anchor_allowed(self):
        self.assertIn('<a href="#sec-1">jump</a>', M.inline("[jump](#sec-1)"))
    def test_relative_allowed(self):
        self.assertIn('<a href="../specs/x.md">doc</a>', M.inline("[doc](../specs/x.md)"))
    def test_entity_obfuscated_scheme_inert(self):
        out = M.inline("[x](javascript&colon;alert(1))")
        self.assertIn("&amp;colon;", out)
        self.assertNotIn('href="javascript:', out)
    def test_mailto_allowed(self):
        self.assertIn('<a href="mailto:a@b.c">x</a>', M.inline("[x](mailto:a@b.c)"))
    def test_rejected_label_with_bold(self):
        self.assertEqual(M.inline("[**danger**](javascript:alert(1))"),
                         "<strong>danger</strong>")

class TestChip(unittest.TestCase):
    def test_line_start(self):
        self.assertEqual(M.chipify("🔴 Fix now"),
                         '<span class="chip chip-red">🔴 Fix now</span>')
    def test_not_middle(self):
        self.assertIsNone(M.chipify("text with a 🔴 marker in the middle"))
    def test_meta_malformed_line_not_lost(self):
        # The malformed line must sit after a valid chip line: extraction stops
        # at the first miss, and the malformed line survives verbatim in `rest`.
        html, rest = M.parse_meta(["- **Date：** 2026-01-01", "- **No colon field**"])
        self.assertIn("2026-01-01", html)
        self.assertEqual(rest, ["- **No colon field**"])

class TestBlocks(unittest.TestCase):
    def test_paragraphs(self):
        html = M.blocks("First paragraph\n\nSecond paragraph", "generic")
        self.assertEqual(html.count("<p>"), 2)
    def test_ul_li_with_chip(self):
        html = M.blocks("- 🔴 Issue A\n- Normal item", "generic")
        self.assertIn("chip-red", html)
        self.assertIn("<li>Normal item</li>", html)
    def test_ol(self):
        self.assertIn("<ol>", M.blocks("1. One\n2. Two", "generic"))
    def test_blockquote(self):
        self.assertIn('class="ev"', M.blocks("> Evidence", "generic"))
    def test_plain_fence(self):
        html = M.blocks("```python\nprint(1)\n```", "generic")
        self.assertIn('class="code"', html)
        self.assertIn("print(1)", html)
    def test_mermaid_fence_arch(self):
        html = M.blocks("```mermaid\ngraph LR; A-->B\n```", "generic")
        self.assertIn('class="arch"', html)
        self.assertIn("arch-src", html)
    def test_table(self):
        html = M.blocks("| Module | Responsibility |\n|---|---|\n| a | b |", "generic")
        self.assertIn('<table class="tbl">', html)
        self.assertIn("<th>Module</th>", html)
        self.assertIn("<td>a</td>", html)
    def test_hr(self):
        self.assertIn("<hr>", M.blocks("---", "generic"))
    def test_blockquote_keeps_content(self):
        html = M.blocks("> evidence one\n> evidence two", "generic")
        self.assertIn("evidence one", html)
        self.assertIn("evidence two", html)
    def test_crlf_input(self):
        html = M.blocks("line one\r\nline two", "generic")
        self.assertIn("line one", html)
        self.assertIn("line two", html)

class TestSection(unittest.TestCase):
    def test_role_detect(self):
        self.assertEqual(M.role_of("1. Architecture Overview"), "arch-sec")
        self.assertEqual(M.role_of("6. ADR Records"), "adr")
        self.assertEqual(M.role_of("7. 8-Dimension Self-Check"), "selftest")
        self.assertEqual(M.role_of("8. Evolution Roadmap"), "roadmap")
        self.assertEqual(M.role_of("1. Overview (8-Dimension Radar)"), "overview")
        self.assertEqual(M.role_of("unknown title"), "generic")
        self.assertEqual(M.role_of("4. Module List & Responsibilities"), "generic")
    def test_cells(self):
        self.assertEqual(M.cell_html("✅"),
                         '<span class="chip chip-ok">✅</span>')
        self.assertEqual(M.cell_html("⚠️ risk"),
                         '<span class="chip chip-warn">⚠️ risk</span>')
    def test_meta_parse(self):
        html, rest = M.parse_meta(["- **Date:** 2026-01-01", "", "# title"])
        self.assertIn("2026-01-01", html)
        self.assertEqual(rest[1], "# title")
    def test_cells_five_marks(self):
        self.assertEqual(M.cell_html("🔴 risk"),
                         '<span class="chip chip-red">🔴 risk</span>')
        self.assertEqual(M.cell_html("⚪ info"),
                         '<span class="chip chip-gray">⚪ info</span>')
        self.assertEqual(M.cell_html("✅ / ⚠️ mixed"),
                         '<span class="chip chip-warn">✅ / ⚠️ mixed</span>')
    def test_adr_h3_generic_not_swallowed(self):
        html = M.blocks("### ADR-9: Stray entry\nContent", "generic")
        self.assertIn("sub-h3", html)
        self.assertIn("ADR-9", html)
    def test_adr_h3_swallowed_in_adr_role(self):
        html = M.blocks("### ADR-1: Chosen title\nContent", "adr")
        self.assertNotIn("sub-h3", html)
    def test_selftest_table_integration(self):
        html = M.blocks("| Dimension | Status |\n|---|---|\n| 1. Functional Correctness | 🔴 Risk |", "selftest")
        self.assertIn("chip-red", html)
    def test_overview_table_class_and_avg(self):
        html = M.blocks("| Dimension | Score (0-5) |\n|---|---|\n| 1. Functional Correctness | 4 |\n| **Average** | **3.0** |", "overview")
        self.assertIn("tbl-scores", html)
        self.assertIn("Average", html)
    def test_meta_parse_leading_blank(self):
        html, rest = M.parse_meta(["", "- **Date：** 2026-01-01", "", "Body text"])
        self.assertIn("2026-01-01", html)
        self.assertEqual(rest[0], "")
        self.assertEqual(rest[1], "Body text")
    def test_roadmap_table_wrapped(self):
        html = M.blocks("| Stage | Scope |\n|---|---|\n| MVP | Vertical slice |", "roadmap")
        self.assertIn('class="roadmap"', html)
    def test_slug_nested_number(self):
        self.assertEqual(M.slugify("1.2 Sub module"), "Sub-module")
    def test_dim_h3_in_review(self):
        html = M.blocks("### Dimension 4: Observability — Score 2/5\nContent", "generic")
        self.assertIn("sub-h3", html)
        self.assertIn("Observability", html)

class TestAssemble(unittest.TestCase):
    def test_section_roles(self):
        sec = M.section_html("3. Architecture Overview", ["```mermaid", "graph LR; A-->B", "```"])
        self.assertIn("arch-sec", sec)
        self.assertIn('<h2 class="sec-title">', sec)
        self.assertIn('<div class="sec-body">', sec)
        sec2 = M.section_html("6. ADR Records",
                              ["### ADR-1: Event-driven calls", "Reason x", "### ADR-2: Database choice", "Reason y"])
        self.assertEqual(sec2.count("<details"), 2)
        self.assertIn("ADR-2", sec2)
        self.assertIn("<summary>", sec2)
    def test_overview_radar_wrap(self):
        sec = M.section_html("1. Overview (8-Dimension Radar)", ["| Dimension | Score (0-5) |", "|---|---|", "| 1. Functional Correctness | 4 |"])
        self.assertIn("overview", sec)
        self.assertIn('class="radar-wrap"', sec)
        self.assertIn("tbl-scores", sec)
    def test_render_document(self):
        out = M.render_document("Architecture Design: Order Platform (sample)", '<span class="chip">Date 2026-01-01</span>', "<p>x</p>")
        for tok in ("<!--T:TITLE-->", "<!--T:META-->", "<!--T:BODY-->", "<!--T:EXTRA-->"):
            self.assertNotIn(tok, out)
        self.assertIn("Date 2026-01-01", out)
        self.assertIn("<p>x</p>", out)
        self.assertIn("Architecture Design: Order Platform (sample)", out)
    def test_render_document_from_md(self):
        md = ("# Architecture Design: Order Platform\n\n- **Date:** 2026-09-09\n- **Status:** Draft\n\n"
              "## 1. Background & Goals\n\nGoal one.\n\n## 3. Architecture Overview\n\n```mermaid\n"
              "graph LR; A-->B\n```\n")
        out = M.render_document_from_md(md)
        for tok in ("<!--T:TITLE-->", "<!--T:META-->", "<!--T:BODY-->", "<!--T:EXTRA-->"):
            self.assertNotIn(tok, out)
        self.assertIn("Architecture Design: Order Platform", out)
        self.assertIn('class="arch"', out)
        self.assertIn("2026-09-09", out)
        self.assertIn("Goal one.", out)
    def test_adr_intro_kept(self):
        sec = M.section_html("6. ADR Records", ["This section records key decisions.", "### ADR-1: Event-driven calls", "Reason x"])
        self.assertIn("This section records key decisions.", sec)
        self.assertEqual(sec.count("<details"), 1)
        self.assertIn("Reason x", sec)
    def test_adr_variant_headings(self):
        sec = M.section_html("6. ADR Records", ["### ADR-1: a", "x", "###  ADR-2: b", "y", "### adr-3: c", "z"])
        self.assertEqual(sec.count("<details"), 3)
        self.assertIn("adr-3", sec)
    def test_adr_empty_body(self):
        sec = M.section_html("6. ADR Records", ["### ADR-9: Heading only"])
        self.assertEqual(sec.count("<details"), 1)
    def test_duplicate_section_titles_deduped(self):
        md = "# T\n\n## 1. Architecture Overview\n\nAlpha\n\n## Architecture Overview\n\nBeta\n"
        out = M.render_document_from_md(md)
        self.assertEqual(out.count('id="Architecture-Overview"'), 1)
        self.assertEqual(out.count('id="Architecture-Overview-2"'), 1)
    def _cli_paths(self):
        # The sandbox forbids creating directories: CLI cases write plain files
        # (inside the html dir) instead of using tempfile.
        html_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tag = "cli%d" % os.getpid()
        return (html_dir,
                os.path.join(html_dir, "_%s_src.md" % tag),
                os.path.join(html_dir, "_%s_src2.md" % tag),
                os.path.join(html_dir, "_%s_out.html" % tag))
    def _cli_cleanup(self, paths):
        for p in paths:
            try:
                os.remove(p)
            except OSError:
                pass
    def _cli_run(self, html_dir, args):
        import subprocess, sys, os
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run([sys.executable, os.path.join(html_dir, "md2html.py")] + args,
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=env)
    def test_cli_default_deletes_src_keep_flag_keeps(self):
        html_dir, src, src2, out = self._cli_paths()
        md_text = "# CLI\n\n- **Date:** 2026-01-01\n\n## 1. Background & Goals\n\na\n"
        try:
            with open(src, "w", encoding="utf-8") as f:
                f.write(md_text)
            r = self._cli_run(html_dir, [src, out])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.exists(src))   # source deleted by default
            self.assertTrue(os.path.exists(out))
            with open(src2, "w", encoding="utf-8") as f:
                f.write(md_text)
            r2 = self._cli_run(html_dir, [src2, out, "--keep-src"])
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertTrue(os.path.exists(src2))   # --keep-src preserves it
        finally:
            self._cli_cleanup((src, src2, out))
    def test_cli_same_path_rejected(self):
        html_dir, src, _, out = self._cli_paths()
        md_text = "# CLI\n\n- **Date:** 2026-01-01\n\n## 1. Background & Goals\n\na\n"
        try:
            with open(src, "w", encoding="utf-8") as f:
                f.write(md_text)
            r = self._cli_run(html_dir, [src, src])
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Conversion failed", r.stderr)
        finally:
            self._cli_cleanup((src, out))

if __name__ == "__main__":
    unittest.main(verbosity=2)
