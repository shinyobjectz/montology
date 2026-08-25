"""`monty onto review`: the anti-patterns, named.

Palantir's most stealable asset is not their metamodel — ours is thicker in the
places that matter — it is their NAMED anti-pattern catalogue. A shared name is
what makes review possible: "this is a God Object" ends an argument that "this
feels wrong" cannot. Half the catalogue turns out to be computable here
already; it was just never named or surfaced.

Two rules hold this together:

  ADVISORY, ALWAYS. The gate is for facts. An anti-pattern is a judgement, and
  a judgement that fails a build is a judgement people learn to route around —
  which costs you the gate as well as the judgement.

  EVERY FINDING SAYS WHAT IT IS. A `proof` is syntactic and cannot be wrong
  about itself; a `heuristic` is a guess with evidence attached. Presenting the
  second as the first is how a review tool stops being read.

What is deliberately NOT here is listed by `skipped()` and printed every run: a
catalogue with silent omissions reads as one that looked and found nothing.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

# Names that carry no meaning on their own. Not a spell-check: each of these is
# a word people reach for when they have not decided what the thing IS.
VAGUE = {
    "data", "info", "item", "thing", "object", "entity", "value", "record",
    "manager", "handler", "helper", "util", "utils", "common", "misc", "shared",
    "base", "generic", "wrapper", "service", "processor", "engine", "system",
}
# The shapes a pipeline leaves behind when nobody curated what came out of it.
ETL = re.compile(r"^(tmp|temp|raw|stg|staging|etl|dim|fact)[-_]|"
                 r"[-_](at|ts|timestamp|flag|id|idx|tmp)$|^_")
# A name that carries a version or a date is a name doing a ledger's job.
TIME_MACHINE = re.compile(r"(^|[-_])(v[0-9]+|[0-9]{4}|old|new|legacy|deprecated|"
                          r"final|latest|current|next)([-_]|$)")


def _finding(pattern: str, verdict: str, subject: str, evidence: str, repair: str) -> dict:
    return {"pattern": pattern, "verdict": verdict, "subject": subject,
            "evidence": evidence, "repair": repair}


def _misnomers(vocab: list[dict]) -> list[dict]:
    out = []
    for w in vocab:
        name = w["name"].lower()
        if name in VAGUE:
            out.append(_finding(
                "The Misnomer", "heuristic", w["name"],
                f"{w['name']!r} is a word people reach for when they have not decided "
                f"what the thing is",
                "name what it IS, not what shape it has: the definition already says "
                "it, so the name can too"))
        elif _circular(name, w["definition"]):
            out.append(_finding(
                "The Misnomer", "proof", w["name"],
                "the definition explains the word with the word",
                "say what it IS without using the name: if that cannot be done, "
                "the name is standing in for a meaning nobody has settled"))
    return out


def _circular(name: str, definition: str) -> bool:
    """A definition that explains the word with the word. OOPS! catalogues this
    and it is one of the few pitfalls that is genuinely syntactic.

    Only the GENUS position counts — the first clause, where the defining work
    happens. A definition may name its own word later without being circular:
    montology's `edge` closes with "an edge nothing can check is a drawing",
    which is the sentence earning its keep, not begging the question.

    Both narrower rules here were learned by measuring rather than by
    reasoning. A short name is not a finding (qubie's `gap`, `leg`, `rig` and
    `tap` are ordinary words with real definitions, and flagging them beside
    `asr` and `tts` made a list that was three-quarters noise), and neither is
    a name appearing anywhere in its own definition — that flagged 46 of
    qubie's 99 words, which is a check nobody would read twice.
    """
    genus = re.split(r"[—:;]|\. ", definition, maxsplit=1)[0].lower()
    stem = name.rstrip("s")
    return bool(re.search(rf"\b{re.escape(stem)}(s|d|ing|es)?\b", genus))


def _time_machines(vocab: list[dict]) -> list[dict]:
    return [_finding(
        "The Time Machine", "proof", w["name"],
        f"{w['name']!r} carries a version or a date in the name itself",
        "a word means one thing; WHEN it meant it belongs in the rename ledger "
        "(`monty onto rename`), never in the name")
        for w in vocab if TIME_MACHINE.search(w["name"].lower())]


def _kitchen_sinks(vocab: list[dict], vendors: tuple[str, ...]) -> list[dict]:
    out = []
    for w in vocab:
        hit = [v for v in vendors if v in w["definition"].lower()]
        if hit:
            out.append(_finding(
                "The Kitchen Sink", "proof", w["name"],
                f"the definition names a vendor: {', '.join(hit)}",
                "vendors are not vocabulary — a tool you buy belongs in the code, "
                "never in a sentence about what the system means"))
        if ETL.search(w["name"].lower()):
            out.append(_finding(
                "The Kitchen Sink", "heuristic", w["name"],
                f"{w['name']!r} has the shape of a pipeline artefact",
                "keep the fields with business meaning and let the pipeline keep "
                "its own bookkeeping"))
    return out


def _system_silos(threshold: float) -> tuple[list[dict], str | None]:
    """Two words, one meaning. This is `onto audit` given the name Palantir
    gave it — the check was already here, nobody could say what it was FOR."""
    from montology_ontology import near_pairs

    pairs = near_pairs(threshold)
    if isinstance(pairs, str):
        return [], pairs                       # the extra is missing; say so, once
    return [_finding(
        "System Silos", "heuristic", f"{p['a']['name']} ~ {p['b']['name']}",
        f"their definitions sit at {p['score']:.2f} similarity — above {threshold}",
        "one meaning, one word: merge them, or sharpen one definition until they "
        "are genuinely two things") for p in pairs], None


def _god_objects(vocab: list[dict], decls: list[dict], enforced: set[str],
                 spread: int) -> list[dict]:
    """A word whose name is worn by declarations across unrelated top-level
    areas is doing several jobs. `divergence` is the strict half of this and
    already fails the build; this is the loose half, which cannot."""
    where: dict[str, set[str]] = defaultdict(set)
    names = {w["name"].lower(): w["name"] for w in vocab if w["kind"] in enforced}
    for d in decls:
        low = d["name"].lower()
        if low in names:
            where[names[low]].add(Path(d["file"]).parts[0] if Path(d["file"]).parts else ".")
    return [_finding(
        "The God Object", "heuristic", name,
        f"declarations wear this name in {len(areas)} unrelated areas: "
        f"{', '.join(sorted(areas)[:6])}",
        "one word, one thing — if the areas mean different things, they need "
        "different words; if they mean the same thing, say so with an exception")
        for name, areas in sorted(where.items()) if len(areas) >= spread]


def _toothless(routes: list[dict]) -> list[dict]:
    """Not in anyone's catalogue, because no vendor models a register. A ruling
    that cannot be scoped can never gate, so it reads as a decision and behaves
    as a comment."""
    return [_finding(
        "The Toothless Ruling", "proof", f"{r['from_term']} → {r['to_word']}",
        "routed at register 'all' with no scope, so nothing can enforce it",
        "scope it (`--scope`) or name its register (`--in code|surface|prose`) — "
        "an unscopable route may never gate")
        for r in routes if r["register"] == "all" and not r["scope"]]


def skipped() -> list[tuple[str, str]]:
    """What this review does NOT look for, and why. Printed every run: a
    catalogue with silent omissions reads as one that found nothing."""
    return [
        ("Department Silos", "needs an owner or team on a word, which montology "
                             "does not model — every word here belongs to the repo"),
        ("Action Sprawl", "needs a kinetic layer (actions). montology has none, "
                          "by the decision in the edge doctrine"),
        ("The Golden Hammer", "same reason: it compares tools we do not have"),
    ]


def review(root: Path | None = None, *, threshold: float = 0.70,
           spread: int = 3) -> dict:
    """Every anti-pattern this vocabulary instantiates, with its evidence."""
    from montology_core import workspace_root
    from montology_ontology import routes, words

    from .lint import _config
    from .surface import declarations

    root = root or workspace_root()
    vocab = words()
    enforced = set(_config(root).get("scan", {}).get("enforced_kinds", ["core", "inner"]))

    try:
        from montology_gen.laws import VENDOR_WORDS as vendors
    except Exception:  # noqa: BLE001 — the review must not need the generator
        vendors = ("tree-sitter", "ast-grep", "sqlite", "ollama", "github", "openai")

    silos, note = _system_silos(threshold)
    findings = (_misnomers(vocab) + _time_machines(vocab)
                + _kitchen_sinks(vocab, vendors) + silos
                + _god_objects(vocab, declarations(root)["decls"], enforced, spread)
                + _toothless(routes()))
    return {"findings": findings, "skipped": skipped(),
            "unavailable": [note] if note else [], "words": len(vocab)}


def render(r: dict) -> list[str]:
    out: list[str] = []
    by: dict[str, list[dict]] = defaultdict(list)
    for f in r["findings"]:
        by[f["pattern"]].append(f)

    if not r["findings"]:
        out.append(f"review: nothing found across {r['words']} words. Advisory "
                   "either way — the gate is `monty lint`.")
    for pattern, items in by.items():
        out.append("")
        out.append(f"{pattern}  ({len(items)})")
        for f in items:
            out.append(f"  {f['verdict']:9} {f['subject']}")
            out.append(f"            {f['evidence']}")
            out.append(f"            repair: {f['repair']}")
    out.append("")
    for note in r["unavailable"]:
        out.append(f"note review: not run — {note}")
    for name, why in r["skipped"]:
        out.append(f"note review: {name} not checked — {why}")
    out.append(f"review: {len(r['findings'])} finding(s), all advisory. "
               "A judgement that fails a build is one people route around.")
    return out
