"""Images: convert and resize via Pillow. WebP/PNG/JPEG cover the ad
formats; sizes come from the caller (the FORMATS table upstream)."""

from __future__ import annotations

from pathlib import Path

FORMATS = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP"}


def convert_image(src: str, to: str, quality: int = 85) -> str:
    from PIL import Image

    fmt = FORMATS.get(to.lower().lstrip("."))
    if fmt is None:
        return f"unknown target {to!r} — one of: {', '.join(FORMATS)}"
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    out = p.with_suffix(f".{to.lower().lstrip('.')}")
    img = Image.open(p)
    if fmt == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(out, fmt, quality=quality, optimize=True)
    return f"wrote {out} ({out.stat().st_size // 1024} KB, was {p.stat().st_size // 1024} KB)"


def resize_image(src: str, width: int, height: int = 0, cover: bool = True) -> str:
    """Resize to a frame. cover=True center-crops to fill exactly (the ad
    case); cover=False fits inside preserving aspect."""
    from PIL import Image

    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    img = Image.open(p)
    if height and cover:
        scale = max(width / img.width, height / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        left, top = (img.width - width) // 2, (img.height - height) // 2
        img = img.crop((left, top, left + width, top + height))
    else:
        img.thumbnail((width, height or width * 4), Image.LANCZOS)
    out = p.with_stem(f"{p.stem}-{img.width}x{img.height}")
    img.save(out)
    return f"wrote {out} ({img.width}x{img.height})"
