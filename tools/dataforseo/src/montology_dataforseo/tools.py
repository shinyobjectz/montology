"""The DataForSEO surface, deliberately small to start.

v3 API, https://api.dataforseo.com, HTTP Basic auth (login/password — the
same scheme the official Python client uses). Both endpoint paths and their
request fields verified against https://docs.dataforseo.com on 2026-08-10.
Two tools cover the questions marketers ask first; the rest of the catalogue
is added by decision, not by mirroring 107 routes into a prompt (a lesson
paid for elsewhere). Method lives in skills/dataforseo/, the official
vendor skill folded in.
"""

from __future__ import annotations

import json
import os

import httpx

BASE = "https://api.dataforseo.com/v3"


def _auth() -> tuple[str, str] | None:
    login = os.environ.get("DATAFORSEO_LOGIN", "")
    password = os.environ.get("DATAFORSEO_PASSWORD", "")
    return (login, password) if login and password else None


_NO_KEYS = (
    "DataForSEO credentials are not set. Repair: export DATAFORSEO_LOGIN and "
    "DATAFORSEO_PASSWORD (from https://app.dataforseo.com/api-access), then retry."
)


def _post(path: str, payload: list[dict]) -> str:
    auth = _auth()
    if auth is None:
        return _NO_KEYS
    r = httpx.post(f"{BASE}{path}", auth=auth, json=payload, timeout=120)
    if r.status_code != 200:
        return f"DataForSEO answered {r.status_code}: {r.text[:300]}"
    return json.dumps(r.json(), indent=1)[:20_000]


def serp_search(keyword: str, location: str = "United States", language: str = "en") -> str:
    """Live Google organic results for a keyword — who ranks, with what.

    Billed per request (one SERP of up to 10 results at the default depth),
    so batch questions before calling.

    Args:
        keyword: The search query, exactly as a user would type it (max 700 chars).
        location: Location name, e.g. "United States" or "London,England,United Kingdom".
        language: Two-letter language code.
    """
    return _post(
        "/serp/google/organic/live/advanced",
        [{"keyword": keyword, "location_name": location, "language_code": language}],
    )


def keyword_ideas(seed_keywords: str, location: str = "United States") -> str:
    """Keyword suggestions with search volume for one or more seed terms.

    Returns search_volume, cpc, competition and monthly_searches per keyword.
    The endpoint takes up to 20 seeds per call and the docs cap Google Ads
    live endpoints at 12 requests/minute — one call with many seeds, never a
    loop of single-seed calls.

    Args:
        seed_keywords: Comma-separated seed keywords, e.g. "ceramic pan, nonstick".
            Up to 20 are used; the rest are dropped.
        location: Location name for volume data (worldwide if the API gets none).
    """
    seeds = [k.strip() for k in seed_keywords.split(",") if k.strip()][:20]
    return _post(
        "/keywords_data/google_ads/keywords_for_keywords/live",
        [{"keywords": seeds, "location_name": location}],
    )


def mellea_tools() -> list:
    """The same functions, wrapped for a Mellea program's `tools=` list.

    Wrapped HERE, at the edge, because mellea's @tool returns a MelleaTool
    object — decorating the definitions would hide the plain callables the
    MCP server registers.
    """
    from mellea.backends.tools import tool

    return [tool(serp_search), tool(keyword_ideas)]
