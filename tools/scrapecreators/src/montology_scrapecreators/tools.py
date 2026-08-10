"""The ScrapeCreators surface — public creator data, platform by platform.

https://api.scrapecreators.com, key in the x-api-key header. Endpoint paths
follow the official docs (https://docs.scrapecreators.com); the two tools
here cover profile and recent posts, the first questions asked of any
creator. Fold the official skill into skills/scrapecreators/ for method.
"""

from __future__ import annotations

import json
import os

import httpx

BASE = "https://api.scrapecreators.com"

_NO_KEY = (
    "ScrapeCreators key is not set. Repair: export SCRAPECREATORS_API_KEY "
    "(from https://scrapecreators.com), then retry."
)


def _get(path: str, params: dict) -> str:
    key = os.environ.get("SCRAPECREATORS_API_KEY", "")
    if not key:
        return _NO_KEY
    r = httpx.get(f"{BASE}{path}", params=params, headers={"x-api-key": key}, timeout=120)
    if r.status_code != 200:
        return f"ScrapeCreators answered {r.status_code}: {r.text[:300]}"
    return json.dumps(r.json(), indent=1)[:20_000]


def creator_profile(platform: str, handle: str) -> str:
    """A creator's public profile — followers, bio, links.

    Args:
        platform: One of tiktok, instagram, youtube.
        handle: The creator's handle, without the @.
    """
    return _get(f"/v1/{platform.lower().strip()}/profile", {"handle": handle.lstrip("@")})


def creator_posts(platform: str, handle: str, count: int = 20) -> str:
    """A creator's recent public posts with engagement counts.

    Args:
        platform: One of tiktok, instagram, youtube.
        handle: The creator's handle, without the @.
        count: How many recent posts (max 50).
    """
    return _get(
        f"/v1/{platform.lower().strip()}/posts",
        {"handle": handle.lstrip("@"), "count": min(int(count), 50)},
    )


def mellea_tools() -> list:
    """The same functions, wrapped for a Mellea program's `tools=` list.

    Wrapped HERE, at the edge, because mellea's @tool returns a MelleaTool
    object — decorating the definitions would hide the plain callables the
    MCP server registers.
    """
    from mellea.backends.tools import tool

    return [tool(creator_profile), tool(creator_posts)]
