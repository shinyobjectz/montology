"""Brand logo lookup: quality vectors by name, instantly, with provenance.

LOOK UP, DON'T TRACE — the third leg of "scrape to measure, design to
make". A crawled site yields raster logos at whatever size the header
needed; these sources carry the real vector. Chain, in quality order:

1. **svgl** (svgl.app) — curated brand SVGs with wordmark variants and the
   brand's own assets page; a JSON search API.
2. **theSVG** (GLINCKER/thesvg) — 6,500+ full-color brand marks with the
   brand hex, categories and aliases, one module per icon on the npm CDN.
3. **Simple Icons** — thousands of monochrome brand glyphs on a
   predictable CDN, tintable by URL (`/<slug>/<hex>`).
4. **LobeHub icons** — AI/LLM product logos, served from the npm CDN.

A miss answers with the BROWSE fallback (SVG Repo — check the per-asset
license there) instead of an empty hand. Logos are trademarks:
fetched for work you are doing for or about that brand, and the source +
official brand-assets page ride along in the report so usage stays
answerable.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from .brand import brands_dir

_UA = {"User-Agent": "montology-logos/0.1 (+https://github.com/socialite-ml/montology)"}
_TIMEOUT = 15.0

BROWSE_FALLBACKS = (
    "not found in the API sources. Browse (check each asset's license): "
    "https://www.svgrepo.com/vectors/{q}/ · https://thesvg.com"
)

_THESVG_CDN = "https://cdn.jsdelivr.net/npm/@thesvg/icons@latest/dist"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _svgl(query: str) -> list[dict]:
    r = httpx.get("https://api.svgl.app", params={"search": query},
                  headers=_UA, timeout=_TIMEOUT)
    if r.status_code != 200:
        return []
    out = []
    for hit in r.json():
        routes: dict[str, str] = {}
        for kind in ("route", "wordmark"):
            v = hit.get(kind)
            if isinstance(v, str):
                routes[kind] = v
            elif isinstance(v, dict):
                for theme, url in v.items():
                    routes[f"{kind}-{theme}"] = url
        out.append({"source": "svgl", "title": hit.get("title", query),
                    "variants": routes, "brand_assets": hit.get("brandUrl", "")})
    return out


def _thesvg(query: str) -> list[dict]:
    url = f"{_THESVG_CDN}/{_slug(query)}.js"
    r = httpx.get(url, headers=_UA, timeout=_TIMEOUT, follow_redirects=True)
    if r.status_code != 200 or "export const svg" not in r.text:
        return []
    meta = dict(re.findall(r'export const (\w+) = "([^"]*)";', r.text))
    return [{"source": "thesvg", "title": meta.get("title", query),
             "variants": {"logo": url},
             "note": f"full color; brand hex #{meta['hex']}" if meta.get("hex") else "full color"}]


def _simpleicons(query: str) -> list[dict]:
    slug = _slug(query)
    url = f"https://cdn.simpleicons.org/{slug}"
    r = httpx.get(url, headers=_UA, timeout=_TIMEOUT)
    if r.status_code != 200 or "svg" not in r.headers.get("content-type", ""):
        return []
    return [{"source": "simple-icons", "title": query,
             "variants": {"glyph": url},
             "note": f"monochrome; tint with {url}/<hex>"}]


def _lobehub(query: str) -> list[dict]:
    slug = _slug(query)
    url = f"https://unpkg.com/@lobehub/icons-static-svg/icons/{slug}.svg"
    r = httpx.get(url, headers=_UA, timeout=_TIMEOUT, follow_redirects=True)
    if r.status_code != 200 or not r.text.lstrip().startswith("<svg"):
        return []
    return [{"source": "lobehub", "title": query, "variants": {"logo": url}}]


def logo_search(query: str) -> str:
    """Every variant the sources know for a brand name, as JSON — pick a
    variant, then fetch it into a project with logo_fetch."""
    hits: list[dict] = []
    for probe in (_svgl, _thesvg, _simpleicons, _lobehub):
        try:
            hits.extend(probe(query))
        except httpx.HTTPError:
            continue  # a dead source is a skipped source, never a crash
    if not hits:
        return BROWSE_FALLBACKS.format(q=query.replace(" ", "-"))
    return json.dumps(hits, indent=2)


def logo_fetch(project: str, query: str, variant: str = "", theme: str = "light") -> str:
    """The best vector into projects/<project>/assets/logos/, provenance
    beside it. `variant`: '' (the plain logo), 'wordmark', 'glyph' — themed
    variants resolve with `theme`."""
    try:
        found = json.loads(logo_search(query))
    except json.JSONDecodeError:
        return logo_search(query)  # the browse-fallback repair, verbatim

    want = variant or "route"
    ranked: list[tuple[dict, str, str]] = []
    for hit in found:
        for key, url in hit["variants"].items():
            score = (key == want or key == f"{want}-{theme}" or
                     (not variant and key in ("route", "logo", "glyph")))
            if score:
                ranked.append((hit, key, url))
    if not ranked:
        available = sorted({k for h in found for k in h["variants"]})
        return (f"no '{want}' variant for {query!r}. Available: "
                f"{', '.join(available)} — pass one as --variant.")

    hit, key, url = ranked[0]
    r = httpx.get(url, headers=_UA, timeout=_TIMEOUT, follow_redirects=True)
    if r.status_code != 200:
        return f"the source answered {r.status_code} for {url} — retry, or logo_search for alternatives."

    content = r.content
    if hit["source"] == "thesvg":  # the SVG rides inside a JS module
        m = re.search(r"export const svg = `(.*?)`;", r.text, re.DOTALL)
        if not m:
            return f"could not read the icon module at {url} — logo_search for alternatives."
        content = m.group(1).encode()

    dest_dir = brands_dir() / project / "assets" / "logos"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{_slug(query)}-{hit['source']}-{key}.svg"
    dest.write_bytes(content)

    prov = dest_dir / "provenance.json"
    entries = json.loads(prov.read_text()) if prov.exists() else []
    entries.append({"file": dest.name, "source": hit["source"], "url": url,
                    "brand_assets": hit.get("brand_assets", ""),
                    "note": hit.get("note", "")})
    prov.write_text(json.dumps(entries, indent=2))

    extra = f" (official brand assets: {hit['brand_assets']})" if hit.get("brand_assets") else ""
    return f"wrote {Path(dest).relative_to(brands_dir())} from {hit['source']}{extra}"
