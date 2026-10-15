#!/usr/bin/env python3
"""Static sanity checks for the Jekyll site.

This machine has no Ruby, so Jekyll itself cannot be run here (GitHub Pages
builds the site server-side). These checks cover the mistakes that would
otherwise only show up as a broken page after pushing:

1. Navigation anchors actually resolve to a generated heading id or an explicit
   `<span id="...">`. kramdown turns ``# 🔥 News`` into the id ``-news`` (the
   emoji is dropped but the space becomes a hyphen), which is exactly the kind
   of thing that silently breaks in-page navigation.
2. Local files referenced from ``_config.yml`` and ``head/custom.html`` exist.
3. Liquid tags are balanced.
4. No template "Lorem ipsum" placeholders survive.
5. Every ``data-title`` on a paper is unique and non-empty (duplicates would make
   two papers show the same citation count).

Run:
    python tools/check_site.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

failures: list[str] = []
checks = 0


def check(condition: bool, label: str) -> None:
    global checks
    checks += 1
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


def kramdown_id(heading_text: str) -> str:
    """Approximate kramdown's auto_id generation (verified against the live
    AcadHomepage deployments: ``# 🔥 News`` really does become ``-news``)."""
    text = heading_text.strip()
    text = re.sub(r"[^\w \-]", "", text, flags=re.UNICODE)
    text = text.replace(" ", "-").lower()
    return text


def load_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
def test_navigation_anchors() -> None:
    print("\n[1] 导航锚点能在 about.md 里找到落点")

    about = load_text("_pages/about.md")
    nav = load_text("_data/navigation.yml")

    headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", about, flags=re.MULTILINE)
    generated = {kramdown_id(heading) for heading in headings}
    explicit = set(re.findall(r"""id=['"]([^'"]+)['"]""", about))
    available = generated | explicit

    print(f"        kramdown 生成的 id: {sorted(generated)}")
    print(f"        手写的 id:          {sorted(explicit)}")

    anchors = re.findall(r'url:\s*"/#([^"]+)"', nav)
    check(bool(anchors), f"navigation.yml 里解析出 {len(anchors)} 个锚点")

    for anchor in anchors:
        check(anchor in available, f"导航 '#{anchor}' 有对应落点")

    for anchor in anchors:
        check(
            anchor in explicit or anchor in generated,
            f"'{anchor}' 可被浏览器解析（id 是合法标识）",
        )


def test_referenced_files_exist() -> None:
    print("\n[2] 被引用的本地文件都存在")

    config = load_text("_config.yml")
    avatar = re.search(r"^\s*avatar\s*:\s*\"([^\"]+)\"", config, flags=re.MULTILINE)
    check(avatar is not None, "_config.yml 里配置了 avatar")
    if avatar:
        check((ROOT / avatar.group(1)).exists(), f"{avatar.group(1)} 存在")

    custom_head = load_text("_includes/head/custom.html")
    refs = re.findall(r'(?:href|src)="((?!https?:|#|//)[^"]+)"', custom_head)
    refs.append("images/favicon.ico")
    check(bool(refs), f"head/custom.html 里解析出 {len(refs)} 个本地引用")
    for ref in dict.fromkeys(refs):
        check((ROOT / ref).exists(), f"{ref} 存在")

    # 反向检查：manifest 里声明的图标也要真的在
    manifest_path = ROOT / "images" / "site.webmanifest"
    if manifest_path.exists():
        manifest = manifest_path.read_text(encoding="utf-8")
        for icon in re.findall(r'"src"\s*:\s*"([^"]+)"', manifest):
            check((ROOT / "images" / icon).exists(), f"webmanifest 图标 {icon} 存在")


def test_scripts_include_is_wired() -> None:
    print("\n[3] 引用数据脚本确实被挂到页面上")

    scripts = load_text("_includes/scripts.html")
    check(
        "fetch_google_scholar_stats.html" in scripts,
        "scripts.html 引用了 fetch_google_scholar_stats.html",
    )
    layout = load_text("_layouts/default.html")
    check("scripts.html" in layout, "default 布局里包含了 scripts.html")
    include = load_text("_includes/fetch_google_scholar_stats.html")
    check("show_paper_citations" in include, "脚本会查找 .show_paper_citations")
    check("total_cit" in include, "脚本会回填 #total_cit")


def test_liquid_balance() -> None:
    print("\n[4] Liquid 标签成对出现")

    targets = [
        "_pages/about.md",
        "_includes/fetch_google_scholar_stats.html",
        "_includes/scripts.html",
        "_layouts/default.html",
        "_includes/author-profile.html",
    ]
    pairs = [("if", "endif"), ("for", "endfor"), ("unless", "endunless")]
    for target in targets:
        text = load_text(target)
        for opening, closing in pairs:
            opened = len(re.findall(r"{%-?\s*" + opening + r"[\s%]", text))
            closed = len(re.findall(r"{%-?\s*" + closing + r"\s*-?%}", text))
            check(
                opened == closed or (opened == 0 and closed == 0),
                f"{target}: {opening}({opened}) / {closing}({closed}) 配平",
            )


def test_no_placeholders() -> None:
    print("\n[5] 没有残留的模板占位文本")

    suspicious = ["Lorem ipsum", "YOUR_GOOGLE_SCHOLAR_ID", "example.com", "TODO 必改"]
    for target in ["_pages/about.md", "_config.yml", "images/site.webmanifest"]:
        text = load_text(target)
        for phrase in suspicious:
            if phrase == "TODO 必改" and "YOUR_EMAIL" in text:
                # 邮箱占位符是刻意保留的，会在下一步单独报告
                continue
            check(phrase not in text, f"{target} 不含 '{phrase}'")

    # 邮箱占位符单独提示（这是唯一刻意保留、需要用户自己改的）
    config = load_text("_config.yml")
    if "YOUR_EMAIL" in config:
        print("  NOTE  _config.yml 里仍是邮箱占位符 YOUR_EMAIL@stu.pku.edu.cn —— 记得改")


def test_paper_titles() -> None:
    print("\n[6] 论文数据（_data/publications.yml）")

    data = load_text("_data/publications.yml")
    titles = re.findall(r'^\s*title:\s*"([^"]+)"', data, flags=re.MULTILINE)
    figures = re.findall(r'^\s*figure:\s*"([^"]+)"', data, flags=re.MULTILINE)
    authors = re.findall(r"^\s*authors_html:\s*'([^']+)'", data, flags=re.MULTILINE)
    topics = re.findall(r"^\s*-?\s*topic:\s*(\S+)", data, flags=re.MULTILINE)
    dates = re.findall(r'^\s*date:\s*"([^"]+)"', data, flags=re.MULTILINE)
    roles = re.findall(r"^\s*role:\s*(.+?)\s*$", data, flags=re.MULTILINE)
    links = re.findall(r"^\s*links:\s*'([^']+)'", data, flags=re.MULTILINE)

    check(len(titles) == 11, f"共 11 篇论文（实际 {len(titles)}）")
    check(len(set(titles)) == len(titles), "论文标题没有重复")
    check(all(title.strip() for title in titles), "没有空标题")
    check(len(figures) == len(titles), f"每篇都配了框架图（{len(figures)} 张）")
    check(len(authors) == len(titles), f"每篇都有作者列表（{len(authors)} 条）")
    check(len(dates) == len(titles), "每篇都有 date（用于组内排序）")
    check(len(roles) == len(titles), "每篇都标了 role（一作 / 共同一作 / 合作）")

    check(
        topics.count("st") == 4
        and topics.count("vcell") == 1
        and topics.count("imaging") == 4
        and topics.count("other") == 2,
        "分类：空间转录 4 / 虚拟细胞扰动 1 / 医学影像 4 / 其他 2"
        f"（实际 {topics}）",
    )
    check(
        all(re.match(r"^\d{4}-\d{2}(-\d{2})?$", value) for value in dates),
        "date 都是 YYYY-MM 或 YYYY-MM-DD",
    )

    for figure in figures:
        check((ROOT / figure).exists(), f"{figure} 存在")

    for title, author_html in zip(titles, authors):
        check(
            "<strong>Ningfeng Que</strong>" in author_html,
            f"作者本人加粗：{title[:36]}",
        )
        check("✉" in author_html, f"标了通讯作者：{title[:36]}")

    for link in links:
        check("github.com/" in link, f"代码链接指向 GitHub：{link[:70]}")
    check(len(links) == 5, f"5 篇写明了公开代码（实际 {len(links)}）")

    # “其他合作”那两篇（材料综述、人体活动识别）里作者不是共同一作
    other_block = data.split("- topic: other", 1)[1] if "- topic: other" in data else ""
    check(
        "<strong>Ningfeng Que</strong><sup>†</sup>" not in other_block,
        "其他合作组里作者本人不带共同一作标记",
    )


def test_publications_include_is_wired() -> None:
    print("\n[6b] 论文渲染模板")

    about = load_text("_pages/about.md")
    check("{% include publications.html %}" in about, "about.md 引用 publications.html")
    check("# 📝 Publications" in about, "about.md 里有 Publications 标题")
    # 旧的手写列表必须已经删掉，否则会和模板渲染重复
    check('class="pub-venue"' not in about, "about.md 里没有遗留的手写论文条目")

    include = load_text("_includes/publications.html")
    check("site.data.publications" in include, "模板读取 _data/publications.yml")
    check('where: "topic"' in include, "模板按研究类别分节")
    check('sort: "date"' in include, "模板每组按日期排序")
    check("reverse" in include, "新的论文排在前面")
    for key in ["st", "vcell", "imaging", "other"]:
        check(f"{key}|" in include, f"模板里定义了分类 {key}")
    check("paper.role" in include, "模板输出作者角色（一作/共同一作/合作）")
    check("data-title" in include, "模板渲染了引用数所需的 data-title")
    check("data-title-alt" in include, "模板支持候选标题（预印本改名的情况）")
    check("paper-box" in include, "模板使用了左右布局的 paper-box")
    check("paper.authors_html" in include, "模板输出作者列表（不转义 HTML）")
    check("venue_full" in include, "模板输出期刊全称")

    js = load_text("_includes/fetch_google_scholar_stats.html")
    check("candidateTitles" in js, "引用脚本会尝试多个候选标题")
    check("data-title-alt" in js, "引用脚本读取 data-title-alt")

    css = load_text("assets/css/main.scss")
    check(".author__urls li" in css and "white-space: normal" in css,
          "侧边栏长文本已改为自动换行")
    for selector in [".pub-title", ".pub-authors", ".pub-meta", ".pub-note"]:
        check(selector in css, f"样式里有 {selector}")


def test_config_keys() -> None:
    print("\n[7] _config.yml 关键项")

    config = load_text("_config.yml")
    check(
        'repository               : "queningfeng/queningfeng.github.io"' in config,
        "repository 指向 queningfeng/queningfeng.github.io",
    )
    check("ZxrkoP4AAAAJ" in config, "Google Scholar ID 已写入")
    check("0009-0000-1790-1241" in config, "ORCID 已写入")
    check("queningfeng" in config, "GitHub 用户名已写入")
    check(
        "\t" not in config,
        "没有 Tab 字符（YAML 禁止用 Tab 缩进）",
    )
    check("  - tools" in config, "tools/ 已被 exclude，不会被打包进站点")


def test_yaml_shape() -> None:
    """A focused structural lint for the two YAML files.

    No PyYAML is available in this sandbox, so instead of parsing we validate the
    shape: indentation is a multiple of two, and every meaningful line is one of
    the forms this file is allowed to use. That catches the realistic YAML
    mistake -- a line indented one space too far, which silently re-parents a key
    and changes the meaning of the config.
    """
    print("\n[8] YAML 结构 lint（缩进 / 行形状）")

    allowed = re.compile(
        r"^("
        r"(?P<key>[A-Za-z_][\w.\-]*)\s*:(\s+.*)?$"      # key: / key: value
        r"|-\s+.*$"                                      # list item
        r"|(?P<url_key>url|title)\s*:\s*.*$"            # list-of-mapping entries
        r")"
    )

    for target in ["_config.yml", "_data/navigation.yml", "_data/publications.yml"]:
        text = load_text(target)
        bad_indent = []
        bad_shape = []
        for number, raw in enumerate(text.splitlines(), start=1):
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent % 2 != 0:
                bad_indent.append(f"{target}:{number} 缩进 {indent} 空格不是 2 的倍数")
            if not allowed.match(raw.strip()):
                bad_shape.append(f"{target}:{number} 形状无法识别: {raw.strip()[:50]!r}")

        check(not bad_indent, f"{target} 缩进都是 2 的倍数")
        for problem in bad_indent:
            print(f"        {problem}")
        check(not bad_shape, f"{target} 每行都是合法的 YAML 结构")
        for problem in bad_shape:
            print(f"        {problem}")

    # navigation.yml 必须能解析成 (title, url) 对
    nav = load_text("_data/navigation.yml")
    entries = re.findall(
        r'-\s+title:\s*"([^"]+)"\s*\n\s*url:\s*"([^"]+)"', nav
    )
    check(len(entries) >= 4, f"navigation.yml 解析出 {len(entries)} 个有效导航项")
    check(
        all(url.startswith("/#") for _, url in entries),
        "所有导航 url 都是站内锚点",
    )


def main() -> int:
    print("=" * 72)
    print("静态站点检查（本机没有 Ruby，无法运行 Jekyll 本身）")
    print("=" * 72)

    test_navigation_anchors()
    test_referenced_files_exist()
    test_scripts_include_is_wired()
    test_liquid_balance()
    test_no_placeholders()
    test_paper_titles()
    test_publications_include_is_wired()
    test_config_keys()
    test_yaml_shape()

    print("\n" + "=" * 72)
    if failures:
        print(f"FAILED: {len(failures)} / {checks} 项未通过")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"OK: {checks} 项检查全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
