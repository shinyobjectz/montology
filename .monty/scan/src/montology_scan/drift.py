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

  * CONVERGENCE — mined concepts (the candidate filter: recurring,
    non-noise) adopted cumulatively across samples: `new` per sample and
    new-per-100-new-declarations. A tended lexicon's `new` column decays
    toward zero (measured: flask, 15 years, flat since 2019); an
    untended vocabulary never settles (measured: excalidraw's palette,
    ~10x fragmentation in two years).

Read the curves, not the rows. Samples check out via `git worktree`
(read-only, cleaned up), so the working tree is never touched. `--csv`
emits machine-readable rows for the research lane.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from montology_core import workspace_root

from collections import Counter

from .lint import _NOISE
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


def _concepts(surface: dict) -> set[str]:
    counts: Counter[str] = Counter()
    for d in surface["decls"]:
        low = d["name"].lower().lstrip("_")
        if low not in _NOISE and len(low) >= 4 and low.isalpha():
            counts[low] += 1
    return {n for n, c in counts.items() if c >= 2}


def measure_history(repo: Path | None = None, samples: int = 12) -> list[dict]:
    """One row per sampled commit, oldest first — the lexicon, the palette,
    and the convergence columns in a single replay."""
    repo = repo or workspace_root()
    rows: list[dict] = []
    adopted: set[str] = set()
    prev_decls = 0
    for sha in _samples(repo, samples):
        date = _git(repo, "show", "-s", "--format=%cs", sha)
        with tempfile.TemporaryDirectory(prefix="monty-drift-") as tmp:
            wt = Path(tmp) / "wt"
            _git(repo, "worktree", "add", "--detach", "-f", str(wt), sha)
            try:
                surface = declarations(wt)
                styles = style_surface(wt)
                names = {d["name"] for d in surface["decls"]}
                concepts = _concepts(surface)
                new = concepts - adopted
                adopted |= concepts
                d_decls = len(surface["decls"]) - prev_decls
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
                    "new_concepts": len(new),
                    "vocab": len(adopted),
                    "new_per_100": round(100 * len(new) / d_decls, 1) if d_decls > 0 else None,
                })
                prev_decls = len(surface["decls"])
            finally:
                _git(repo, "worktree", "remove", "--force", str(wt))
    return rows


def csv(rows: list[dict]) -> list[str]:
    """Machine-readable, for the research lane."""
    cols = ["sha", "date", "files", "decls", "names", "ttr", "colors",
            "color_uses", "spacing", "escapes", "new_concepts", "vocab", "new_per_100"]
    return [",".join(cols)] + [
        ",".join("" if r.get(c) is None else str(r.get(c, "")) for c in cols)
        for r in rows]


def render(rows: list[dict]) -> list[str]:
    if not rows:
        return ["no history to sample."]
    head = (f"{'date':<12}{'decls':>7}{'names':>7}{'ttr':>7}{'colors':>8}"
            f"{'spacing':>9}{'new':>6}{'vocab':>7}")
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
                     f"{r['colors']:>8}{r['spacing']:>9}{r['new_concepts']:>6}"
                     f"{r['vocab']:>7}{marks}")
        prev = r
    first, last = rows[0], rows[-1]
    if last["colors"] > first["colors"]:
        lines.append(f"note: the palette grew {first['colors']} → {last['colors']} distinct "
                     "colors — a design vocabulary nobody is tending grows with the code")
    tail_new = [r["new_concepts"] for r in rows[-3:]]
    converged = rows[-1]["vocab"] > 0 and sum(tail_new) <= max(3, rows[-1]["vocab"] * 0.05)
    lines.append(("note: the concept lexicon has CONVERGED — new concepts per sample "
                  f"decayed to {tail_new} (a tended vocabulary settles)") if converged else
                 ("note: the concept lexicon is still growing — recent samples added "
                  f"{tail_new} new concepts (a vocabulary that never settles is one "
                  "nobody is tending)"))
    lines.append(f"drift: {len(rows)} samples, lexicon {first['names']} → {last['names']} names, "
                 f"concept vocab {rows[-1]['vocab']}, ttr {first['ttr']} → {last['ttr']}")
    return lines
