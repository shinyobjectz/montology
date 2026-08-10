"""Montology's OWN vocabulary — the dogfood seed.

This seeds the montology repo's ontology (the system described in its own
terms). A target repo's ontology starts empty and is authored through
`monty onto add` — their words, not these.
"""

from __future__ import annotations

from .db import connect

WORDS = [
    # (name, kind, owner, code, definition, test)
    ("ontology", "core", None, "onto",
     "a repo's vocabulary as a database: words, doctrine, rulings — enforced by scan, rendered to prose, never authored in prose",
     "what the words are"),
    ("word", "core", "ontology", "onto.word",
     "one term with one meaning: definition, the one-line test, an optional owner and dotted code",
     "what we mean"),
    ("code", "core", "ontology", "onto.code",
     "a word's dotted address (har, har.cell) — prefixes must resolve to words, so the namespace stays a tree",
     "where a word lives"),
    ("doctrine", "core", "ontology", "onto.doctrine",
     "a decision written down in the database — because a decision that is not written down gets re-litigated",
     "why it is this way"),
    ("scan", "core", None, "scan",
     "the tree-sitter sweep of a codebase: every declaration measured, checked against the vocabulary",
     "what the code claims"),
    ("collision", "core", "scan", "scan.collision",
     "a declaration named after a word that means something else — the failure scan exists to catch",
     "where code and vocabulary disagree"),
    ("candidate", "core", "scan", "scan.candidate",
     "a recurring declared name with no word — vocabulary the codebase is asking for",
     "what wants a definition"),
    ("workspace", "core", None, "ws",
     "any repo montology is initialized into — found by walking up for .monty, the way git finds .git",
     "where work happens"),
    ("sync", "core", "ontology", "onto.sync",
     "rendering the database to the generated words skill — prose is output, never source",
     "how agents read it"),
]

DOCTRINE = [
    ("Prose is rendered, never authored", 10,
     "The database is the truth. The words skill, the CLAUDE.md section, any "
     "listing — all render FROM it (`monty sync`). A vocabulary kept in prose "
     "stays correct only as long as someone remembers to keep it correct; the "
     "last one drifted, which is why this one is a database with a gate."),
    ("The gate is the point", 20,
     "`monty lint` fails a build: collisions (a declaration named after a word "
     "that means something else), unresolvable code prefixes, generated prose "
     "gone stale behind the database. Errors carry the repair. An ontology "
     "without enforcement is a glossary."),
]


def seed() -> str:
    conn = connect()
    for name, kind, owner, code, definition, test in WORDS:
        conn.execute(
            "INSERT OR REPLACE INTO word (name, kind, owner, definition, test, note, code) "
            "VALUES (?,?,?,?,?,NULL,?)",
            (name, kind, owner, definition, test, code),
        )
    for title, ord_, body in DOCTRINE:
        conn.execute("INSERT OR REPLACE INTO doctrine VALUES (?,?,?)", (title, ord_, body))
    conn.commit()
    return f"seeded {len(WORDS)} words, {len(DOCTRINE)} doctrine blocks"
