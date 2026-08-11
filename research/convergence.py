"""The convergence experiment: does a codebase's concept-lexicon saturate?

Replays a repo's git history at N sample points. At each point, the
mined concept names (the same candidate filter the product uses:
recurring, non-noise, declared >= 2x) are ADOPTED into a growing
vocabulary; the next sample can only add names it has never seen.

What the numbers answer:

  * NATURAL CONVERGENCE — does "new concepts per 100 new declarations"
    decline as the codebase matures (a Heaps-style saturation of the
    concept lexicon), or does the vocabulary grow without settling?
  * THE BASELINE the enforcement question needs: the open experiment —
    does a guard+ontology loop bend this curve? — requires live agents
    writing code; this replay measures the un-enforced control.

Run:  uv run python research/convergence.py <repo> [samples]
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / ".monty" / m / "src")
                for m in ("core", "onto", "scan")]

from collections import Counter

from montology_scan.lint import _NOISE            # noqa: E402
from montology_scan.surface import declarations   # noqa: E402


def _git(repo: Path, *args: str) -> str:
    got = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True, timeout=300)
    if got.returncode != 0:
        raise RuntimeError(got.stderr.strip()[-200:])
    return got.stdout.strip()


def concepts(root: Path) -> tuple[set[str], int]:
    """The mined concept names at one point in history, + decl count."""
    surface = declarations(root)
    counts: Counter[str] = Counter()
    for d in surface["decls"]:
        low = d["name"].lower().lstrip("_")
        if low not in _NOISE and len(low) >= 4 and low.isalpha():
            counts[low] += 1
    return {n for n, c in counts.items() if c >= 2}, len(surface["decls"])


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    shas = _git(repo, "rev-list", "--first-parent", "--reverse", "HEAD").splitlines()
    step = max(1, (len(shas) - 1) // (n - 1))
    samples = shas[::step][:n]

    adopted: set[str] = set()
    prev_decls = 0
    print(f"{'date':<12}{'decls':>7}{'concepts':>10}{'new':>6}{'vocab':>7}"
          f"{'new/100decl':>13}")
    for sha in samples:
        date = _git(repo, "show", "-s", "--format=%cs", sha)
        with tempfile.TemporaryDirectory(prefix="conv-") as tmp:
            wt = Path(tmp) / "wt"
            _git(repo, "worktree", "add", "--detach", "-f", str(wt), sha)
            try:
                names, decls = concepts(wt)
            finally:
                _git(repo, "worktree", "remove", "--force", str(wt))
        new = names - adopted
        adopted |= names
        d_decls = decls - prev_decls
        rate = (100 * len(new) / d_decls) if d_decls > 0 else float("nan")
        print(f"{date:<12}{decls:>7}{len(names):>10}{len(new):>6}{len(adopted):>7}"
              f"{rate:>13.1f}")
        prev_decls = decls


if __name__ == "__main__":
    main()
