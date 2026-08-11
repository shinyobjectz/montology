"""`monty drift` — the telescope: meaning-drift over a repo's history.

Structural decay under AI assistance is measured (GitClear: duplication
up 8x, churn doubled). The SEMANTIC dimension is not: how fast does a
codebase's lexicon grow, when does its palette fragment, what did the
second gray arrive next to? This instrument samples the git history at N
evenly spaced commits and measures, at each point:

  * declarations, distinct declared names, and the type-token ratio
    (distinct/total — falling TTR means more repetition of the same
    names; rising distinct-per-KLOC means lexicon sprawl);
  * distinct colors and their use count, distinct spacing values,
    Tailwind arbitrary escapes — the design vocabulary's fragmentation.

Read the curves, not the rows: a palette that grows linearly with code
size is a design system losing; a lexicon whose growth never saturates
is a vocabulary nobody is tending. Samples check out via `git worktree`
(read-only, cleaned up), so the working tree is never touched.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from montology_core import workspace_root

from .styles import style_surface
from .surface import declarations


def _git(repo: Path, *args: str) -> str:
    got = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True, timeout=300)
    if got.returncode != 0:
        raise RuntimeError(got.stderr.strip()[-200:])
    return got.stdout.strip()


def _samples(repo: Path, n: int) -> list[str]:
    shas = _git(repo, "rev-list", "--first-parent", "--reverse", "HEAD").splitlines()
    if len(shas) <= n:
        return shas
    step = (len(shas) - 1) / (n - 1)
    return [shas[round(i * step)] for i in range(n)]


def measure_history(repo: Path | None = None, samples: int = 12) -> list[dict]:
    """One row per sampled commit, oldest first."""
    repo = repo or workspace_root()
    rows: list[dict] = []
    for sha in _samples(repo, samples):
        date = _git(repo, "show", "-s", "--format=%cs", sha)
        with tempfile.TemporaryDirectory(prefix="monty-drift-") as tmp:
            wt = Path(tmp) / "wt"
            _git(repo, "worktree", "add", "--detach", "-f", str(wt), sha)
            try:
                surface = declarations(wt)
                styles = style_surface(wt)
                names = {d["name"] for d in surface["decls"]}
                rows.append({
                    "sha": sha[:8], "date": date,
                    "files": surface["files"],
                    "decls": len(surface["decls"]),
                    "names": len(names),
                    "ttr": round(len(names) / max(1, len(surface["decls"])), 3),
                    "colors": len(styles["colors"]),
                    "color_uses": sum(styles["colors"].values()),
                    "spacing": len(styles["spacing"]),
                    "escapes": len(styles["arbitrary"]),
                })
            finally:
                _git(repo, "worktree", "remove", "--force", str(wt))
    return rows


def render(rows: list[dict]) -> list[str]:
    if not rows:
        return ["no history to sample."]
    head = f"{'date':<12}{'decls':>7}{'names':>7}{'ttr':>7}{'colors':>8}{'spacing':>9}{'escapes':>9}"
    lines = ["── drift: the lexicon and the palette over time ──────────", head]
    prev = None
    for r in rows:
        marks = ""
        if prev:
            if r["colors"] >= prev["colors"] * 1.5 and r["colors"] - prev["colors"] >= 5:
                marks += "  ← palette fragmenting"
            if prev["decls"] and r["names"] / max(1, r["decls"]) > 0 and \
                    (r["names"] - prev["names"]) > (r["decls"] - prev["decls"]) * 0.8 \
                    and r["decls"] > prev["decls"]:
                marks += "  ← lexicon sprawl"
        lines.append(f"{r['date']:<12}{r['decls']:>7}{r['names']:>7}{r['ttr']:>7}"
                     f"{r['colors']:>8}{r['spacing']:>9}{r['escapes']:>9}{marks}")
        prev = r
    first, last = rows[0], rows[-1]
    if last["colors"] > first["colors"]:
        lines.append(f"note: the palette grew {first['colors']} → {last['colors']} distinct "
                     "colors — a design vocabulary nobody is tending grows with the code")
    growth = last["names"] - first["names"]
    lines.append(f"drift: {len(rows)} samples, lexicon {first['names']} → {last['names']} "
                 f"names (+{growth}), ttr {first['ttr']} → {last['ttr']}")
    return lines
