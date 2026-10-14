#!/usr/bin/env python3
"""Collect citation data for the academic homepage.

Two data sources, tried in order:

1. **Google Scholar** via the ``scholarly`` package. This is authoritative --
   it is the number the profile itself shows -- but Google aggressively
   rate-limits and CAPTCHA-walls datacenter IPs, so GitHub Actions frequently
   cannot reach it.

2. **OpenAlex** (public API, no key needed) matched by ORCID, as a fallback.
   Counts lag Google Scholar by a little, but the homepage keeps updating
   instead of freezing on stale numbers.

Both paths write the *same* JSON schema, so the page JavaScript never needs to
know which source ran:

    {
      "source": "google_scholar" | "openalex",
      "updated": "2026-10-14 09:12:03",
      "name": "Ningfeng Que",
      "citedby": 69,
      "hindex": 5,
      "i10index": 4,
      "publications": {
         "<any stable id>": {
            "bib": {"title": "...", "pub_year": "2025"},
            "num_citations": 12
         },
         ...
      }
    }

If *both* sources fail, nothing is written and the process exits 0, so the
workflow leaves the previously published numbers untouched rather than
replacing good data with zeros.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote

# The Scholar ID and ORCID are public information (they are literally in the
# profile URL), so they are used as defaults -- you do not have to configure any
# GitHub secret for this to work. Set the env vars to override them.
#
# Note: an undefined GitHub Actions secret is exported as an *empty string*, not
# as an unset variable, so "or default" is doing real work here.
def _env_or(name: str, default: str) -> str:
    return (os.environ.get(name) or "").strip() or default


SCHOLAR_ID = _env_or("GOOGLE_SCHOLAR_ID", "ZxrkoP4AAAAJ")
ORCID = _env_or("ORCID", "0009-0000-1790-1241")
MAILTO = _env_or("MAILTO", "queningfeng@stu.pku.edu.cn")

RESULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# Must stay in sync with normTitle() in _includes/fetch_google_scholar_stats.html
_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_ENTITY = re.compile(r"&[a-z]+;")
_TAGS = re.compile(r"<[^>]*>")


def norm_title(value: str | None) -> str:
    if not value:
        return ""
    value = _TAGS.sub(" ", str(value))
    value = _ENTITY.sub(" ", value)
    return _NON_ALNUM.sub("", value.lower())


def log(message: str) -> None:
    print(f"[crawler] {message}", flush=True)


def http_json(url: str, attempts: int = 4, timeout: int = 45):
    """GET a JSON document with a small backoff on transient failures."""
    last_error = None
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"acad-homepage-crawler/1.0 (mailto:{MAILTO})",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - we genuinely want to try again
            last_error = exc
            wait = 3 * (attempt + 1)
            log(f"    {type(exc).__name__}: {exc} -- retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"giving up on {url}: {last_error}")


# ---------------------------------------------------------------------------
# Source 1: Google Scholar
# ---------------------------------------------------------------------------
def from_google_scholar() -> dict | None:
    try:
        from scholarly import scholarly  # type: ignore
    except Exception as exc:  # noqa: BLE001
        log(f"  `scholarly` is not importable ({exc}); skipping Google Scholar.")
        return None

    log(f"  looking up author {SCHOLAR_ID} ...")
    try:
        author = scholarly.search_author_id(SCHOLAR_ID)
        author = scholarly.fill(
            author, sections=["basics", "indices", "counts", "publications"]
        )
    except Exception as exc:  # noqa: BLE001
        log(f"  Google Scholar lookup failed: {type(exc).__name__}: {exc}")
        return None

    publications = {}
    for index, publication in enumerate(author.get("publications", [])):
        bib = publication.get("bib", {}) or {}
        key = publication.get("author_pub_id") or bib.get("title") or f"pub-{index}"
        publications[key] = {
            "bib": {
                "title": bib.get("title", ""),
                "pub_year": str(bib.get("pub_year", "") or ""),
                "citation": bib.get("citation", ""),
            },
            "num_citations": publication.get("num_citations", 0) or 0,
        }

    if not publications:
        log("  Google Scholar returned no publications.")
        return None

    log(f"  got {len(publications)} publications from Google Scholar.")
    return {
        "source": "google_scholar",
        "name": author.get("name", ""),
        "citedby": author.get("citedby", 0),
        "hindex": author.get("hindex", 0),
        "i10index": author.get("i10index", 0),
        "publications": publications,
    }


# ---------------------------------------------------------------------------
# Source 2: OpenAlex (fallback)
# ---------------------------------------------------------------------------
def _works_by(filter_expression: str) -> list[dict]:
    payload = http_json(
        "https://api.openalex.org/works"
        f"?filter={filter_expression}&per_page=200&mailto={MAILTO}"
        "&select=id,doi,title,publication_year,cited_by_count"
    )
    return payload.get("results", [])


def from_openalex() -> dict | None:
    """Collect works through three filters and merge whatever they return.

    No single filter is sufficient, which is not obvious until you check:

    1. ``author.orcid`` -- misses papers whose authorship carries no ORCID.
    2. ``author.id``   -- misses papers OpenAlex never disambiguated into an
       author entity. The IJCAI 2024 paper literally has ``author.id: null`` on
       its "Ningfeng Que" authorship (OpenAlex also files it under Northeastern
       University in the US), so both of the above return 10 works and quietly
       drop it.
    3. ``raw_author_name.search`` -- a permissive byline text search, which does
       find it. It can match a namesake, but that is harmless here: the page only
       reads a citation count for titles it recognises, and a namesake will never
       share an exact normalised title with one of these papers.
    """
    log(f"  resolving OpenAlex author for ORCID {ORCID} ...")
    try:
        author_by_orcid = http_json(
            f"https://api.openalex.org/authors/https://orcid.org/{ORCID}"
            f"?mailto={MAILTO}"
        )
    except Exception as exc:  # noqa: BLE001
        log(f"  OpenAlex author lookup failed: {type(exc).__name__}: {exc}")
        return None

    author_id = (author_by_orcid.get("id") or "").rsplit("/", 1)[-1]
    display_name = (author_by_orcid.get("display_name") or "").strip()
    candidates: list[tuple[str, list[dict]]] = []

    try:
        candidates.append(("author.orcid", _works_by(f"author.orcid:{ORCID}")))
    except Exception as exc:  # noqa: BLE001
        log(f"  works-by-ORCID query failed: {type(exc).__name__}: {exc}")

    author_by_id = None
    if author_id:
        try:
            author_by_id = http_json(
                f"https://api.openalex.org/authors/{author_id}?mailto={MAILTO}"
            )
            candidates.append(
                ("author.id", _works_by(f"author.id:{author_id}"))
            )
        except Exception as exc:  # noqa: BLE001
            log(f"  works-by-author-id query failed: {type(exc).__name__}: {exc}")

    if display_name:
        try:
            candidates.append(
                (
                    "raw_author_name.search",
                    _works_by(f"raw_author_name.search:{quote(display_name)}"),
                )
            )
        except Exception as exc:  # noqa: BLE001
            log(f"  works-by-author-name query failed: {type(exc).__name__}: {exc}")

    if not candidates:
        log("  no OpenAlex query succeeded.")
        return None

    # Merge on the work identity, keeping the larger citation count when the two
    # queries disagree (e.g. a journal version and its preprint).
    merged: dict[str, dict] = {}
    for source_name, works in candidates:
        log(f"  {source_name}: {len(works)} works")
        for work in works:
            identity = (work.get("doi") or work.get("id") or "").lower()
            if not identity:
                continue
            previous = merged.get(identity)
            if previous is None or (work.get("cited_by_count") or 0) > (
                previous.get("cited_by_count") or 0
            ):
                merged[identity] = work

    publications = {}
    for work in merged.values():
        title = work.get("title") or ""
        if not title:
            continue
        key = (work.get("doi") or work.get("id") or title).rsplit("/", 1)[-1]
        publications[key] = {
            "bib": {
                "title": title,
                "pub_year": str(work.get("publication_year") or ""),
                "citation": "",
            },
            "num_citations": work.get("cited_by_count", 0) or 0,
        }

    if not publications:
        log("  OpenAlex returned no works.")
        return None

    # Prefer whichever author record knows about more work.
    author = author_by_orcid
    if author_by_id and (author_by_id.get("works_count") or 0) > (
        author_by_orcid.get("works_count") or 0
    ):
        author = author_by_id
    stats = (author or {}).get("summary_stats", {}) or {}

    log(f"  merged {len(publications)} unique works from OpenAlex.")
    return {
        "source": "openalex",
        "name": (author or {}).get("display_name", ""),
        "citedby": (author or {}).get("cited_by_count", 0),
        "hindex": stats.get("h_index", 0),
        "i10index": stats.get("i10_index", 0),
        "publications": publications,
    }


def main() -> int:
    log("collecting citation data")
    log("1/2 Google Scholar")
    data = from_google_scholar()

    if data is None:
        log("2/2 OpenAlex (fallback)")
        data = from_openalex()

    if data is None:
        log("Both sources failed. Leaving previously published data untouched.")
        return 0

    # ISO 8601 so the page can Date.parse() it reliably when deciding whether the
    # CDN handed back a stale cache. updated_display is only for the tooltip.
    now = datetime.now(timezone.utc)
    data["updated"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["updated_display"] = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Sanity check: never publish a payload that would blank out the homepage.
    titles = [p["bib"]["title"] for p in data["publications"].values()]
    matched = sum(1 for title in titles if norm_title(title))
    if matched == 0:
        log("Data has no usable titles. Refusing to publish.")
        return 0

    os.makedirs(RESULT_DIR, exist_ok=True)

    with open(os.path.join(RESULT_DIR, "gs_data.json"), "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)

    shields = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(data["citedby"]),
        "color": "9cf",
    }
    with open(
        os.path.join(RESULT_DIR, "gs_data_shieldsio.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(shields, handle, ensure_ascii=False, indent=2)

    log(
        f"wrote {len(data['publications'])} publications "
        f"(source={data['source']}, citedby={data['citedby']}, "
        f"h-index={data['hindex']}, i10={data['i10index']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
