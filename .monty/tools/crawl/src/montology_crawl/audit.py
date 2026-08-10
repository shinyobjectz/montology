"""brand_audit: the COMPLETE measured brand surface, multi-page.

Where brand_kit measures a homepage, the audit measures the SYSTEM: key
pages discovered from the nav, every linked stylesheet, and from that
corpus —

  * colors in every syntax (hex, rgb/rgba, hsl) with counts
  * the font stack, the font-SIZE scale, and weights
  * TAILWIND detection: utility-class frequency across class attributes;
    high density means the design system is legible from the markup itself,
    and the top utilities ARE the config (spacing scale, palette names,
    radii) — recorded, not guessed
  * spacing, radius and shadow tokens (counted values)
  * breakpoints (media-query min-widths)
  * the button recipe (the most repeated CTA class/style signature)
  * a COMPONENT INVENTORY: repeated section signatures across pages become
    typed candidates (nav, hero, card, footer…), each with its source HTML
    saved for the agent to convert — 'a complete component library from
    anything it can find' starts as a complete INVENTORY of what exists.

Everything is a count. The audit never names a color 'primary' — evidence
in, judgment left to the agent at the scaffold, gate at the lint.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from urllib.parse import urljoin, urlparse

from .tools import _crawl, _linked_css

TAILWIND_RE = re.compile(
    r"^(?:sm:|md:|lg:|xl:|2xl:|hover:|focus:|dark:)*"
    r"(?:bg|text|font|p[trblxy]?|m[trblxy]?|gap|space|w|h|min-w|max-w|flex|grid|items|justify|"
    r"rounded|shadow|border|ring|tracking|leading|z|top|left|right|bottom|inset|opacity|"
    r"overflow|object|aspect|col|row|order|self|place|divide|transition|duration|scale|"
    r"translate|rotate|cursor|select|whitespace|break|underline|uppercase|lowercase|italic)"
    r"(?:-[a-z0-9./\[\]%#-]+)?$"
)

SECTION_TYPE_HINTS = (
    ("header", "nav"), ("nav", "nav"), ("footer", "footer"),
)


def brand_audit(url: str, max_pages: int = 4) -> str:
    """The full surface as JSON. Heavier than brand_kit on purpose —
    minutes, not seconds, and worth it once per brand."""
    got = _crawl(url)
    if isinstance(got, str):
        return got
    home_md, home_html = got

    pages = {url: home_html}
    for link in _key_links(url, home_html)[: max_pages - 1]:
        sub = _crawl(link)
        if not isinstance(sub, str):
            pages[link] = sub[1]

    css = "\n".join(_linked_css(u, h) for u, h in pages.items())
    corpus = "\n".join(pages.values()) + "\n" + css

    audit = {
        "url": url,
        "pages_measured": list(pages),
        "colors": _colors(corpus),
        "fonts": _fonts(corpus, css),
        "tailwind": _tailwind(pages.values()),
        "spacing": _counted(css, r"(?:padding|margin|gap)\s*:\s*([0-9.]+(?:px|rem|em))", 10),
        "radii": _counted(css, r"border-radius\s*:\s*([^;}]{1,24})", 8),
        "shadows": _counted(css, r"box-shadow\s*:\s*([^;}]{1,80})", 5),
        "breakpoints": _counted(css, r"@media[^{]*?min-width\s*:\s*(\d+px)", 8),
        "buttons": _buttons(corpus),
        "components": _inventory(pages),
        "logo": (re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', home_html, re.I) or
                 re.search(r'<link[^>]+rel=["\'](?:icon|apple-touch-icon)[^>]*href=["\']([^"\']+)', home_html, re.I) or
                 [None, ""])[1] if True else "",
        "images": _images(pages),
        "voice_sample": home_md[:1200],
    }
    return json.dumps(audit, indent=1)


def _images(pages: dict[str, str]) -> list[str]:
    """Distinct content images across pages — the asset candidates. Icons,
    pixels and data URIs excluded; order preserved (hero images first)."""
    out, seen = [], set()
    for html in pages.values():
        for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
            if src.startswith("data:") or any(k in src.lower() for k in ("sprite", "icon", "pixel", "1x1")):
                continue
            if src not in seen:
                seen.add(src)
                out.append(src)
    return out[:40]


# One page per KIND beats three of the same shape: a listing, a product
# detail, an about page and a pricing page exercise different templates,
# which is what a design-system audit is measuring. Buckets rank by how
# much surface they typically reveal; noise pages never qualify.
_LINK_BUCKETS = (
    ("listing", ("collections", "category", "shop", "store", "catalog", "all-")),
    ("detail", ("/products/", "/product/", "/item/", "/p/")),
    ("about", ("about", "story", "our-", "brand", "mission")),
    ("pricing", ("pricing", "plans")),
    ("content", ("features", "solutions", "blog", "journal", "guide", "lookbook")),
)
_LINK_NOISE = ("cart", "checkout", "login", "account", "legal", "terms",
               "privacy", "gift", "policy", "faq", "help", "support")


def _key_links(base: str, html: str) -> list[str]:
    host = urlparse(base).netloc
    hrefs = re.findall(r'<a[^>]+href=["\']([^"\'#?]+)["\']', html, re.I)
    candidates: list[tuple[str, str]] = []  # (bucket, url) in DOM order
    seen = set()
    for h in hrefs:
        full = urljoin(base, h)
        p = urlparse(full)
        path = p.path.lower()
        if p.netloc != host or full.rstrip("/") == base.rstrip("/") or full in seen:
            continue
        if any(k in path for k in _LINK_NOISE):
            continue
        for bucket, keys in _LINK_BUCKETS:
            if any(k in path for k in keys):
                seen.add(full)
                candidates.append((bucket, full))
                break
    out, taken = [], set()
    for bucket, url in candidates:      # first pass: one per bucket, ranked
        if bucket not in taken:
            taken.add(bucket)
            out.append(url)
    out.extend(u for b, u in candidates if u not in out)  # then the rest
    return out


def _colors(corpus: str) -> list[dict]:
    c = Counter()
    for m in re.findall(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", corpus):
        c[m.lower()] += 1
    for m in re.findall(r"rgba?\([\d ,./%]+\)", corpus):
        c[re.sub(r"\s+", "", m)] += 1
    for m in re.findall(r"hsla?\([\d ,.%deg/]+\)", corpus):
        c[re.sub(r"\s+", "", m)] += 1
    return [{"value": v, "count": n} for v, n in c.most_common(20)]


def _fonts(corpus: str, css: str) -> dict:
    families = Counter(
        f.strip().strip("'\"")
        for decl in re.findall(r"font-family\s*:\s*([^;}]+)", corpus, re.I)
        for f in decl.split(",")
        if f.strip().strip("'\"").lower() not in
        ("sans-serif", "serif", "monospace", "system-ui", "inherit", "initial")
        and not f.strip().startswith("var(")
    )
    sizes = Counter(re.findall(r"font-size\s*:\s*([0-9.]+(?:px|rem))", css))
    weights = Counter(re.findall(r"font-weight\s*:\s*(\d{3})", css))
    faces = re.findall(r"@font-face\s*{[^}]*font-family\s*:\s*['\"]?([^'\";}]+)", css)
    return {
        "families": [{"family": f, "count": n} for f, n in families.most_common(8)],
        "size_scale": [{"size": s, "count": n} for s, n in sizes.most_common(10)],
        "weights": [{"weight": w, "count": n} for w, n in weights.most_common(6)],
        "font_faces": sorted(set(faces))[:8],
    }


def _tailwind(htmls) -> dict:
    classes = Counter()
    total = 0
    for html in htmls:
        for attr in re.findall(r'class=["\']([^"\']+)["\']', html):
            for cls in attr.split():
                total += 1
                if TAILWIND_RE.match(cls):
                    classes[cls] += 1
    density = (sum(classes.values()) / total) if total else 0.0
    return {
        "detected": density > 0.35,
        "utility_density": round(density, 3),
        "top_utilities": [{"class": c, "count": n} for c, n in classes.most_common(30)],
    }


def _counted(css: str, pattern: str, top: int) -> list[dict]:
    c = Counter(m.strip() for m in re.findall(pattern, css, re.I))
    return [{"value": v, "count": n} for v, n in c.most_common(top)]


def _buttons(corpus: str) -> list[dict]:
    sigs = Counter()
    for m in re.finditer(r"<(?:button|a)[^>]*class=[\"']([^\"']+)[\"']", corpus, re.I):
        cls = " ".join(sorted(m.group(1).split())[:8])
        if any(k in cls for k in ("btn", "button", "cta", "rounded", "bg-")):
            sigs[cls] += 1
    return [{"classes": s, "count": n} for s, n in sigs.most_common(5)]


def _inventory(pages: dict[str, str]) -> list[dict]:
    """Repeated section signatures across pages → typed component candidates
    with their source HTML kept (truncated) for conversion."""
    seen: dict[str, dict] = {}
    for page_url, html in pages.items():
        clean = re.sub(r"<(?:script|style|svg)\b[^>]*>.*?</(?:script|style|svg)>", "",
                       html, flags=re.S | re.I)
        for m in re.finditer(
            r"<(header|nav|section|article|aside|footer)\b([^>]*)>(.*?)</\1>",
            clean, re.S | re.I,
        ):
            tag = m.group(1).lower()
            cls = re.search(r'class=["\']([^"\']+)', m.group(2) or "")
            sig = tag + "|" + " ".join(sorted((cls.group(1) if cls else "").split()[:4]))
            body = m.group(0)
            ctype = dict(SECTION_TYPE_HINTS).get(tag)
            if ctype is None:
                low = body.lower()
                if "<h1" in low:
                    ctype = "hero"
                elif any(k in (cls.group(1).lower() if cls else "") for k in ("card", "grid", "col")):
                    ctype = "card"
                elif any(k in low for k in ("price", "plan", "/mo", "per month")):
                    ctype = "pricing"
                elif "<form" in low or "subscribe" in low:
                    ctype = "cta"
                else:
                    ctype = "feature"
            entry = seen.setdefault(sig, {
                "type": ctype, "signature": sig, "seen_on": [],
                "source_html": body[:5000],
            })
            if page_url not in entry["seen_on"]:
                entry["seen_on"].append(page_url)
    out = sorted(seen.values(), key=lambda e: -len(e["seen_on"]))[:24]
    for i, e in enumerate(out):
        e["candidate"] = f"{e['type']}-{i}"
    return out
