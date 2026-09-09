# -*- coding: utf-8 -*-
"""端到端验收:校验渲染产物与断言、与既有产物(golden)一致性。

运行: python accept.py            (从 references/html/tests 下;路径已按 __file__ 归一)
      python accept.py --write    (显式刷新被断言覆盖的样例产物)

失败时不会改写受测产物;--write 仅在全部断言通过后落盘。
既有产物与重渲染不一致时,非 --write 模式判失败且不改写;传 --write 且内容
断言(锚点/令牌)通过时,才把该过期产物刷新为当前渲染。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import md2html as M

# 属性形态锚定,避免被 shell 的 CSS/JS 文本虚满足
NEEDLES = {
    "sample-design": ['<section class="sec arch-sec"', '<figure class="arch">',
                      '<div class="arch-src"', "ADR-2", '<details class="adr">',
                      '<span class="chip chip-warn"', '<table class="tbl">',
                      "演进路线图"],
    "sample-review": ['<section class="sec overview"', '<table class="tbl tbl-scores">',
                      '<div class="radar-wrap">', '<span class="chip chip-red"',
                      '<span class="chip chip-yellow"', "整改路线图"],
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
            bad.append("残留令牌 <!--T:")
        stale = out.exists() and out.read_text(encoding="utf-8") != text
        if stale and not write_mode:
            bad.append("与既有产物不一致(如需刷新请传 --write)")
        # 内容断言通过才落盘:产物缺失时生成;--write 且过期时刷新 golden
        if not bad and (not out.exists() or (write_mode and stale)):
            out.write_text(text, encoding="utf-8")
        print(stem + ".html", "PASS" if not bad else "FAIL " + str(bad))
        ok = ok and not bad
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # 样例缺失/源稿非法等:遵循脚本自身 0/1 约定,不裸堆栈
        print("验收失败:%s" % e, file=sys.stderr)
        sys.exit(1)
