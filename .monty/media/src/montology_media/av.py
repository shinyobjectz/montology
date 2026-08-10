"""Audio/video through an INVOKED ffmpeg. Absent binary answers with the
repair; a failed run answers with ffmpeg's own last words."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_NO_FFMPEG = ("ffmpeg is not installed. Repair: `brew install ffmpeg` "
              "(or your platform's package), then retry.")


def _run(args: list[str], out: Path) -> str:
    if shutil.which("ffmpeg") is None:
        return _NO_FFMPEG
    r = subprocess.run(["ffmpeg", "-y", *args, str(out)],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        return f"ffmpeg failed: {r.stderr.strip().splitlines()[-1] if r.stderr else '?'}"
    return f"wrote {out} ({out.stat().st_size // 1024} KB)"


def to_wav16(src: str) -> str:
    """Anything with audio → 16 kHz mono wav — the zoo transcribe contract."""
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    return _run(["-i", str(p), "-ar", "16000", "-ac", "1"], p.with_suffix(".wav"))


def transcode(src: str, to: str) -> str:
    """Container/codec conversion by extension: mp4, webm, mov, mp3, m4a…"""
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    return _run(["-i", str(p)], p.with_suffix(f".{to.lstrip('.')}"))


def trim(src: str, start: str, duration: str) -> str:
    """Cut a clip: start/duration as seconds or HH:MM:SS."""
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    out = p.with_stem(f"{p.stem}-clip")
    return _run(["-ss", start, "-t", duration, "-i", str(p), "-c", "copy"], out)


def thumbnail(src: str, at: str = "1") -> str:
    """One frame as PNG — the video's poster/preview."""
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    return _run(["-ss", at, "-i", str(p), "-frames:v", "1"], p.with_suffix(".png"))


def extract_gif(src: str, start: str = "0", duration: str = "3", width: int = 480) -> str:
    """A short GIF from a video — the social preview format that autoplays anywhere."""
    p = Path(src).expanduser()
    if not p.exists():
        return f"no such file: {src}"
    out = p.with_suffix(".gif")
    return _run(["-ss", start, "-t", duration, "-i", str(p),
                 "-vf", f"fps=12,scale={width}:-1:flags=lanczos"], out)
