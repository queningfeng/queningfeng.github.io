#!/usr/bin/env python3
"""Tests for the citation crawler and the page-side title matching.

The design deliberately matches papers by *normalised title* rather than by
Google Scholar's internal cluster IDs. That only works if the Python normaliser
and the JavaScript normaliser agree exactly, so the most important test here
extracts `normTitle` out of the real include file and diffs it against Python's
`norm_title` for every title actually used on the homepage.

Run:
    python google_scholar_crawler/test_crawler.py
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
INCLUDE = ROOT / "_includes" / "fetch_google_scholar_stats.html"
ABOUT = ROOT / "_pages" / "about.md"

sys.path.insert(0, str(HERE))
import main as crawler  # noqa: E402

NODE_CANDIDATES = [
    r"C:\Users\LEGION\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\node\bin\node.exe",
    "node",
]

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


# ---------------------------------------------------------------------------
# 1. Titles really used on the homepage, extracted from about.md
# ---------------------------------------------------------------------------
def titles_from_about() -> list[str]:
    text = ABOUT.read_text(encoding="utf-8")
    return re.findall(r'data-title="([^"]+)"', text)


def find_node() -> str | None:
    for candidate in NODE_CANDIDATES:
        try:
            subprocess.run(
                [candidate, "--version"], capture_output=True, check=True, timeout=30
            )
            return candidate
        except Exception:  # noqa: BLE001
            continue
    return None


def extract_js_norm_title() -> str:
    """Pull the real `normTitle` function out of the include file."""
    source = INCLUDE.read_text(encoding="utf-8")
    start = source.index("function normTitle(value)")
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError("could not find the end of normTitle in the include file")


def js_normalise(node: str, titles: list[str]) -> list[str]:
    function_source = extract_js_norm_title()
    script = (
        function_source
        + "\nconst titles = "
        + json.dumps(titles)
        + ";\nconsole.log(JSON.stringify(titles.map(normTitle)));"
    )
    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise AssertionError(f"node failed: {result.stderr}")
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_normalisers_agree() -> None:
    print("\n[1] Python and JavaScript title normalisers agree")
    titles = titles_from_about()
    check(len(titles) == 10, f"about.md declares 10 papers (found {len(titles)})")

    node = find_node()
    if node is None:
        print("  SKIP  node not found, cannot diff against the JavaScript")
        return

    py = [crawler.norm_title(title) for title in titles]
    js = js_normalise(node, titles)

    for title, python_value, js_value in zip(titles, py, js):
        check(
            python_value == js_value,
            f"{title[:55]!r:58} py={python_value[:28]!r}",
        )
        check(bool(python_value), f"  normalised form is non-empty for {title[:40]!r}")


def test_norm_title_edge_cases() -> None:
    print("\n[2] norm_title handles the messy real-world variants")
    pairs = [
        # Google Scholar often injects markup and stray spacing around colons.
        (
            "VTCNet : A Feature Fusion DL Model Based on CNN and ViT",
            "VTCNet: A Feature Fusion DL Model Based on CNN and ViT",
        ),
        # HTML entities and tags must be stripped on both sides.
        ("Physics in Medicine &amp; Biology", "Physics in Medicine  Biology"),
        ("<scp>VTCNet</scp>: A Model", "VTCNet: A Model"),
        # Case and punctuation never matter.
        ("  Deep   Residual  Learning!! ", "deep residual learning"),
    ]
    for left, right in pairs:
        check(
            crawler.norm_title(left) == crawler.norm_title(right),
            f"{left[:48]!r} == {right[:48]!r}",
        )


def test_openalex_fallback_parsing() -> None:
    print("\n[3] OpenAlex fallback produces the schema the page expects")

    author_fixture = {
        "id": "https://openalex.org/A5094126306",
        "display_name": "Ningfeng Que",
        "cited_by_count": 69,
        "works_count": 10,
        "summary_stats": {"h_index": 3, "i10_index": 3},
    }
    works_fixture = {
        "results": [
            {
                "id": "https://openalex.org/W1",
                "doi": "https://doi.org/10.1000/example",
                "title": "Adaptive Spatial Transcriptomics Interpolation",
                "publication_year": 2025,
                "cited_by_count": 2,
            },
            {
                "id": "https://openalex.org/W2",
                "doi": None,
                "title": "MLAR-UNet: LDCT image denoising",
                "publication_year": 2025,
                "cited_by_count": 3,
            },
            # A work with no title must be skipped, not crash the run.
            {"id": "https://openalex.org/W3", "title": "", "cited_by_count": 1},
        ]
    }

    calls: list[str] = []

    def fake_http_json(url: str, *args, **kwargs):  # noqa: ANN002, ANN003
        calls.append(url)
        return author_fixture if "/authors/" in url else works_fixture

    original = crawler.http_json
    crawler.http_json = fake_http_json
    try:
        data = crawler.from_openalex()
    finally:
        crawler.http_json = original

    check(data is not None, "from_openalex returns data")
    check(data is not None and data["source"] == "openalex", "source is tagged openalex")
    check(data is not None and data["citedby"] == 69, "total citations carried over")
    check(data is not None and data["hindex"] == 3, "h-index carried over")
    check(data is not None and data["i10index"] == 3, "i10-index carried over")
    check(
        data is not None and len(data["publications"]) == 2,
        "untitled work is skipped (2 of 3 kept)",
    )
    check(
        any("author.orcid" in url for url in calls),
        "queried works by ORCID",
    )
    check(
        any("author.id" in url for url in calls),
        "queried works by OpenAlex author id as well",
    )

    if data:
        for entry in data["publications"].values():
            check(
                isinstance(entry.get("num_citations"), int)
                and isinstance(entry.get("bib", {}).get("title"), str),
                f"entry has the schema the page reads ({entry['bib']['title'][:34]!r})",
            )


def test_openalex_merges_both_queries() -> None:
    """Regression: an ORCID-only query drops papers OpenAlex never linked to the ORCID.

    The IJCAI 2024 paper ("Multi-scale Context-Aware Networks ...") is attached to
    the author entity but carries no ORCID on its authorship, so it only shows up
    in the author-id query. If the two queries are not merged, that paper silently
    gets no citation count on the homepage.
    """
    print("\n[3b] ORCID 查询与 author-id 查询取并集")

    author_fixture = {
        "id": "https://openalex.org/A5094126306",
        "display_name": "Ningfeng Que",
        "cited_by_count": 69,
        "works_count": 10,
        "summary_stats": {"h_index": 3, "i10_index": 3},
    }
    by_orcid = {
        "results": [
            {
                "id": "https://openalex.org/W1",
                "doi": "https://doi.org/10.1000/orcid-only",
                "title": "A paper with an ORCID",
                "publication_year": 2025,
                "cited_by_count": 4,
            }
        ]
    }
    by_author_id = {
        "results": [
            {
                "id": "https://openalex.org/W1",
                "doi": "https://doi.org/10.1000/orcid-only",
                "title": "A paper with an ORCID",
                "publication_year": 2025,
                "cited_by_count": 4,
            },
            {
                "id": "https://openalex.org/W9",
                "doi": "https://doi.org/10.24963/ijcai.2024/351",
                "title": "Multi-scale Context-Aware Networks for Human Activity Recognition",
                "publication_year": 2024,
                "cited_by_count": 2,
            },
        ]
    }

    def fake_http_json(url: str, *args, **kwargs):  # noqa: ANN002, ANN003
        if "/authors/" in url:
            return author_fixture
        if "author.id" in url:
            return by_author_id
        return by_orcid

    original = crawler.http_json
    crawler.http_json = fake_http_json
    try:
        data = crawler.from_openalex()
    finally:
        crawler.http_json = original

    check(data is not None, "from_openalex returns data")
    if not data:
        return
    check(
        len(data["publications"]) == 2,
        f"并集包含两篇（实际 {len(data['publications'])}）",
    )
    titles = [p["bib"]["title"] for p in data["publications"].values()]
    check(
        any("Multi-scale" in title for title in titles),
        "只出现在 author-id 查询里的 IJCAI 论文被保留",
    )
    check(
        len(titles) == len(set(titles)),
        "同一 DOI 不会重复计入",
    )


def test_gs_schema_matches_page_expectations() -> None:
    print("\n[4] The page-side JS reads exactly the fields the crawler writes")
    include = INCLUDE.read_text(encoding="utf-8")
    for field in ["publications", "num_citations", "bib", "title", "citedby", "source"]:
        check(field in include, f"page JS references '{field}'")


def test_refuses_to_publish_empty_data() -> None:
    print("\n[5] An all-empty payload is rejected instead of blanking the site")

    def fake_http_json(url: str, *args, **kwargs):  # noqa: ANN002, ANN003
        if "/authors/" in url:
            return {"display_name": "X", "cited_by_count": 0, "summary_stats": {}}
        return {"results": [{"id": "W1", "title": "", "cited_by_count": 0}]}

    original = crawler.http_json
    crawler.http_json = fake_http_json
    try:
        data = crawler.from_openalex()
    finally:
        crawler.http_json = original

    check(data is None, "from_openalex returns None when nothing usable came back")


def extract_js_apply_block() -> str:
    """Pull `normTitle` + `setText` + `applyData` out of the include file.

    The region is contiguous in the source but contains Liquid tags, which are
    not valid JavaScript, so they are stripped. `load()` is deliberately left
    out: it is the only part that touches the network.
    """
    source = INCLUDE.read_text(encoding="utf-8")
    start = source.index("function normTitle(value)")
    end = source.index("function load()")
    region = source[start:end]
    # Drop {% if ... %} / {% else %} / {% endif %} and the surrounding
    # assignments so what remains is plain JS. Duplicate `var` declarations are
    # legal in sloppy mode, so the two gsDataBaseUrl assignments are harmless.
    region = re.sub(r"\{%[^%]*%\}", "", region)
    if "{%" in region or "%}" in region:
        raise AssertionError("Liquid stripping left fragments behind")
    return region


def run_apply_data(node: str, fixture: dict, titles: list[str]) -> dict:
    """Execute the production applyData() against a stubbed DOM."""
    script = """
const totalEl = { _t: "", set textContent(v) { this._t = String(v); },
                  get textContent() { return this._t; },
                  setAttribute() {} };
const citationEls = TITLES.map((t) => ({
    _t: "", "data-title": t,
    set textContent(v) { this._t = String(v); },
    get textContent() { return this._t; },
    getAttribute(k) { return this[k]; },
    setAttribute(k, v) { this[k] = String(v); },
}));
globalThis.document = {
    getElementById: (id) => (id === "total_cit" ? totalEl : null),
    getElementsByClassName: (cls) => (cls === "show_paper_citations" ? citationEls : []),
};

APPLY_BLOCK

applyData(FIXTURE);

console.log(JSON.stringify({
    total: totalEl.textContent,
    papers: citationEls.map((e) => e.textContent),
}));
"""
    script = script.replace("APPLY_BLOCK", extract_js_apply_block())
    script = script.replace("TITLES", json.dumps(titles))
    script = script.replace("FIXTURE", json.dumps(fixture))

    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise AssertionError(f"node failed:\n{result.stderr}")
    return json.loads(result.stdout)


def test_duplicate_normalised_titles_keep_the_maximum() -> None:
    """Regression: a journal version and its preprint normalise to the same key.

    OpenAlex lists VTCNet twice (Wiley `ima.23161` with 12 citations and the SSRN
    preprint `ssrn.4748846` with 3). Writing the map in key order let the *later*
    preprint overwrite the journal count, so the page showed 3 instead of 12.
    """
    print("\n[6] 同一篇论文的重复收录取较大引用数")

    node = find_node()
    if node is None:
        print("  SKIP  node not found")
        return

    title = "VTCNet: A Feature Fusion DL Model Based on CNN and ViT for the Classification of Cervical Cells"
    fixture = {
        "source": "openalex",
        "citedby": 69,
        "updated": "2026-10-14 17:28:18 UTC",
        "publications": {
            # Exactly what OpenAlex actually returns for the Wiley version.
            "ima.23161": {
                "bib": {
                    "title": (
                        "VTCNet : A Feature Fusion DL Model Based on CNN and ViT "
                        "for the Classification of Cervical Cells"
                    )
                },
                "num_citations": 12,
            },
            # The SSRN preprint, listed second -- this is the order that won before.
            "ssrn.4748846": {
                "bib": {
                    "title": (
                        "Vtcnet: A Feature Fusion Dl Model Based on Cnn and Vit "
                        "for the Classification of Cervical Cells"
                    )
                },
                "num_citations": 3,
            },
        },
    }

    output = run_apply_data(node, fixture, [title])
    check(output["total"] == "69", "总引用数被回填")
    check(
        output["papers"][0] == "Cited by 12",
        f"重复收录时取最大值 (得到 {output['papers'][0]!r})",
    )


def test_prefix_fallback_for_truncated_titles() -> None:
    print("\n[7] 标题被截断时的前缀兜底匹配")

    node = find_node()
    if node is None:
        print("  SKIP  node not found")
        return

    long_title = (
        "Adaptive Spatial Transcriptomics Interpolation via Cross-modal "
        "Cross-slice Modeling with Extra Words Appended Here"
    )
    fixture = {
        "source": "google_scholar",
        "citedby": 5,
        "publications": {
            "x": {
                "bib": {
                    "title": (
                        "Adaptive Spatial Transcriptomics Interpolation via "
                        "Cross-modal Cross-slice Modeling"
                    )
                },
                "num_citations": 2,
            }
        },
    }

    output = run_apply_data(node, fixture, [long_title])
    check(
        output["papers"][0] == "Cited by 2",
        f"数据源标题更短时回退匹配 (得到 {output['papers'][0]!r})",
    )

    # 反方向：数据源标题更长（Google Scholar 上常见 "Title…" 截断）
    shorter_page_title = (
        "Adaptive Spatial Transcriptomics Interpolation via Cross-modal Cross-slice Modeling"
    )
    longer_fixture = {
        "source": "google_scholar",
        "citedby": 5,
        "publications": {
            "y": {
                "bib": {
                    "title": shorter_page_title
                    + " with Extra Words Appended Here And More"
                },
                "num_citations": 7,
            }
        },
    }
    output2 = run_apply_data(node, longer_fixture, [shorter_page_title])
    check(
        output2["papers"][0] == "Cited by 7",
        f"数据源标题更长时回退匹配 (得到 {output2['papers'][0]!r})",
    )


def test_unknown_titles_stay_empty() -> None:
    print("\n[8] 匹配不到的论文保持空白，不显示 0")

    node = find_node()
    if node is None:
        print("  SKIP  node not found")
        return

    fixture = {
        "source": "openalex",
        "citedby": 1,
        "publications": {
            "y": {"bib": {"title": "Some Totally Different Paper"}, "num_citations": 9}
        },
    }
    output = run_apply_data(node, fixture, ["My Paper That Is Not In The Feed"])
    check(
        output["papers"][0] == "",
        f"未匹配的论文保持空 (得到 {output['papers'][0]!r})",
    )


def main() -> int:
    print("=" * 72)
    print("crawler / title-matching tests")
    print("=" * 72)

    test_normalisers_agree()
    test_norm_title_edge_cases()
    test_openalex_fallback_parsing()
    test_openalex_merges_both_queries()
    test_gs_schema_matches_page_expectations()
    test_refuses_to_publish_empty_data()
    test_duplicate_normalised_titles_keep_the_maximum()
    test_prefix_fallback_for_truncated_titles()
    test_unknown_titles_stay_empty()

    print("\n" + "=" * 72)
    if failures:
        print(f"FAILED: {len(failures)} of {checks} checks")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"OK: all {checks} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
