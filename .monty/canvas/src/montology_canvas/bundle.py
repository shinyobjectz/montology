"""The bundle is generated material, and gets the gate that fact requires.

The words skill taught this: a generated file with no check on it drifts, and
the drift is invisible precisely because the file looks authored. The canvas
bundle is worse than the skill in one way — it is minified, so a hand edit is
unreadable rather than merely undetected.

So the built asset carries the fingerprint of the SOURCE it was built from, and
lint recomputes. No Node is needed to check: the hash is over the source files,
not over a rebuild. A repo with no `canvas/` (every install that is not this
one) is not failed for lacking sources it was never shipped — it is silent,
which is the same rule the surface probes follow.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

STATIC = Path(__file__).resolve().parent / "static"
STAMP = STATIC / "BUILD.json"

# What the bundle is built FROM. node_modules and the lockfile are deliberately
# out: a dependency bump that changes no source changes no meaning, and a hash
# that moves for reasons nobody can see is a hash people learn to ignore.
SOURCES = ("index.html", "vite.config.js", "package.json")
SOURCE_DIR = "src"


def canvas_dir(root: Path | None = None) -> Path | None:
    """The UI sources, if this workspace has them. Only the montology repo does."""
    from montology_core import workspace_root

    d = (root or workspace_root()) / "canvas"
    return d if (d / "package.json").exists() else None


def source_fingerprint(canvas: Path) -> str:
    h = hashlib.sha256()
    files = [canvas / name for name in SOURCES if (canvas / name).exists()]
    files += sorted((canvas / SOURCE_DIR).rglob("*"))
    for f in files:
        if not f.is_file():
            continue
        h.update(str(f.relative_to(canvas)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def stamp(root: Path | None = None) -> str:
    """Record which sources produced the bundle now on disk. Run after a build."""
    canvas = canvas_dir(root)
    if canvas is None:
        return "no canvas/ sources here — nothing to stamp."
    if not (STATIC / "index.html").exists():
        return "no bundle to stamp. Repair: build it first (`just canvas`)."
    fp = source_fingerprint(canvas)
    STAMP.write_text(json.dumps({"source": fp}, indent=2) + "\n")
    return f"stamped the canvas bundle  source=sha256:{fp}"


def lint(root: Path | None = None) -> list[str]:
    """Deterministic, Node-free, exit-code-shaped. Joins the gate."""
    canvas = canvas_dir(root)
    if canvas is None:
        return []                      # not this repo; nothing to say

    if not (STATIC / "index.html").exists():
        return ["FAIL canvas: canvas/ has sources but no bundle is built. "
                "Repair: `just canvas`"]
    if not STAMP.exists():
        return ["FAIL canvas: the bundle carries no provenance — it cannot be "
                "told from one somebody edited. Repair: `just canvas`"]

    want = source_fingerprint(canvas)
    try:
        got = json.loads(STAMP.read_text()).get("source")
    except (OSError, ValueError):
        got = None
    if got != want:
        return [f"FAIL canvas: the bundle was built from source {got}, canvas/ is "
                f"now {want} — STALE. Repair: `just canvas`"]
    return [f"canvas: bundle current (source sha256:{want})"]
