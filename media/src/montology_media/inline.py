"""data_uri: inline a file for self-contained HTML — emails and artifacts."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


def data_uri(src: str, cap_kb: int = 512) -> str:
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    if p.stat().st_size > cap_kb * 1024:
        return (f"{src} is {p.stat().st_size // 1024} KB — over the {cap_kb} KB inline cap. "
                "Repair: resize/convert it first (monty convert image … --to webp).")
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
