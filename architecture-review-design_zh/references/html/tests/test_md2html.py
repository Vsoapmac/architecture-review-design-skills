# -*- coding: utf-8 -*-
"""md2html 单元测试。运行: python tests/test_md2html.py -v (工作目录 references/html)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import md2html as M

class TestInline(unittest.TestCase):
    def test_bold_italic_code(self):
        self.assertEqual(M.inline("**a** *b* `c()` x"),
                         "<strong>a</strong> <em>b</em> <code>c()</code> x")
    def test_link(self):
        self.assertEqual(M.inline("[文档](../specs/x.md)"), '<a href="../specs/x.md">文档</a>')
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
        self.assertEqual(M.inline("[点我](javascript:alert(1))"), "点我")
    def test_data_url_rejected(self):
        self.assertEqual(M.inline("[x](data:text/html,hi)"), "x")
    def test_mixed_case_scheme_rejected(self):
        self.assertEqual(M.inline("[x](JaVaScRiPt:alert(1))"), "x")
    def test_anchor_allowed(self):
        self.assertIn('<a href="#sec-1">跳</a>', M.inline("[跳](#sec-1)"))
    def test_relative_allowed(self):
        self.assertIn('<a href="../specs/x.md">文档</a>', M.inline("[文档](../specs/x.md)"))
    def test_entity_obfuscated_scheme_inert(self):
        out = M.inline("[x](javascript&colon;alert(1))")
        self.assertIn("&amp;colon;", out)
        self.assertNotIn('href="javascript:', out)
    def test_mailto_allowed(self):
        self.assertIn('<a href="mailto:a@b.c">x</a>', M.inline("[x](mailto:a@b.c)"))
    def test_rejected_label_with_bold(self):
        self.assertEqual(M.inline("[**危险**](javascript:alert(1))"),
                         "<strong>危险</strong>")

class TestChip(unittest.TestCase):
    def test_line_start(self):
        self.assertEqual(M.chipify("🔴 必须修复"),
                         '<span class="chip chip-red">🔴 必须修复</span>')
    def test_not_middle(self):
        self.assertIsNone(M.chipify("文本🔴 内容"))
    def test_meta_malformed_line_not_lost(self):
        # 畸形行须位于有效 chip 行之后:提取失败即停,畸形行原样进 rest 不丢失
        html, rest = M.parse_meta(["- **日期：** 2026-01-01", "- **无冒号字段**"])
        self.assertIn("2026-01-01", html)
        self.assertEqual(rest, ["- **无冒号字段**"])

class TestBlocks(unittest.TestCase):
    def test_paragraphs(self):
        html = M.blocks("第一段\n\n第二段", "generic")
        self.assertEqual(html.count("<p>"), 2)
    def test_ul_li_with_chip(self):
        html = M.blocks("- 🔴 问题A\n- 普通项", "generic")
        self.assertIn("chip-red", html)
        self.assertIn("<li>普通项</li>", html)
    def test_ol(self):
        self.assertIn("<ol>", M.blocks("1. 一\n2. 二", "generic"))
    def test_blockquote(self):
        self.assertIn('class="ev"', M.blocks("> 证据", "generic"))
    def test_plain_fence(self):
        html = M.blocks("```python\nprint(1)\n```", "generic")
        self.assertIn('class="code"', html)
        self.assertIn("print(1)", html)
    def test_mermaid_fence_arch(self):
        html = M.blocks("```mermaid\ngraph LR; A-->B\n```", "generic")
        self.assertIn('class="arch"', html)
        self.assertIn("arch-src", html)
    def test_table(self):
        html = M.blocks("| 模块 | 职责 |\n|---|---|\n| a | b |", "generic")
        self.assertIn('<table class="tbl">', html)
        self.assertIn("<th>模块</th>", html)
        self.assertIn("<td>a</td>", html)
    def test_hr(self):
        self.assertIn("<hr>", M.blocks("---", "generic"))
    def test_blockquote_keeps_content(self):
        html = M.blocks("> 证据一\n> 证据二", "generic")
        self.assertIn("证据一", html)
        self.assertIn("证据二", html)
    def test_crlf_input(self):
        html = M.blocks("第一行\r\n第二行", "generic")
        self.assertIn("第一行", html)
        self.assertIn("第二行", html)

class TestSection(unittest.TestCase):
    def test_role_detect(self):
        self.assertEqual(M.role_of("3. 架构概览"), "arch-sec")
        self.assertEqual(M.role_of("6. ADR 决策记录"), "adr")
        self.assertEqual(M.role_of("7. 8 维度自检表"), "selftest")
        self.assertEqual(M.role_of("8. 演进路线图"), "roadmap")
        self.assertEqual(M.role_of("1. 总览(8 维度雷达)"), "overview")
        self.assertEqual(M.role_of("未知标题"), "generic")
        self.assertEqual(M.role_of("4. 模块清单与职责"), "generic")
    def test_cells(self):
        self.assertEqual(M.cell_html("✅"),
                         '<span class="chip chip-ok">✅</span>')
        self.assertEqual(M.cell_html("⚠️ 风险"),
                         '<span class="chip chip-warn">⚠️ 风险</span>')
    def test_meta_parse(self):
        html, rest = M.parse_meta(["- **日期：** 2026-01-01", "", "# title"])
        self.assertIn("2026-01-01", html)
        self.assertEqual(rest[1], "# title")
    def test_cells_five_marks(self):
        self.assertEqual(M.cell_html("🔴 风险"),
                         '<span class="chip chip-red">🔴 风险</span>')
        self.assertEqual(M.cell_html("⚪ 提示"),
                         '<span class="chip chip-gray">⚪ 提示</span>')
        self.assertEqual(M.cell_html("✅ / ⚠️ 风险"),
                         '<span class="chip chip-warn">✅ / ⚠️ 风险</span>')
    def test_adr_h3_generic_not_swallowed(self):
        html = M.blocks("### ADR-9：游离条目\n内容", "generic")
        self.assertIn("sub-h3", html)
        self.assertIn("ADR-9", html)
    def test_adr_h3_swallowed_in_adr_role(self):
        html = M.blocks("### ADR-1：xx\n内容", "adr")
        self.assertNotIn("sub-h3", html)
    def test_selftest_table_integration(self):
        html = M.blocks("| 维度 | 状态 |\n|---|---|\n| 1. 功能 | 🔴 风险 |", "selftest")
        self.assertIn("chip-red", html)
    def test_overview_table_class_and_avg(self):
        html = M.blocks("| 维度 | 评分 |\n|---|---|\n| 1. 功能正确性 | 4 |\n| **平均** | **3.0** |", "overview")
        self.assertIn("tbl-scores", html)
        self.assertIn("平均", html)
    def test_meta_parse_leading_blank(self):
        html, rest = M.parse_meta(["", "- **日期：** 2026-01-01", "", "正文"])
        self.assertIn("2026-01-01", html)
        self.assertEqual(rest[0], "")
        self.assertEqual(rest[1], "正文")
    def test_roadmap_table_wrapped(self):
        html = M.blocks("| 阶段 | 范围 |\n|---|---|\n| MVP | 纵向切片 |", "roadmap")
        self.assertIn('class="roadmap"', html)
    def test_slug_nested_number(self):
        self.assertEqual(M.slugify("1.2 子模块"), "子模块")
    def test_dim_h3_in_review(self):
        html = M.blocks("### 维度 4：可观测性 — 评分 2/5\n内容", "generic")
        self.assertIn("sub-h3", html)
        self.assertIn("可观测性", html)

class TestAssemble(unittest.TestCase):
    def test_section_roles(self):
        sec = M.section_html("3. 架构概览", ["```mermaid", "graph LR; A-->B", "```"])
        self.assertIn("arch-sec", sec)
        self.assertIn('<h2 class="sec-title">', sec)
        self.assertIn('<div class="sec-body">', sec)
        sec2 = M.section_html("6. ADR 决策记录",
                              ["### ADR-1：事件驱动", "理由 x", "### ADR-2：DB", "理由 y"])
        self.assertEqual(sec2.count("<details"), 2)
        self.assertIn("ADR-2", sec2)
        self.assertIn("<summary>", sec2)
    def test_overview_radar_wrap(self):
        sec = M.section_html("1. 总览(8 维度雷达)", ["| 维度 | 评分 |", "|---|---|", "| 1. 功能正确性 | 4 |"])
        self.assertIn("overview", sec)
        self.assertIn('class="radar-wrap"', sec)
        self.assertIn("tbl-scores", sec)
    def test_render_document(self):
        out = M.render_document("架构设计:订单中台(样例)", "<span class=\"chip\">日期 2026-01-01</span>", "<p>x</p>")
        for tok in ("<!--T:TITLE-->", "<!--T:META-->", "<!--T:BODY-->", "<!--T:EXTRA-->"):
            self.assertNotIn(tok, out)
        self.assertIn("日期 2026-01-01", out)
        self.assertIn("<p>x</p>", out)
        self.assertIn("架构设计:订单中台(样例)", out)
    def test_render_document_from_md(self):
        md = ("# 架构设计:订单中台\n\n- **日期：** 2026-09-09\n- **状态：** 草稿\n\n"
              "## 1. 背景与目标\n\n目标一。\n\n## 3. 架构概览\n\n```mermaid\n"
              "graph LR; A-->B\n```\n")
        out = M.render_document_from_md(md)
        for tok in ("<!--T:TITLE-->", "<!--T:META-->", "<!--T:BODY-->", "<!--T:EXTRA-->"):
            self.assertNotIn(tok, out)
        self.assertIn("架构设计:订单中台", out)
        self.assertIn('class="arch"', out)
        self.assertIn("2026-09-09", out)
        self.assertIn("目标一。", out)
    def test_adr_intro_kept(self):
        sec = M.section_html("6. ADR 决策记录", ["本节约录关键取舍。", "### ADR-1：事件驱动", "理由 x"])
        self.assertIn("本节约录关键取舍。", sec)
        self.assertEqual(sec.count("<details"), 1)
        self.assertIn("理由 x", sec)
    def test_adr_variant_headings(self):
        sec = M.section_html("6. ADR 决策记录", ["### ADR-1：a", "x", "###  ADR-2：b", "y", "### adr-3：c", "z"])
        self.assertEqual(sec.count("<details"), 3)
        self.assertIn("adr-3", sec)
    def test_adr_empty_body(self):
        sec = M.section_html("6. ADR 决策记录", ["### ADR-9：只有标题"])
        self.assertEqual(sec.count("<details"), 1)
    def test_duplicate_section_titles_deduped(self):
        md = "# T\n\n## 1. 架构概览\n\n甲\n\n## 架构概览\n\n乙\n"
        out = M.render_document_from_md(md)
        self.assertEqual(out.count('id="架构概览"'), 1)
        self.assertEqual(out.count('id="架构概览-2"'), 1)
    def _cli_paths(self):
        # 沙箱内禁止创建目录:CLI 用例直接使用文件路径(html 目录内),不再用 tempfile
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
        md_text = "# CLI\n\n- **日期：** 2026-01-01\n\n## 1. 背景与目标\n\na\n"
        try:
            with open(src, "w", encoding="utf-8") as f:
                f.write(md_text)
            r = self._cli_run(html_dir, [src, out])
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.exists(src))   # 默认删除源稿
            self.assertTrue(os.path.exists(out))
            with open(src2, "w", encoding="utf-8") as f:
                f.write(md_text)
            r2 = self._cli_run(html_dir, [src2, out, "--keep-src"])
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertTrue(os.path.exists(src2))   # --keep-src 保留
        finally:
            self._cli_cleanup((src, src2, out))
    def test_cli_same_path_rejected(self):
        html_dir, src, _, out = self._cli_paths()
        md_text = "# CLI\n\n- **日期：** 2026-01-01\n\n## 1. 背景与目标\n\na\n"
        try:
            with open(src, "w", encoding="utf-8") as f:
                f.write(md_text)
            r = self._cli_run(html_dir, [src, src])
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("转换失败", r.stderr)
        finally:
            self._cli_cleanup((src, out))

if __name__ == "__main__":
    unittest.main(verbosity=2)
