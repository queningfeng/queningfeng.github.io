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
        "display_name": "Ningfeng Que",
        "cited_by_count": 69,
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
    check(len(calls) == 2, "both OpenAlex endpoints were queried")

    if data:
        for entry in data["publications"].values():
            check(
                isinstance(entry.get("num_citations"), int)
                and isinstance(entry.get("bib", {}).get("title"), str),
                f"entry has the schema the page reads ({entry['bib']['title'][:34]!r})",
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


def main() -> int:
    print("=" * 72)
    print("crawler / title-matching tests")
    print("=" * 72)

    test_normalisers_agree()
    test_norm_title_edge_cases()
    test_openalex_fallback_parsing()
    test_gs_schema_matches_page_expectations()
    test_refuses_to_publish_empty_data()

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
