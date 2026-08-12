"""Surfaces and seams: what this repo stands on, and what actually touches it.

`surface.py` beside this measures ONE surface — the declarations this
codebase makes. This package measures every surface, ours included, and the
seams between them.

The model, in three sentences. A **surface** is what a thing exposes: its
named, callable, importable face; ours and a dependency's are the same kind
of thing, and whose it is, is a column. A **seam** is one point where two
surfaces meet — an import that resolves, a call that lands, a config key
read. A surface with no seam is a **phantom**: declared, never met.

THE SEAM IS THE EVIDENCE. There is no separate proof-of-use, because a seam
is what proof-of-use is. Static seams gate; observed seams (traces,
telemetry) may raise confidence and may never fail a build, because they
only cover paths that happened to run. A phantom is a claim about STATIC
evidence — if one is wrong the probe is wrong, and the repair is to teach
the probe, not to widen what counts as proof until nothing is ever a
phantom.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from montology_core import workspace_root
from montology_ontology.db import connect

from .probes import PROBES, first_party_id, sid, unprobed

__all__ = ["PROBES", "bear", "bearings", "first_party_id", "gate", "measure",
           "phantoms", "record", "report", "seams", "sid", "surfaces",
           "surfaces_for_word", "unbearing_phantoms", "words_for_surface"]


def _root(root: Path | None = None) -> Path:
    return root or workspace_root()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


# ── recording ────────────────────────────────────────────────────────────

def measure(root: Path | None = None, probes: list[str] | None = None) -> dict:
    """Run the probes and return what they find, WITHOUT writing anything.

    The gate reads this, not the table. A lint that trusted the last sweep
    would pass on a dependency deleted an hour ago — which is the exact
    drift montology exists to catch, reintroduced at the one place it is
    least excusable. Recording is a separate act.

    Returns surfaces, seams, phantoms, and what was SKIPPED and why: a probe
    that cannot run says so, because silence would read as "covered" when it
    was not. That is `surface.py`'s rule for missing grammars, unchanged.
    """
    root = _root(root)
    chosen = [p for p in PROBES if probes is None or p.name in probes]

    found_surfaces: list[dict] = []
    skipped: list[str] = []
    ran: set[str] = set()   # probes that ANSWERED — only these may delete
    for probe in chosen:
        try:
            rows = probe.surfaces(root)
        except Exception as exc:  # a broken probe must not fail the sweep
            skipped.append(f"{probe.name}: {type(exc).__name__}: {exc}")
            continue
        if rows is None:
            skipped.append(f"{probe.name}: nothing to read in this repo")
            continue
        ran.add(probe.name)
        found_surfaces.extend(rows)

    # One component can be claimed by two probes (a package that ships both
    # a Python module and a JS entry point). Its id is deliberately not
    # namespaced by probe, so merge the faces rather than letting the last
    # probe to run overwrite the first.
    merged: dict[str, dict] = {}
    for s in found_surfaces:
        prev = merged.get(s["id"])
        if prev is None:
            merged[s["id"]] = dict(s, probes=[s["probe"]])
            continue
        prev["exposes"] = sorted(set(prev.get("exposes", [])) | set(s.get("exposes", [])))
        prev["version"] = prev.get("version") or s.get("version")
        if prev["kind"] != "first-party":
            prev["kind"] = s["kind"]
        # `probes` is what each probe filters on below: after a merge, one
        # record answers to several probes, and filtering on the singular
        # `probe` column would hide it from all but the first.
        if s["probe"] not in prev["probes"]:
            prev["probes"].append(s["probe"])
    found_surfaces = list(merged.values())

    known = {s["id"] for s in found_surfaces}
    found_seams: list[dict] = []
    seam_ran: set[str] = set()
    for probe in chosen:
        try:
            rows = probe.seams(root, found_surfaces)
        except Exception as exc:
            skipped.append(f"{probe.name} seams: {type(exc).__name__}: {exc}")
            continue
        seam_ran.add(probe.name)
        # A seam between surfaces we did not find is not one we can defend.
        found_seams.extend(m for m in (rows or [])
                           if m["from_id"] in known and m["to_id"] in known)

    skipped += unprobed(root, {p.name for p in chosen})

    met = {end for m in found_seams for end in (m["from_id"], m["to_id"])}
    return {"surfaces": found_surfaces, "seams": found_seams,
            "phantoms": [s for s in found_surfaces if s["id"] not in met],
            "probes": [p.name for p in chosen], "skipped": skipped,
            "ran": ran, "seam_ran": seam_ran}


def record(root: Path | None = None, probes: list[str] | None = None) -> dict:
    """Measure, then persist. The table is a cache of the last sweep; the
    bearings joined to it are the part that is authored and must survive."""
    m = measure(root, probes)
    conn = connect()
    stamp = _now()
    found_surfaces, ran, seam_ran = m["surfaces"], m["ran"], m["seam_ran"]

    for s in found_surfaces:
        conn.execute(
            "INSERT INTO surface (id, owner, kind, version, exposes, declared_at, probe, first_seen) "
            "VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET owner=excluded.owner, kind=excluded.kind, "
            "version=excluded.version, exposes=excluded.exposes, "
            "declared_at=excluded.declared_at, probe=excluded.probe",
            (s["id"], s["owner"], s["kind"], s.get("version"),
             json.dumps(sorted(s.get("exposes", []))), s.get("declared_at"),
             s["probe"], stamp),
        )

    # Surfaces that vanished from the manifests are gone, not phantoms — a
    # phantom is DECLARED and unmet, so an undeclared one is just absent.
    # Only a probe that ANSWERED may retire its own rows: a probe that threw
    # knows nothing, and letting it delete would turn a broken probe into a
    # silently shrinking estate.
    known = {s["id"] for s in found_surfaces}
    if ran:
        marks = ",".join("?" * len(ran))
        keep = ",".join("?" * len(known)) or "NULL"
        conn.execute(
            f"DELETE FROM surface WHERE probe IN ({marks}) AND id NOT IN ({keep})",
            (*ran, *known))

    # A seam is a PLACE (file:line), so an edit above an import moves it.
    # A sweep therefore REPLACES its own seams rather than adding to them —
    # accumulating would leave a seam at every line an import ever sat on,
    # and a phantom that can never come back is worse than no phantom.
    if seam_ran:
        marks = ",".join("?" * len(seam_ran))
        conn.execute(f"DELETE FROM seam WHERE probe IN ({marks})", tuple(seam_ran))
    conn.execute("DELETE FROM seam WHERE from_id NOT IN (SELECT id FROM surface) "
                 "OR to_id NOT IN (SELECT id FROM surface)")

    for m2 in m["seams"]:
        conn.execute(
            "INSERT OR IGNORE INTO seam (from_id, to_id, kind, direction, at, probe, first_seen) "
            "VALUES (?,?,?,?,?,?,?)",
            (m2["from_id"], m2["to_id"], m2["kind"], m2.get("direction", "out"),
             m2["at"], m2["probe"], stamp),
        )

    conn.commit()
    return {"surfaces": len(found_surfaces), "seams": len(m["seams"]),
            "probes": m["probes"], "skipped": m["skipped"]}


# ── queries ──────────────────────────────────────────────────────────────

def _conn(root: Path | None = None):
    return connect()


def surfaces(root: Path | None = None, kind: str | None = None) -> list[dict]:
    sql = "SELECT * FROM surface"
    args: list = []
    if kind:
        sql += " WHERE kind=?"
        args.append(kind)
    rows = [dict(r) for r in _conn(root).execute(sql + " ORDER BY kind, owner", args)]
    for r in rows:
        r["exposes"] = json.loads(r["exposes"] or "[]")
    return rows


def seams(root: Path | None = None, surface_id: str | None = None) -> list[dict]:
    sql = "SELECT * FROM seam"
    args: list = []
    if surface_id:
        sql += " WHERE from_id=? OR to_id=?"
        args += [surface_id, surface_id]
    return [dict(r) for r in _conn(root).execute(sql + " ORDER BY to_id, at", args)]


def phantoms(root: Path | None = None) -> list[dict]:
    """Surfaces that appear in no seam, in either direction.

    Either direction matters: our own surface is the `from` end of every
    outbound seam, so it is never a phantom for lack of inbound callers.
    """
    rows = [dict(r) for r in _conn(root).execute(
        "SELECT * FROM surface WHERE id NOT IN "
        "(SELECT from_id FROM seam UNION SELECT to_id FROM seam) "
        "ORDER BY kind, owner")]
    for r in rows:
        r["exposes"] = json.loads(r["exposes"] or "[]")
    return rows


# ── the join to the vocabulary ───────────────────────────────────────────

def bear(word: str, surface_id: str, note: str | None = None,
         root: Path | None = None) -> str:
    """Record that a word is borne by a surface — what implements this term."""
    conn = _conn(root)
    if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (word.lower(),)).fetchone():
        return (f"REFUSED — {word!r} is not a word. Add it first "
                f"(`monty onto add`), then say what bears it.")
    if not conn.execute("SELECT 1 FROM surface WHERE id=?", (surface_id,)).fetchone():
        near = [r[0] for r in conn.execute(
            "SELECT id FROM surface WHERE id LIKE ? ORDER BY id LIMIT 5",
            (f"%{surface_id}%",))]
        hint = f" Did you mean: {', '.join(near)}?" if near else ""
        return f"REFUSED — no surface {surface_id!r}. Run `monty surface` first.{hint}"
    conn.execute("INSERT OR REPLACE INTO bearing (word_name, surface_id, note) VALUES (?,?,?)",
                 (word, surface_id, note))
    conn.commit()
    return f"bearing  {word} ← {surface_id}"


def bearings(root: Path | None = None) -> list[dict]:
    return [dict(r) for r in _conn(root).execute(
        "SELECT * FROM bearing ORDER BY word_name, surface_id")]


def surfaces_for_word(word: str, root: Path | None = None) -> list[dict]:
    """A word's surfaces: what actually implements this term.

    Several surfaces bearing on one word IS the consolidation case — "we
    collapsed these into our own term" — readable without a fourth concept.
    """
    rows = [dict(r) for r in _conn(root).execute(
        "SELECT s.*, b.note FROM surface s JOIN bearing b ON b.surface_id = s.id "
        "WHERE lower(b.word_name)=? ORDER BY s.kind, s.owner", (word.lower(),))]
    for r in rows:
        r["exposes"] = json.loads(r["exposes"] or "[]")
    return rows


def words_for_surface(surface_id: str, root: Path | None = None) -> list[str]:
    """A surface's words: which of our terms this thing bears on."""
    return [r[0] for r in _conn(root).execute(
        "SELECT word_name FROM bearing WHERE surface_id=? ORDER BY word_name",
        (surface_id,))]


def unbearing_phantoms(root: Path | None = None) -> list[dict]:
    """Phantoms a word bears on — the vocabulary claiming what the code no
    longer supports. This is the only case worth failing a build over; a
    phantom nothing bears on is untidy, not a lie."""
    out = []
    for p in phantoms(root):
        words = words_for_surface(p["id"], root)
        if words:
            out.append({**p, "words": words})
    return out


# ── the gate ─────────────────────────────────────────────────────────────

def gate(root: Path | None = None) -> list[str]:
    """The lint finding, measured fresh: a phantom a word bears on.

    Only that case FAILS. It is the vocabulary making a claim the code no
    longer supports — a word pointing at something nothing touches — which
    is precisely the misalignment this feature exists to catch. A phantom
    NOTHING bears on is reported and not fatal: an unused dependency is
    untidy, not a lie.

    Bearings come from the table because they are AUTHORED; surfaces and
    seams are measured now, because they are not.
    """
    m = measure(root)
    if not m["surfaces"]:
        return []

    claims: dict[str, list[str]] = {}
    for b in bearings(root):
        claims.setdefault(b["surface_id"], []).append(b["word_name"])

    out: list[str] = []
    for p in sorted(m["phantoms"], key=lambda s: (s["kind"], s["owner"])):
        where = f", declared in {p['declared_at']}" if p.get("declared_at") else ""
        words = claims.get(p["id"], [])
        if words:
            out.append(
                f"FAIL surface {p['owner']!r} ({p['kind']}{where}) is a phantom — "
                f"declared, and nothing meets it — but the word(s) "
                f"{', '.join(sorted(words))} bear on it, so the vocabulary claims "
                f"what the code no longer supports. Repair: use it, drop it "
                f"(and the bearing with it), or move the bearing to the surface "
                f"that carries the term now — `monty surface WORD --bear ID`.")
        else:
            out.append(
                f"note surface {p['owner']!r} ({p['kind']}{where}) is a phantom — "
                f"declared, never met. Untidy, not fatal: no word bears on it.")
    for s in m["skipped"]:
        out.append(f"note surface: {s}")
    return out


# ── the report ───────────────────────────────────────────────────────────

def report(root: Path | None = None, only_phantoms: bool = False,
           word: str | None = None, on: str | None = None) -> list[str]:
    root = _root(root)
    if word:
        rows = surfaces_for_word(word, root)
        if not rows:
            return [f"no surface bears {word!r} — nothing recorded implements this term"]
        out = [f"{word} is borne by {len(rows)} surface(s):"]
        out += [f"  {r['id']:<40} {r['kind']:<12} {r['note'] or ''}".rstrip() for r in rows]
        return out

    if on:
        words = words_for_surface(on, root)
        seam_rows = seams(root, on)
        out = [f"{on}: {len(seam_rows)} seam(s), bears on {len(words)} word(s)"]
        out += [f"  word   {w}" for w in words]
        out += [f"  seam   {m['kind']:<8} {m['direction']:<4} {m['at']}" for m in seam_rows[:20]]
        if len(seam_rows) > 20:
            out.append(f"  … and {len(seam_rows) - 20} more seam(s)")
        return out

    ghosts = phantoms(root)
    if only_phantoms:
        if not ghosts:
            return ["no phantoms — every surface is met by something"]
        out = [f"{len(ghosts)} phantom(s) — declared, never met:"]
        for p in ghosts:
            words = words_for_surface(p["id"], root)
            claim = f"  ← claimed by: {', '.join(words)}" if words else ""
            out.append(f"  {p['owner']:<32} {p['kind']:<12} {p['declared_at'] or ''}{claim}")
        return out

    all_s = surfaces(root)
    if not all_s:
        return ["no surfaces recorded — run `monty surface --record`"]
    all_m = seams(root)
    # Counted in BOTH directions and shown that way. Inbound alone would
    # print "0 seams" beside a surface that is not a phantom — a component
    # that uses things and is used by none is a leaf, not a ghost.
    used_by: dict[str, int] = {}
    uses: dict[str, int] = {}
    for m in all_m:
        used_by[m["to_id"]] = used_by.get(m["to_id"], 0) + 1
        uses[m["from_id"]] = uses.get(m["from_id"], 0) + 1

    ghost_ids = {g["id"] for g in ghosts}
    out = [f"{len(all_s)} surface(s), {len(all_m)} seam(s), {len(ghosts)} phantom(s)", ""]
    for s in all_s:
        mark = ("phantom" if s["id"] in ghost_ids
                else f"{used_by.get(s['id'], 0):>3} in {uses.get(s['id'], 0):>3} out")
        words = words_for_surface(s["id"], root)
        tail = f"  ← {', '.join(words)}" if words else ""
        out.append(f"  {s['owner']:<32} {s['kind']:<12} {mark:<14}{tail}")
    gaps = unprobed(root, {p.name for p in PROBES})
    if gaps:
        out += ["", "not measured — silence would read as covered:"]
        out += [f"  {g}" for g in gaps]
    unmet = unbearing_phantoms(root)
    if unmet:
        out += ["", f"{len(unmet)} phantom(s) a word bears on — the gate fails on these:"]
        out += [f"  {p['owner']} ← {', '.join(p['words'])}" for p in unmet]
    return out
