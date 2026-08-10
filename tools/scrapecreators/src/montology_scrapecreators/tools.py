"""The ScrapeCreators surface — public creator data, platform by platform.

https://api.scrapecreators.com, key in the x-api-key header. Endpoint paths
verified against the official OpenAPI spec
(https://docs.scrapecreators.com/openapi.json, fetched 2026-08-10): they are
per-platform — TikTok, Instagram and YouTube each name their profile and
posts routes differently — so the tools dispatch through a table. Method
lives in skills/scrapecreators/, the official vendor skill folded in.
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

# Verified per-endpoint at https://docs.scrapecreators.com/{path}/openapi.json.
# Every route below takes a `handle` query param (without the @); YouTube also
# accepts channelId or url.
_PROFILE_PATHS = {
    "tiktok": "/v1/tiktok/profile",
    "instagram": "/v1/instagram/profile",
    "youtube": "/v1/youtube/channel",
}
_POSTS_PATHS = {
    "tiktok": "/v3/tiktok/profile/videos",
    "instagram": "/v2/instagram/user/posts",
    "youtube": "/v1/youtube/channel-videos",
}


def _unknown_platform(platform: str) -> str:
    return (
        f"Platform {platform!r} is not covered by this tool. Repair: pass one "
        "of tiktok, instagram, youtube — or reach the wider ScrapeCreators "
        "surface (110+ endpoints) described in the scrapecreators skill."
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
        handle: The creator's handle, without the @ (for YouTube, the channel
            handle, e.g. "ThePatMcAfeeShow").
    """
    path = _PROFILE_PATHS.get(platform.lower().strip())
    if path is None:
        return _unknown_platform(platform)
    return _get(path, {"handle": handle.lstrip("@")})


def creator_posts(platform: str, handle: str) -> str:
    """One page of a creator's most recent public posts, with engagement counts.

    The platform decides the page size; the response carries a cursor
    (max_cursor / next_max_id / continuationToken by platform) that the wider
    API accepts for further pages. Field names differ per platform —
    normalise before comparing across platforms.

    Args:
        platform: One of tiktok, instagram, youtube.
        handle: The creator's handle, without the @.
    """
    p = platform.lower().strip()
    path = _POSTS_PATHS.get(p)
    if path is None:
        return _unknown_platform(platform)
    params: dict = {"handle": handle.lstrip("@")}
    if p == "youtube":
        # Adds like + comment counts and the description to each video.
        params["includeExtras"] = "true"
    return _get(path, params)


def mellea_tools() -> list:
    """The same functions, wrapped for a Mellea program's `tools=` list.

    Wrapped HERE, at the edge, because mellea's @tool returns a MelleaTool
    object — decorating the definitions would hide the plain callables the
    MCP server registers.
    """
    from mellea.backends.tools import tool

    return [tool(creator_profile), tool(creator_posts)]
