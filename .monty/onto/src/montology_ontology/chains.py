"""Where a term ends up: chains, orphans, and rulings that contradict.

A route is one hop. Two hops is where the interesting failure lives:
`workspace → org` in code, and `org → Studio` on the surface, so a reader
following the ledger from `workspace` has to know which register they are
standing in to know where they land. That is legitimate — it is one boundary
in two registers — but only if it is VISIBLE. Chased silently it reads as a
vocabulary that cannot make up its mind.

Three findings, and the difference between them is the whole module:

  * **chain** — a route whose target is itself routed away. Fine when the
    registers differ; a genuine problem when they do not, because then the
    ledger sends you somewhere it also forbids.
  * **orphan** — a route pointing at a word that does not exist. The ruling
    has outlived its target.
  * **contradiction** — two routes sending the SAME term to different words
    in the same register. Not scoping: disagreement.

A cycle is reported as a cycle and never followed twice; a vocabulary can
contain one, and an instrument that hangs on it is useless exactly when it
is needed.
"""

from __future__ import annotations

from .db import routes, words


def _live(name: str, known: set[str]) -> bool:
    return name.lower() in known


def analyse() -> dict:
    rs = routes()
    known = {w["name"].lower() for w in words()}
    by_term: dict[str, list[dict]] = {}
    for r in rs:
        by_term.setdefault(r["from_term"].lower(), []).append(r)

    orphans = [r for r in rs if not _live(r["to_word"], known)]

    contradictions = []
    for term, group in by_term.items():
        per_register: dict[str, set[str]] = {}
        for r in group:
            per_register.setdefault(r["register"], set()).add(r["to_word"])
        for register, targets in per_register.items():
            if len(targets) > 1:
                contradictions.append({
                    "from_term": group[0]["from_term"], "register": register,
                    "targets": sorted(targets),
                })

    chains = []
    for r in rs:
        for hop in by_term.get(r["to_word"].lower(), []):
            chains.append({
                "path": [r["from_term"], r["to_word"], hop["to_word"]],
                "registers": [r["register"], hop["register"]],
                "overlaps": overlaps(r["register"], hop["register"]),
                "cycle": hop["to_word"].lower() == r["from_term"].lower(),
            })
    return {"routes": len(rs), "chains": chains, "orphans": orphans,
            "contradictions": contradictions}


def overlaps(a: str, b: str) -> bool:
    """Do two registers describe any of the same ground?

    `all` overlaps everything — that is what makes an unscoped ruling so
    blunt. Two DIFFERENT named registers are disjoint, which is exactly how
    a term can be right in code and wrong on the surface without the ledger
    contradicting itself."""
    return a == b or "all" in (a, b)


def render(a: dict) -> list[str]:
    if not a["routes"]:
        return ["no routes yet — `monty onto route --drafts` reads what your "
                "existing rulings already imply."]
    out: list[str] = []

    for c in a["contradictions"]:
        out.append(f"FAIL route {c['from_term']!r} points at "
                   f"{' and '.join(repr(t) for t in c['targets'])} in the SAME "
                   f"register ({c['register']}) — that is disagreement, not scope. "
                   f"Repair: give each its own register or --scope, or drop one.")
    for o in a["orphans"]:
        out.append(f"FAIL route {o['from_term']!r} → {o['to_word']!r} points at a "
                   f"word that does not exist. Repair: `monty onto add "
                   f"{o['to_word']!r}`, repoint the route, or drop it "
                   f"(`monty onto route {o['from_term']!r} --drop --to "
                   f"{o['to_word']!r} --in {o['register']}`).")
    seen: set[tuple] = set()
    for c in a["chains"]:
        arrow = " → ".join(c["path"])
        key = (arrow, tuple(c["registers"]))
        if key in seen:
            continue
        seen.add(key)
        r1, r2 = c["registers"]
        if c["cycle"] and c["overlaps"]:
            out.append(f"FAIL route cycle: {arrow} — and the two hops overlap "
                       f"({r1} / {r2}), so the ledger forbids the very word it "
                       f"sends you to. Repair: narrow one hop to the register it "
                       f"really governs (`--in code` or `--in surface`).")
        elif c["cycle"]:
            out.append(f"note route {arrow} — a bridge, not a cycle: {r1} says one "
                       f"word, {r2} says the other, and the registers do not "
                       f"overlap. This is one boundary in two registers.")
        elif c["overlaps"]:
            out.append(f"warn route {arrow} — two hops over the same ground "
                       f"({r1} / {r2}); the ledger forbids where it sends. "
                       f"Repair: point the first hop at the final word.")
        else:
            out.append(f"note route {arrow} — {r1} then {r2}; one boundary in two "
                       f"registers, worth knowing when you follow it.")
    if not out:
        out.append("ok — every route lands on a live word, once.")
    return out
