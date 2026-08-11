"""`monty vitals` — the state of a repo's meaning, at a glance.

One fast pass (no history, no model calls beyond the optional semantic
audit) composing every instrument's current reading into a scorecard and
ONE verdict:

  * TENDED    — the gate passes, the vocabulary exists and is clean, the
                design system holds, the guard is complying;
  * DRIFTING  — meaning exists but is leaking: advisory collisions,
                rogue values, duplicate meanings, escapes;
  * UNTENDED  — no vocabulary at all while the code is asking for one,
                or a palette with no tokens.

Every verdict line carries its reason and its repair. `monty drift` is
the trajectory; vitals is the pulse — an org tracks the verdict per repo
the way it tracks CI.
"""

from __future__ import annotations

from pathlib import Path

from montology_core import workspace_root

from .guard import stats as guard_stats
from .lint import candidates as scan_candidates
from .lint import lint as scan_lint
from .styles import norm_color, style_surface


def vitals(root: Path | None = None) -> list[str]:
    from montology_ontology import tokens, words

    root = root or workspace_root()
    lines = [f"── {root.name}: vitals ────────────────────────────────────"]
    reasons_drifting: list[str] = []
    reasons_untended: list[str] = []

    # the gate
    report = scan_lint(root)
    verdict_line = report[-1]
    fails = sum(1 for r in report if r.startswith("FAIL"))
    warns = sum(1 for r in report if r.startswith("warn"))
    lines.append(("ok " if fails == 0 else "FAIL ") + f"gate: {verdict_line}")
    if fails:
        reasons_drifting.append(f"{fails} lint failure(s)")
    if warns:
        reasons_drifting.append(f"{warns} advisory collision(s)")

    # the vocabulary
    vocab = words()
    cands = scan_candidates(root, top=10)
    lines.append(f"vocabulary: {len(vocab)} word(s); code asking for {len(cands)} more"
                 + (f" (top: {', '.join(c['name'] for c in cands[:3])})" if cands else ""))
    if not vocab and len(cands) >= 5:
        reasons_untended.append(f"no words while the code asks for {len(cands)} "
                                "(monty scan --candidates, then onto add)")

    # the design system
    toks = tokens()
    styles = style_surface(root)
    tok_colors = {norm_color(t["value"]) for t in toks if t["category"] == "color"}
    rogues = [c for c, _ in styles["colors"].most_common() if c not in tok_colors]
    if styles["colors"]:
        lines.append(f"design: {len(toks)} token(s), {len(styles['colors'])} distinct "
                     f"color(s) in use, {len(rogues)} unnamed, "
                     f"{len(styles['arbitrary'])} escape(s)")
        if not toks:
            reasons_untended.append(f"{len(styles['colors'])} colors, zero tokens "
                                    "(monty design ingest — the theme becomes the law)")
        elif rogues:
            reasons_drifting.append(f"{len(rogues)} unnamed color(s) (monty lint names "
                                    "the nearest token for each)")
        if styles["arbitrary"]:
            reasons_drifting.append(f"{len(styles['arbitrary'])} arbitrary escape(s)")

    # duplicate meanings (soft — needs the [semantics] extra)
    try:
        from montology_ontology import semantic_audit

        dups = sum(1 for line in semantic_audit(candidates=cands).splitlines()
                   if "~" in line and line.startswith("note semantics:"))
        if dups:
            lines.append(f"semantics: {dups} colliding meaning(s) (monty onto audit)")
            reasons_drifting.append(f"{dups} duplicate meaning(s)")
    except Exception:  # noqa: BLE001
        pass

    # the guard
    for line in guard_stats(root):
        if not line.startswith("no guard history"):
            lines.append(line)

    if reasons_untended:
        verdict = "UNTENDED — " + "; ".join(reasons_untended)
    elif reasons_drifting:
        verdict = "DRIFTING — " + "; ".join(reasons_drifting)
    else:
        verdict = ("TENDED — the gate passes, the vocabulary holds, "
                   "nothing is leaking")
    lines.append(f"verdict: {verdict}")
    return lines
