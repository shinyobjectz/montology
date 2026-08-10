"""Creative production: formats, assets, and the grounded brief.

THE DOCTRINE THE USER NAMED: scraped components are BRAND GROUNDING, not
deliverables. An ad, an email, a landing page is NEW creative the agent
DESIGNS inside the measured system — tokens, voice, assets — never a
collage of scraped sections. Montology's half of the partnership is
deterministic: the format specs, the measured brand, the assets on disk,
and the gate; the agent's half is the design.

FORMATS are data (IAB display standards, the social sizes platforms
actually serve, remotion-ads' video formats, email width) so a deliverable
can be CHECKED against its format instead of eyeballed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

from .brand import COMPONENT_TYPES, brands_dir

# (name, width, height, use) — the sizes that actually run
FORMATS: dict[str, list[tuple[str, int, int, str]]] = {
    "banner": [  # IAB display
        ("medium-rectangle", 300, 250, "the workhorse; most inventory"),
        ("leaderboard", 728, 90, "top-of-page desktop"),
        ("wide-skyscraper", 160, 600, "sidebar desktop"),
        ("half-page", 300, 600, "high-impact sidebar"),
        ("billboard", 970, 250, "premium top-of-page"),
        ("mobile-banner", 320, 50, "mobile anchor"),
    ],
    "social": [
        ("square", 1080, 1080, "feed (IG/FB/LI)"),
        ("portrait", 1080, 1350, "IG feed, more screen"),
        ("story", 1080, 1920, "stories/reels covers"),
        ("landscape", 1200, 628, "link ads (FB/LI/X)"),
    ],
    "video": [  # remotion-ads' formats
        ("reel", 1080, 1920, "9:16 reels/tiktok/shorts"),
        ("square-video", 1080, 1080, "1:1 feed video"),
        ("landscape-video", 1920, 1080, "16:9 explainer/yt"),
    ],
    "email": [("email", 600, 0, "the standard render width; height flows")],
    "landing": [("landing", 0, 0, "responsive; no fixed frame")],
}

DELIVERABLE_TYPES = {"banner": "ad-banner", "social": "ad-social",
                     "video": "video-title", "email": "email-body", "landing": "page"}


def assets(brand: str, audit_json: str, cap: int = 16) -> str:
    """Download the brand's images into brands/<brand>/assets/ — bounded,
    deduped, provenance in assets.json. Local files are what Remotion and
    email builds consume; a hotlinked scrape is not an asset."""
    import httpx

    try:
        audit = json.loads(audit_json) if audit_json.strip().startswith("{") \
            else json.loads(Path(audit_json).read_text())
    except (json.JSONDecodeError, OSError) as e:
        return f"could not read the audit ({e}); pass brand_audit output or a path to it"

    root = brands_dir() / brand / "assets"
    root.mkdir(parents=True, exist_ok=True)
    base = audit.get("url", "")
    urls: list[str] = []
    if audit.get("logo"):
        urls.append(audit["logo"])
    urls += audit.get("images", [])
    seen, ledger, n = set(), [], 0
    for u in urls:
        full = urljoin(base, u)
        if full in seen or n >= cap:
            continue
        seen.add(full)
        name = re.sub(r"[^a-zA-Z0-9.-]", "_", full.rsplit("/", 1)[-1])[:60] or f"asset{n}"
        if "." not in name:
            name += ".img"
        try:
            r = httpx.get(full, timeout=30, follow_redirects=True)
            if r.status_code != 200 or len(r.content) > 3_000_000:
                continue
            (root / name).write_bytes(r.content)
            ledger.append({"file": f"assets/{name}", "source": full, "bytes": len(r.content)})
            n += 1
        except httpx.HTTPError:
            continue
    (root / "assets.json").write_text(json.dumps(ledger, indent=1))
    return f"pulled {n} asset(s) into projects/{brand}/assets/ (ledger: assets.json)"


def brief(brand: str, deliverable: str, goal: str) -> str:
    """The grounded creative brief — montology's half of the partnership.

    Everything measured, nothing invented: tokens, voice, assets, formats,
    the component manifest, and the laws the deliverable must pass. The
    agent designs FROM this; the gate checks the result."""
    if deliverable not in FORMATS:
        return f"deliverable must be one of: {', '.join(FORMATS)} (got {deliverable!r})"
    root = brands_dir() / brand
    if not (root / "manifest.json").exists():
        return (f"no library at projects/{brand} — run the pipeline first: "
                f"monty crawl audit <url> && monty brand scaffold {brand} audit.json")
    manifest = json.loads((root / "manifest.json").read_text())
    tokens = (root / "tokens.ts").read_text() if (root / "tokens.ts").exists() else ""
    ledger = []
    if (root / "assets/assets.json").exists():
        ledger = json.loads((root / "assets/assets.json").read_text())

    ctype = DELIVERABLE_TYPES[deliverable]
    spec = {
        "task": f"DESIGN a {deliverable} deliverable for {brand}: {goal}",
        "doctrine": (
            "This is a BRANDED INSTANTIATION, not a collage: design NEW creative "
            "inside the measured system. Use tokens.ts for every color and font "
            "(the lint gate rejects literal hex), the voice sample for tone, "
            "assets/ files for imagery, and existing components as REFERENCE for "
            "the brand's shapes — never paste scraped sections into an ad."
        ),
        "formats": [{"name": n, "width": w, "height": h, "use": u}
                    for n, w, h, u in FORMATS[deliverable]],
        "output_contract": (
            f"One React component per chosen format in deliverables/, file named "
            f"<name>-<width>x<height>.tsx for fixed-frame formats, registered as "
            f"type {ctype} via `monty brand register`, passing "
            f"`monty brand lint {brand}`. Fixed-frame components declare their "
            "exact width/height from the format table."
        ),
        "brand_tokens": tokens[:2400],
        "voice": manifest.get("voice_sample", "") or "(run crawl brand for a voice sample)",
        "assets": ledger[:12],
        "component_manifest": [{"name": c["name"], "type": c["type"], "status": c.get("status", "built")}
                               for c in manifest.get("components", [])],
        "then": f"monty brand lint {brand} — a FAIL line is your next edit.",
    }
    return ("GROUNDED CREATIVE BRIEF — the design is yours, the measurements are montology's.\n\n"
            + json.dumps(spec, indent=1))
