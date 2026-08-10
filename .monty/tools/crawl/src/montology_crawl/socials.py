"""The full pull: index a brand across every category it lives in.

`brand_index` is the whole motion, each step degrading with its repair:

  1. DISCOVER — social handles read off the brand's own site (the footer
     is the registry the brand maintains itself) → `data/socials.json`.
  2. PULL — ScrapeCreators profile + recent posts per covered platform
     (tiktok, instagram, youtube) → `data/socials/<platform>.*.json`.
  3. FILL — post media downloaded into the book by category:
     `design/image/`, `design/video/` — bounded, with a ledger.
  4. INDEX — zoo embeddings (downloaded, on-device) over captions and
     images → the `brand_index` table in the warehouse, so a brand is
     SEARCHABLE: `SELECT ... FROM brand_index WHERE brand='x'` joins the
     book to everything else the marketer holds.

Vendor keys and model weights are both optional at every step — a missing
key skips the pull with the export line, missing weights skip the index
with the `monty zoo pull` line. What ran is what the report says ran.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from .brand import brands_dir

TEXT_MODEL = "text-bge-small"       # small, carried; override per call
IMAGE_MODEL = "visual-siglip2"      # text-query-only: indexed for text→image search

_UA = {"User-Agent": "Mozilla/5.0 (montology brand index)"}

_SOCIAL_PATTERNS = {
    "instagram": r"instagram\.com/([A-Za-z0-9_.]{2,30})",
    "tiktok": r"tiktok\.com/@([A-Za-z0-9_.]{2,24})",
    "youtube": r"youtube\.com/(?:@|c/|user/)([A-Za-z0-9_.-]{2,40})",
    "x": r"(?:twitter|x)\.com/([A-Za-z0-9_]{2,15})",
    "linkedin": r"linkedin\.com/company/([A-Za-z0-9-]{2,60})",
    "pinterest": r"pinterest\.com/([A-Za-z0-9_]{2,30})",
    "facebook": r"facebook\.com/([A-Za-z0-9.]{2,50})",
}
_NOT_HANDLES = {"share", "sharer", "intent", "hashtag", "explore", "reel",
                "watch", "channel", "search", "p", "pages", "policies", "legal"}


def discover_socials(url: str) -> dict[str, str]:
    """Handles from the brand's own homepage — the links they chose."""
    r = httpx.get(url if "://" in url else f"https://{url}",
                  headers=_UA, timeout=30, follow_redirects=True)
    found: dict[str, str] = {}
    for platform, pattern in _SOCIAL_PATTERNS.items():
        for m in re.finditer(pattern, r.text):
            handle = m.group(1).rstrip("/.")
            if handle.lower() not in _NOT_HANDLES and platform not in found:
                found[platform] = handle
    return found


def _walk_strings(data, keys: tuple[str, ...]) -> list[str]:
    """Every string under a key whose name contains one of `keys`."""
    out: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str) and v.strip() and any(h in k.lower() for h in keys):
                out.append(v.strip())
            else:
                out.extend(_walk_strings(v, keys))
    elif isinstance(data, list):
        for item in data:
            out.extend(_walk_strings(item, keys))
    return out


_TEXT_KEYS = ("caption", "title", "desc", "text", "bio", "signature")
_IMAGE_KEYS = ("display_url", "thumbnail", "cover", "image_url", "display_uri")
_VIDEO_KEYS = ("video_url", "play_addr", "download_addr", "playaddr")


def _download(urls: list[str], dest_dir: Path, stem: str, cap: int,
              max_bytes: int = 25_000_000) -> list[dict]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ledger, n = [], 0
    for u in urls:
        if n >= cap or not u.startswith("http"):
            continue
        try:
            r = httpx.get(u, headers=_UA, timeout=60, follow_redirects=True)
            if r.status_code != 200 or len(r.content) > max_bytes or len(r.content) < 1024:
                continue
            ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
                   "video/mp4": ".mp4"}.get(r.headers.get("content-type", "").split(";")[0])
            if ext is None:
                continue
            f = dest_dir / f"{stem}-{n}{ext}"
            f.write_bytes(r.content)
            ledger.append({"file": f.name, "source": u[:300], "bytes": len(r.content)})
            n += 1
        except httpx.HTTPError:
            continue
    return ledger


def _index_rows(brand: str, rows: list[tuple[str, str, str, list[float]]]) -> str:
    """(platform, kind, ref, vec) rows into the warehouse's brand_index."""
    from montology_warehouse import connect

    conn = connect()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS brand_index (brand VARCHAR, platform VARCHAR, "
        "kind VARCHAR, ref VARCHAR, content VARCHAR, vec FLOAT[])"
    )
    conn.execute("DELETE FROM brand_index WHERE brand = ?", [brand])
    for platform, kind, ref, content, vec in rows:  # type: ignore[misc]
        conn.execute("INSERT INTO brand_index VALUES (?,?,?,?,?,?)",
                     [brand, platform, kind, ref, content, vec])
    return f"indexed {len(rows)} row(s) into warehouse table brand_index (brand='{brand}')"


def brand_index(brand: str, posts_platforms: str = "tiktok,instagram,youtube",
                media_cap: int = 12, text_model: str = TEXT_MODEL,
                image_model: str = IMAGE_MODEL) -> str:
    """The full pull — discover, pull, fill, index. Every step reports."""
    root = brands_dir() / brand
    mf = root / "manifest.json"
    if not mf.exists():
        return (f"no brand book at brands/{brand} — run "
                f"`monty crawl audit <url>` and `monty brand scaffold {brand} audit.json` first")
    manifest = json.loads(mf.read_text())
    site = manifest.get("source", "")
    report: list[str] = []

    # 1. discover
    try:
        handles = discover_socials(site) if site else {}
    except httpx.HTTPError as e:
        handles = {}
        report.append(f"discover: could not reach {site} ({type(e).__name__})")
    (root / "data").mkdir(exist_ok=True)
    (root / "data" / "socials.json").write_text(json.dumps(handles, indent=1))
    report.append("discover: " + (", ".join(f"{p}:@{h}" for p, h in handles.items()) or
                                  "no social links found on the site"))

    # 2. pull + 3. fill
    from montology_scrapecreators.tools import creator_posts, creator_profile

    texts: list[tuple[str, str, str]] = []     # (platform, ref, content)
    images: list[tuple[str, Path]] = []        # (platform, file)
    sdir = root / "data" / "socials"
    sdir.mkdir(exist_ok=True)
    for platform in (p.strip() for p in posts_platforms.split(",")):
        handle = handles.get(platform)
        if not handle:
            continue
        profile = creator_profile(platform, handle)
        posts = creator_posts(platform, handle)
        if not profile.lstrip().startswith(("{", "[")):
            report.append(f"{platform}: {profile[:160]}")
            continue  # the repair (missing key, API answer) is the report line
        (sdir / f"{platform}.profile.json").write_text(profile)
        (sdir / f"{platform}.posts.json").write_text(posts)
        data = json.loads(posts) if posts.lstrip().startswith(("{", "[")) else {}
        for i, t in enumerate(dict.fromkeys(_walk_strings(data, _TEXT_KEYS))):
            if len(t) > 10:
                texts.append((platform, f"{platform}:{handle}:{i}", t[:2000]))
        img_ledger = _download(list(dict.fromkeys(_walk_strings(data, _IMAGE_KEYS))),
                               root / "design" / "image", f"social-{platform}", media_cap)
        vid_ledger = _download(list(dict.fromkeys(_walk_strings(data, _VIDEO_KEYS))),
                               root / "design" / "video", f"social-{platform}",
                               max(2, media_cap // 4))
        images += [(platform, root / "design" / "image" / e["file"]) for e in img_ledger]
        report.append(f"{platform}: @{handle} — {len(texts)} text(s), "
                      f"{len(img_ledger)} image(s), {len(vid_ledger)} video(s) pulled")

    # 4. index
    rows: list = []
    if texts:
        try:
            from montology_zoo import embed_text

            vecs = embed_text(text_model, [t for _, _, t in texts])
            rows += [(p, "text", ref, t, vecs[i].tolist())
                     for i, (p, ref, t) in enumerate(texts)]
        except Exception as e:  # noqa: BLE001
            report.append(f"text index skipped ({str(e)[:120]}) — repair: monty zoo pull {text_model}")
    if images:
        try:
            from montology_zoo import embed_image

            vecs = embed_image(image_model, [str(f) for _, f in images])
            rows += [(p, "image", str(f.relative_to(root)), "", vecs[i].tolist())
                     for i, (p, f) in enumerate(images)]
        except Exception as e:  # noqa: BLE001
            report.append(f"image index skipped ({str(e)[:120]}) — repair: monty zoo pull {image_model}")
    if rows:
        report.append(_index_rows(brand, rows))
    elif texts or images:
        pass  # the skip lines above carry the repair
    else:
        report.append("nothing to index yet — no posts pulled "
                      "(set SCRAPECREATORS_API_KEY for the social pull)")
    return "\n".join(report)
