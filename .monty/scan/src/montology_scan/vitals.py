"""`monty vitals` — the state of a repo's meaning, at a glance.

One fast pass (no history, no model calls beyond the optional semantic
audit) composing every instrument's current reading into a scorecard and
ONE verdict:

  * TENDED    — the gate passes, the vocabulary exists and is clean, the
                design system holds, nothing is leaking;
  * DRIFTING  — meaning exists but is leaking: lint failures, advisory
                collisions, rogue values, duplicate meanings, escapes;
  * UNTENDED  — no vocabulary at all while the code is asking for one,
                or a palette with no tokens. Untended outranks drifting:
                a repo that has not started is a different fact from one
                that is losing.

Every verdict line carries its reason and its repair. `monty drift` is
the trajectory; vitals is the pulse — an org tracks the verdict per repo
the way it tracks CI (`--strict` exits 1 unless TENDED; `--json` is the
dashboard shape).
"""

from __future__ import annotations

import json as json_mod
from pathlib import Path

from montology_core import workspace_root

from .guard import stats as guard_stats
from .lint import candidates as scan_candidates
from .lint import lint as scan_lint
from .styles import norm_color, style_surface


def build_vitals(root: Path | None = None) -> dict:
    """Every instrument's current reading, composed. Deterministic except
    the soft semantic-audit section; every absent capability degrades to
    an absent section, never an error."""
    from montology_ontology import pinned_upstream, tokens, words

    root = root or workspace_root()
    reasons_drifting: list[str] = []
    reasons_untended: list[str] = []
    r: dict = {"name": root.name, "root": str(root)}

    # the gate
    report = scan_lint(root)
    fails = sum(1 for line in report if line.startswith("FAIL"))
    warns = sum(1 for line in report if line.startswith("warn"))
    r["gate"] = {"ok": fails == 0, "failures": fails, "advisory_collisions": warns,
                 "summary": report[-1]}
    if fails:
        reasons_drifting.append(f"{fails} lint failure(s) (monty lint)")
    if warns:
        reasons_drifting.append(f"{warns} advisory collision(s)")

    # the vocabulary
    vocab = words()
    cands = scan_candidates(root, top=10)
    r["vocabulary"] = {"words": len(vocab), "candidates": len(cands),
                       "top_candidates": [c["name"] for c in cands[:3]]}
    if not vocab and len(cands) >= 5:
        reasons_untended.append(f"no words while the code asks for {len(cands)} "
                                "(monty scan --candidates, then onto add)")

    # the design system
    toks = tokens()
    styles = style_surface(root)
    tok_colors = {norm_color(t["value"]) for t in toks if t["category"] == "color"}
    rogues = [c for c, _ in styles["colors"].most_common() if c not in tok_colors]
    r["design"] = {"tokens": len(toks), "colors": len(styles["colors"]),
                   "unnamed": len(rogues), "escapes": len(styles["arbitrary"])}
    if styles["colors"]:
        if not toks:
            reasons_untended.append(f"{len(styles['colors'])} colors, zero tokens "
                                    "(monty design ingest — the theme becomes the law)")
        elif rogues:
            reasons_drifting.append(f"{len(rogues)} unnamed color(s) (monty lint "
                                    "names the nearest token for each)")
        if styles["arbitrary"]:
            reasons_drifting.append(f"{len(styles['arbitrary'])} arbitrary escape(s)")

    # duplicate meanings (soft — needs the [semantics] extra)
    r["semantics"] = None
    try:
        from montology_ontology import semantic_audit

        audit = semantic_audit(candidates=cands)
        if not audit.startswith("semantic analysis needs"):
            dups = sum(1 for line in audit.splitlines()
                       if "~" in line and line.startswith("note semantics:"))
            r["semantics"] = {"colliding_meanings": dups}
            if dups:
                reasons_drifting.append(f"{dups} duplicate meaning(s) (monty onto audit)")
    except Exception:  # noqa: BLE001
        pass

    # the guard: wired? complying?
    settings = root / ".claude" / "settings.json"
    wired = settings.exists() and "monty guard" in settings.read_text()
    stats_lines = [line for line in guard_stats(root)
                   if not line.startswith("no guard history")]
    r["guard"] = {"wired": wired, "stats": stats_lines}

    # the org
    r["upstream"] = pinned_upstream(root)

    if reasons_untended:
        state, verdict = "untended", "UNTENDED — " + "; ".join(reasons_untended)
    elif reasons_drifting:
        state, verdict = "drifting", "DRIFTING — " + "; ".join(reasons_drifting)
    else:
        state, verdict = "tended", ("TENDED — the gate passes, the vocabulary "
                                    "holds, nothing is leaking")
    r["state"], r["verdict"] = state, verdict
    r["reasons"] = reasons_untended + reasons_drifting
    return r


def render_vitals(r: dict) -> list[str]:
    lines = [f"── {r['name']}: vitals ────────────────────────────────────"]
    g = r["gate"]
    lines.append(("ok " if g["ok"] else "FAIL ") + f"gate: {g['summary']}")
    v = r["vocabulary"]
    lines.append(f"vocabulary: {v['words']} word(s); code asking for {v['candidates']} more"
                 + (f" (top: {', '.join(v['top_candidates'])})" if v["top_candidates"] else ""))
    d = r["design"]
    if d["colors"]:
        lines.append(f"design: {d['tokens']} token(s), {d['colors']} distinct color(s) "
                     f"in use, {d['unnamed']} unnamed, {d['escapes']} escape(s)")
    if r["semantics"] and r["semantics"]["colliding_meanings"]:
        lines.append(f"semantics: {r['semantics']['colliding_meanings']} colliding "
                     "meaning(s) (monty onto audit)")
    lines.append("firewall: " + ("wired — agents cannot write drift" if r["guard"]["wired"]
                                 else "not wired (monty init installs the hook)"))
    lines.extend(r["guard"]["stats"])
    if r["upstream"]:
        lines.append(f"org: inheriting from {r['upstream']} (monty onto pull refreshes)")
    lines.append(f"verdict: {r['verdict']}")
    return lines


def vitals(root: Path | None = None) -> list[str]:
    return render_vitals(build_vitals(root))


def vitals_json(root: Path | None = None) -> str:
    return json_mod.dumps(build_vitals(root), indent=2)
