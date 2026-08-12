"""Word health: is each word carried by anything, or is it a name alone?

The mirror of `candidates`. A candidate is a declaration with no word; a
word with nothing carrying it is the same failure from the other side — a
term the vocabulary asserts and the codebase never took up.

MATCHING IS THE WHOLE DIFFICULTY, and getting it wrong makes this
instrument lie. Three rules, each learned by measuring a real tree:

  * **Compare the last dotted segment.** Elixir declares
    `Nexus.Events.Event`; Python declares `Event`. Matching full names
    reported 65 live words as unimplemented.
  * **Normalize spelling.** `doc_id`, `docId` and `DocId` are one name, and
    a two-word term like `adapter function` is written `adapter_function`
    or `AdapterFunction` when a symbol carries it.
  * **A phrase is not a symbol.** `progressive disclosure` will never be a
    class, and calling it dead because no class has that name is the
    instrument being wrong, not the vocabulary.

So a word is judged by three independent signals — a symbol carries it, the
code mentions it, prose mentions it — and the verdict names which are
missing rather than collapsing them into a score.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from montology_core import workspace_root
from montology_ontology import words

from .stale import CODE_EXT, MAX_BYTES, PROSE_EXT, _files, _pattern
from .surface import declarations

# Kinds that describe ideas rather than things a symbol could be named for.
# A philosophy is not expected to be a class; judging it as one manufactures
# a finding out of a category error.
CONCEPTUAL_KINDS = {"philosophy", "people", "concept", "role", "attribute"}

THIN = 3   # mentions at or below which a word is barely present


def norm(s: str) -> str:
    """CamelCase, snake_case and 'two words' collapse to one key."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def health(root: Path | None = None) -> dict:
    root = root or workspace_root()
    vocab = words()
    if not vocab:
        return {"words": [], "counts": {}}

    carried: Counter[str] = Counter()
    for d in declarations(root)["decls"]:
        carried[norm(d["name"].split(".")[-1])] += 1

    try:
        from .surf import bearings

        borne: set[str] = {b["word_name"].lower() for b in bearings(root)}
    except Exception:  # noqa: BLE001 — an absent instrument is not a verdict
        borne = set()

    pats = {w["name"]: _pattern(w["name"]) for w in vocab}
    in_code: Counter[str] = Counter()
    in_prose: Counter[str] = Counter()
    for f, _rel in _files(root):
        try:
            if f.stat().st_size > MAX_BYTES:
                continue
            text = f.read_text(errors="replace")
        except OSError:
            continue
        bucket = in_code if f.suffix in CODE_EXT else in_prose
        for name, pat in pats.items():
            n = len(pat.findall(text))
            if n:
                bucket[name] += n

    out = []
    for w in vocab:
        name = w["name"]
        sym = carried.get(norm(name), 0)
        code, prose = in_code[name], in_prose[name]
        conceptual = w["kind"] in CONCEPTUAL_KINDS or " " in name.strip()
        bearing = name.lower() in borne

        if code == 0 and prose == 0 and sym == 0 and not bearing:
            state, why = "dead", "nowhere in the tree — not a symbol, not code, not prose"
        elif code == 0 and sym == 0 and not bearing:
            state, why = "prose-only", f"written about {prose}×, never built"
        elif sym == 0 and not bearing and code <= THIN:
            state, why = "thin", f"{code} code mention(s), nothing named for it"
        elif sym == 0 and not conceptual and not bearing:
            state, why = "unnamed", f"used {code}× in code, but no symbol carries the name"
        else:
            state, why = "carried", (
                f"{sym} symbol(s)" if sym else "borne by a surface" if bearing
                else f"a concept, {code + prose} mention(s)")
        out.append({"name": name, "kind": w["kind"], "code": w["code"],
                    "state": state, "why": why, "symbols": sym,
                    "in_code": code, "in_prose": prose, "bearing": bearing,
                    "conceptual": conceptual})

    order = {"dead": 0, "prose-only": 1, "thin": 2, "unnamed": 3, "carried": 4}
    out.sort(key=lambda r: (order[r["state"]], r["in_code"] + r["in_prose"]))
    return {"words": out, "counts": Counter(r["state"] for r in out)}


def render(r: dict, *, verbose: bool = False) -> list[str]:
    if not r["words"]:
        return ["no words yet — `monty scan --candidates` shows what the code is asking for."]
    c = r["counts"]
    out: list[str] = []
    for state, headline in (
        ("dead", "DEAD — nothing anywhere carries these"),
        ("prose-only", "PROSE-ONLY — written about, never built"),
        ("thin", "THIN — barely present, nothing named for them"),
    ):
        rows = [w for w in r["words"] if w["state"] == state]
        if not rows:
            continue
        out.append(f"{headline}: {len(rows)}")
        for w in rows:
            out.append(f"    {w['name']:<26} {(w['code'] or ''):<16} {w['why']}")
    unnamed = [w for w in r["words"] if w["state"] == "unnamed"]
    if unnamed:
        out.append(f"UNNAMED — used in code, no symbol holds the name: {len(unnamed)}")
        show = unnamed if verbose else unnamed[:8]
        for w in show:
            out.append(f"    {w['name']:<26} {(w['code'] or ''):<16} {w['why']}")
        if len(unnamed) > len(show):
            out.append(f"    … and {len(unnamed) - len(show)} more (--verbose)")
    out.append("")
    out.append(f"ok — {sum(c.values())} word(s): {c.get('carried', 0)} carried, "
               f"{c.get('unnamed', 0)} unnamed, {c.get('thin', 0)} thin, "
               f"{c.get('prose-only', 0)} prose-only, {c.get('dead', 0)} dead")
    return out
