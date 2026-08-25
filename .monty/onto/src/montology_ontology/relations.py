"""Relations: the ontology's own noun-verb-noun graph, AUTHORED.

Everything else montology holds is mined or ruled. This is the one thing that
has to be said outright, and the reason is worth writing down because it took
measuring to see.

An ontology's graph — `tour flies pointer` — exists in Palantir because a person
declared a link type in Ontology Manager, and in DTDL because someone wrote a
relationship into the model file. NOBODY MINES IT. Code contains an
implementation, not an ontology: measured on qubie, a receiver and an argument
that are both words occur ZERO times, typed parameters forming a noun-verb-noun
occur zero times, and typed fields once. The relations are not in there to find.

So they are authored, and the scan's ACTS become DRAFTS for them — exactly the
shape `candidate` already has for words. The scan proposes and a person commits,
which is the only arrangement in this repo that has ever held up.

What a relation buys that an act cannot: it survives a refactor, it says WHY,
and it can be reviewed in a proposal like any other change to meaning.
"""

from __future__ import annotations

from .db import connect


def _has(conn) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='relation'").fetchone())


def relate(subject: str, verb: str, object: str, *, why: str | None = None,
           at: str | None = None, origin: str | None = None) -> str:
    """Say that one word does something to another."""
    conn = connect()
    known = {r[0].lower() for r in conn.execute("SELECT name FROM word")}
    for name, role in ((subject, "subject"), (object, "object")):
        if name.lower() not in known:
            return (f"REFUSED — {name!r} is not a word, and the {role} of a relation "
                    f"has to be one. A relation between things nobody has named is "
                    f"a sentence about nothing. Repair: `monty onto add {name!r} …`")
    if subject.lower() == object.lower():
        return f"REFUSED — {subject!r} cannot act on itself; that is a definition, not a relation."

    conn.execute("INSERT OR REPLACE INTO relation (subject, verb, object, why, at, origin) "
                 "VALUES (?,?,?,?,?,?)",
                 (subject.lower(), verb.lower(), object.lower(), why, at, origin))
    conn.commit()
    line = f"related  {subject} --{verb}--> {object}"
    if verb.lower() not in known:
        # Not a refusal: the verb is usually the thing you learn you needed.
        line += (f"\n  note: {verb!r} is not a word yet. The verbs are the half of a "
                 f"vocabulary that goes unnamed — `monty onto add {verb!r} "
                 f"\"<definition>\" --pos verb`.")
    return line


def unrelate(subject: str, verb: str, object: str) -> str:
    conn = connect()
    cur = conn.execute("DELETE FROM relation WHERE subject=? AND verb=? AND object=?",
                       (subject.lower(), verb.lower(), object.lower()))
    conn.commit()
    return (f"dropped  {subject} --{verb}--> {object}" if cur.rowcount
            else "nothing to drop — that relation was not recorded.")


def relations(word: str | None = None) -> list[dict]:
    conn = connect(readonly=True)
    if not _has(conn):
        return []
    sql, args = "SELECT * FROM relation", []
    if word:
        sql += " WHERE subject=? OR object=?"
        args += [word.lower(), word.lower()]
    return [dict(r) for r in conn.execute(sql + " ORDER BY subject, verb, object", args)]


def drafts(root=None, top: int = 30) -> list[dict]:
    """What the code suggests, for a person to confirm or throw away.

    Every draft carries HOW it was resolved — by type, by name, by module — so
    the confirming is done with the evidence in view rather than on trust.
    """
    try:
        from montology_scan import domain_acts
        from montology_scan.acts import PLUMBING
    except Exception:  # noqa: BLE001 — the vocabulary must not need the scanner
        return []

    have = {(r["subject"], r["verb"], r["object"]) for r in relations()}
    seen: dict[tuple, dict] = {}
    for a in domain_acts(root):
        subj, obj, verb = a["subject_word"], a["object"], a["verb"].lower()
        if not subj or subj == obj or verb in PLUMBING:
            continue
        key = (subj, verb, obj)
        if key in have:
            continue
        row = seen.setdefault(key, {"subject": subj, "verb": verb, "object": obj,
                                    "count": 0, "how": a["subject_resolved"],
                                    "at": f"{a['file']}:{a['line']}"})
        row["count"] += 1
        # the strongest evidence wins the label
        rank = {"by-type": 3, "by-name": 2, "by-module": 1}
        if rank.get(a["subject_resolved"], 0) > rank.get(row["how"], 0):
            row["how"] = a["subject_resolved"]
            row["at"] = f"{a['file']}:{a['line']}"
    return sorted(seen.values(), key=lambda r: -r["count"])[:top]


def render_drafts(root=None, top: int = 30) -> list[str]:
    got = drafts(root, top)
    if not got:
        return ["no drafts — either every act the code performs is already a "
                "relation, or the code performs none between things you name."]
    out = [f"{len(got)} relation(s) the code suggests. Confirm the ones that are true:", ""]
    for d in got:
        out.append(f"  {d['count']:>3}×  {d['subject']} --{d['verb']}--> {d['object']}"
                   f"   ({d['how']}, {d['at']})")
        out.append(f"        monty onto relate {d['subject']} {d['verb']} {d['object']}")
    out += ["", "The scan proposes; you commit. A relation survives a refactor, says "
                "why, and can be reviewed in a proposal — an act can do none of those."]
    return out
