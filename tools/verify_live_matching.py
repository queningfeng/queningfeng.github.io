#!/usr/bin/env python3
"""Verify the LIVE citation feed against the titles written in _pages/about.md.

This runs the *production* JavaScript (the very `normTitle`/`setText`/`applyData`
from `_includes/fetch_google_scholar_stats.html`) against the real
`gs_data.json` published to the `google-scholar-stats` branch, with a stubbed
DOM. It answers the only question that matters after a data change:

    "will citation numbers actually show up on my page?"

It is worth running after editing the paper list or the crawler. Two real bugs
were found this way, neither of which any fixture-based test had caught:

  * VTCNet appears twice in OpenAlex (journal + SSRN preprint) with titles that
    normalise identically, so the later preprint overwrote the journal count.
  * The IJCAI 2024 paper has no ORCID and no author entity in OpenAlex, so two
    of the three works queries dropped it and the row stayed blank.

Usage:
    python tools/verify_live_matching.py                # fetch from the CDN
    python tools/verify_live_matching.py path/to/gs_data.json   # use a local copy
    python tools/verify_live_matching.py --raw          # fetch from raw.githubusercontent

Requires Node.js on PATH (or set NODE_BIN).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "queningfeng/queningfeng.github.io"
BRANCH = "google-scholar-stats"

CDN_URL = f"https://cdn.jsdelivr.net/gh/{REPO}@{BRANCH}/gs_data.json"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/gs_data.json"

sys.path.insert(0, str(ROOT / "google_scholar_crawler"))
import test_crawler as tc  # noqa: E402  (reuses the same stubbed-DOM harness)


def find_node() -> str | None:
    configured = os.environ.get("NODE_BIN")
    if configured and pathlib.Path(configured).exists():
        return configured
    return shutil.which("node")


def fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "verify-live/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        # utf-8-sig tolerates a BOM.
        return json.loads(response.read().decode("utf-8-sig"))


def parse_updated(value: str | None) -> float:
    """Mirror of the page's updatedAt(): ISO 8601 first, legacy format second."""
    if not value:
        return float("-inf")
    text = str(value).strip()
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})", text)
    if not match:
        return float("-inf")
    import calendar

    parts = [int(part) for part in match.groups()]
    return float(
        calendar.timegm((parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], 0, 0, 0))
    )


def fetch_quietly(url: str) -> dict | None:
    try:
        print(f"  fetching {url}")
        return fetch(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  failed: {exc}")
        return None


def main() -> int:
    args = sys.argv[1:]
    paths = [a for a in args if not a.startswith("--")]

    if paths:
        source = paths[0]
        print(f"reading local file: {source}")
        live = json.loads(pathlib.Path(source).read_text(encoding="utf-8-sig"))
        chosen = "local file"
    else:
        # The page reads the CDN first and falls back to raw when the CDN copy is
        # stale (jsDelivr caches @branch URLs for ~12h and ignores query strings).
        # Mirror that here so the report matches what a visitor actually sees.
        print("fetching both endpoints (same logic the page uses):")
        cdn = fetch_quietly(CDN_URL)
        raw = fetch_quietly(RAW_URL)

        if cdn is None and raw is None:
            print("\nboth endpoints unreachable; pass a local gs_data.json instead.")
            return 2

        if cdn is None:
            live, chosen = raw, "raw.githubusercontent (CDN unreachable)"
        elif raw is None:
            live, chosen = cdn, "jsDelivr CDN (raw unreachable)"
        elif parse_updated(raw.get("updated")) > parse_updated(cdn.get("updated")):
            live, chosen = raw, "raw.githubusercontent (newer than the CDN copy)"
        else:
            live, chosen = cdn, "jsDelivr CDN"

        print(
            f"\n  CDN updated : {cdn and cdn.get('updated')}\n"
            f"  raw updated : {raw and raw.get('updated')}\n"
            f"  using       : {chosen}"
        )

    node = find_node()
    if node is None:
        print("Node.js not found; set NODE_BIN or add node to PATH.")
        return 2

    papers = (ROOT / "_data" / "publications.yml").read_text(encoding="utf-8")
    blocks = re.split(r"^\s*-\s+group:", papers, flags=re.MULTILINE)[1:]

    titles: list[str] = []
    alt_titles: list[str] = []
    pending: set[str] = set()
    for block in blocks:
        match = re.search(r'^\s*title:\s*"([^"]+)"', block, flags=re.MULTILINE)
        if not match:
            continue
        title = match.group(1)
        titles.append(title)
        # A paper that was renamed between preprint versions keeps the old title
        # here so the feed can still be matched; list items are the only `- "..."`
        # entries inside a block, so this picks up exactly citation_titles.
        alt_titles.append("|".join(re.findall(r'^\s*-\s+"([^"]+)"', block, flags=re.MULTILINE)))
        if re.search(r"^\s*not_in_feed:\s*true", block, flags=re.MULTILINE):
            pending.add(title)

    if not titles:
        print("no titles found in _data/publications.yml")
        return 2

    tc.INCLUDE = ROOT / "_includes" / "fetch_google_scholar_stats.html"
    output = tc.run_apply_data(node, live, titles, alt_titles)

    print("\n" + "=" * 78)
    print(f"feed source : {live.get('source')}")
    print(f"feed updated: {live.get('updated')}")
    print(f"total cites : {live.get('citedby')}   h-index: {live.get('hindex')}")
    print("=" * 78)
    print(f"#total_cit will render as: {output['total']!r}\n")

    matched = sum(1 for result in output["papers"] if result)
    pending_seen = sum(
        1 for title, result in zip(titles, output["papers"]) if not result and title in pending
    )
    unmatched = [
        title
        for title, result in zip(titles, output["papers"])
        if not result and title not in pending
    ]

    for title, result in zip(titles, output["papers"]):
        if not result and title in pending:
            print(f"  [--  ] {'(not indexed yet)':<20} {title[:58]}")
        else:
            flag = "OK  " if result else "MISS"
            print(f"  [{flag}] {result or '(nothing shown)':<20} {title[:58]}")

    print(f"\nmatched {matched}/{len(titles)} papers"
          + (f" ({pending_seen} not expected in this feed)" if pending_seen else ""))
    if unmatched:
        print("\nUnmatched -- either the paper is absent from the feed, or the title")
        print("in _data/publications.yml differs from what the source reports:")
        for title in unmatched:
            print(f"  - {title}")
        return 1

    print("every paper resolved to a citation count.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
