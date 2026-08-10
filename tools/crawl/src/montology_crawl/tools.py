"""The crawl surface: three plain functions, mellea edge at the bottom.

Same conventions as the other tools packages: plain callables the MCP
server registers directly, function-local heavy imports (crawl4ai pulls
Playwright), errors that carry their repair, output capped so a page cannot
flood a context window.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections import Counter

_NO_BROWSER = (
    "The crawler's browser is not installed. Repair: run `montology crawl setup` "
    "once (downloads Chromium for Playwright), then retry."
)


def _crawl(url: str) -> tuple[str, str] | str:
    """(markdown, html) for one URL, or a repair string."""
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return "montology-crawl is not installed in this environment. Repair: uv sync"

    async def run():
        async with AsyncWebCrawler(verbose=False) as crawler:
            r = await crawler.arun(url=url)
            return (r.markdown or "", r.html or "")

    try:
        return asyncio.run(run())
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "playwright" in msg.lower() and "install" in msg.lower():
            return _NO_BROWSER
        return f"crawl failed for {url}: {type(e).__name__}: {msg[:300]}"


def fetch_page(url: str) -> str:
    """One page as clean, LLM-ready markdown.

    Args:
        url: The page to fetch (renders JavaScript; use for any public page).
    """
    got = _crawl(url)
    if isinstance(got, str):
        return got
    markdown, _ = got
    return markdown[:40_000] or "(the page rendered empty — it may require login or block automation)"


def brand_kit(url: str) -> str:
    """A brand's visual identity from its homepage: colors, fonts, logo, voice.

    Deterministic extraction — counted from the page's own CSS and metadata,
    never guessed. The counts travel with the answer so a designer (or the
    agent) can see WHY a color made the kit.

    Args:
        url: The brand's homepage.
    """
    got = _crawl(url)
    if isinstance(got, str):
        return got
    markdown, html = got

    # THE PALETTE LIVES IN LINKED STYLESHEETS, not the HTML — counting only
    # inline styles measured the crumbs and missed the meal (caught in
    # review before any real site was measured). Fetch the site's own CSS,
    # bounded: same-ish origin resolution, 8 sheets, 300 KB each.
    css = _linked_css(url, html)
    corpus = html + "\n" + css
    colors = Counter(c.lower() for c in re.findall(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", corpus))
    fonts = Counter(
        f.strip().strip("'\"")
        for decl in re.findall(r"font-family\s*:\s*([^;}]+)", corpus, re.I)
        for f in decl.split(",")
        if f.strip().strip("'\"").lower() not in
        ("sans-serif", "serif", "monospace", "system-ui", "inherit", "initial", "var")
        and not f.strip().startswith("var(")
    )

    def meta(prop: str) -> str:
        m = re.search(
            rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']+)', html, re.I
        ) or re.search(
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{prop}["\']', html, re.I
        )
        return m.group(1) if m else ""

    logo = ""
    m = re.search(r'<link[^>]+rel=["\'](?:icon|apple-touch-icon)[^>]*href=["\']([^"\']+)', html, re.I)
    if m:
        logo = m.group(1)

    kit = {
        "url": url,
        "stylesheets_counted": corpus.count("\n") > html.count("\n"),
        "title": meta("og:site_name") or meta("og:title"),
        "description": meta("og:description") or meta("description"),
        "logo": meta("og:image") or logo,
        "colors": [{"hex": c if c.startswith("#") else f"#{c}", "count": n}
                   for c, n in colors.most_common(12)],
        "fonts": [{"family": f, "count": n} for f, n in fonts.most_common(8)],
        "voice_sample": markdown[:1_500],
    }
    return json.dumps(kit, indent=1)


def _linked_css(base_url: str, html: str, cap: int = 8) -> str:
    """Fetch the page's linked stylesheets (bounded), for honest counting."""
    import urllib.parse

    import httpx

    hrefs = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html, re.I)
    hrefs += re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']stylesheet["\']', html, re.I)
    out = []
    for href in dict.fromkeys(hrefs)[:cap] if isinstance(hrefs, dict) else list(dict.fromkeys(hrefs))[:cap]:
        try:
            got = httpx.get(urllib.parse.urljoin(base_url, href), timeout=15,
                            follow_redirects=True)
            if got.status_code == 200 and len(got.text) < 300_000:
                out.append(got.text)
        except httpx.HTTPError:
            continue
    return "\n".join(out)


def page_sections(url: str) -> str:
    """A page split into its top-level sections — raw material for components.

    Each section is cleaned HTML (scripts stripped) the agent turns into a
    React component for the brand's library; pair with brand_kit so the
    components use the brand's tokens. See the brand-crawl skill for the
    method.

    Args:
        url: The page whose sections to extract.
    """
    got = _crawl(url)
    if isinstance(got, str):
        return got
    _, html = got
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.S | re.I)

    sections = re.findall(
        r"<(header|nav|main|section|article|aside|footer)\b.*?</\1>", html, re.S | re.I
    ) and re.finditer(
        r"<(header|nav|main|section|article|aside|footer)\b(.*?)</\1>", html, re.S | re.I
    )
    out, budget = [], 36_000
    for i, m in enumerate(sections or []):
        chunk = m.group(0).strip()
        chunk = chunk if len(chunk) <= 6_000 else chunk[:6_000] + "\n<!-- …truncated -->"
        if budget - len(chunk) < 0:
            out.append(f"<!-- {i + 1}+ further sections omitted for budget; call again per-URL -->")
            break
        budget -= len(chunk)
        out.append(f"<!-- section {i + 1}: <{m.group(1).lower()}> -->\n{chunk}")
    return "\n\n".join(out) or "(no semantic sections found — the page may be one div soup; use fetch_page)"


def setup() -> str:
    """Install the crawler's browser (one-time)."""
    import subprocess
    import sys

    r = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True, text=True, timeout=600,
    )
    return "browser installed" if r.returncode == 0 else f"install failed: {r.stderr[-400:]}"


def mellea_tools() -> list:
    """The same functions, wrapped for a Mellea program's `tools=` list."""
    from mellea.backends.tools import tool

    return [tool(fetch_page), tool(brand_kit), tool(page_sections)]
