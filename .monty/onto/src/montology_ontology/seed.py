"""Montology's OWN vocabulary — the dogfood seed.

This seeds the montology repo's ontology (the system described in its own
terms). A target repo's ontology starts empty and is authored through
`monty onto add` — their words, not these.
"""

from __future__ import annotations

from .db import connect

WORDS = [
    # (name, kind, owner, code, definition, test) — part of speech in POS_OF
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
     "the tree-sitter sweep of a codebase: every declaration measured, every dependency surface and the seams between them, checked against the vocabulary",
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
    ("migration", "core", "scan", "scan.migration",
     "a renamed word propagated through the code by token — sweep reports, apply rewrites, the diff is the review",
     "how the code catches up"),
    ("ruling", "core", "ontology", "onto.ruling",
     "a recorded boundary decision: an overload (say Y not X), a collision (whose word it is, who moved), or a rename (was, now, why)",
     "how arguments end"),
    ("amendment", "core", "ontology", "onto.amendment",
     "a word's own text corrected in place — the name and its history stay, and what the field said before is ledgered; the counterpart to a rename, which retires the name instead",
     "what a word used to say"),
    ("token", "core", "ontology", "onto.token",
     "a named design value — color, space, radius, shadow, font, breakpoint — the vocabulary a visual system trades in",
     "what design means"),
    ("recipe", "core", "ontology", "onto.recipe",
     "a named composition of utility classes — the unit a utility-first design vocabulary trades in above single tokens",
     "what a repeated class string wants to be"),
    ("drift", "core", "scan", "scan.drift",
     "a value or prose that moved away from the vocabulary it claims: a rogue literal, a near-duplicate, a stale render",
     "what the gate exists to catch"),
    ("vitals", "core", "scan", "scan.vitals",
     "the at-a-glance state of a repo's meaning: the gate, the vocabulary, the design system, the guard — one verdict (tended, drifting, untended)",
     "how the repo is doing"),
    ("convergence", "core", "scan", "scan.convergence",
     "the state a tended lexicon reaches: new concepts per sample decaying toward zero while the code keeps growing",
     "whether the vocabulary settles"),
    ("sync", "core", "ontology", "onto.sync",
     "rendering the database to the generated words skill — prose is output, never source",
     "how agents read it"),
    ("surface", "core", None, "surf",
     "what a thing exposes: its named, callable, importable face — ours and a dependency's alike, whose it is being an attribute and not a second word",
     "what something offers"),
    ("seam", "core", "surface", "surf.seam",
     "one point where two surfaces meet — an import that resolves, a call that lands, a config key read; direction is an attribute, so inputs and outputs need no words of their own",
     "where two things touch"),
    ("phantom", "core", "surface", "surf.phantom",
     "a surface with no seam: declared, never met — the mirror of a candidate, which is a declaration with no word",
     "what nothing touches"),
    ("exception", "core", "ontology", "onto.exception",
     "a recorded decision that a symbol may share a word's name — with the reason it was granted and the paths it holds in, because a reasonless allow-list is one nobody reads",
     "which collisions we keep"),
    ("divergence", "core", "scan", "scan.divergence",
     "one word declared as more than one value — the finding no exception silences, because sharing a name is a decision and meaning two things is not",
     "where one noun holds two things"),
]

# What each word NAMES. Almost every term montology has is a NOUN, which is
# itself the finding: this vocabulary describes things, and the one verb in
# it (`sync`) is the one command whose name is also its meaning.
POS_OF = {
    "ontology": "noun", "word": "noun", "code": "value", "doctrine": "noun",
    "scan": "noun", "collision": "noun", "candidate": "noun",
    "workspace": "noun", "migration": "noun", "ruling": "noun",
    "amendment": "noun", "token": "noun", "recipe": "noun", "drift": "noun",
    "vitals": "noun", "convergence": "noun", "sync": "verb",
    "surface": "noun", "seam": "noun", "phantom": "noun",
    "exception": "noun", "divergence": "noun",
}

# Montology's own exceptions, moved out of `montology.toml [scan] allow` and
# into the database on 2026-08-13 — the migration this feature exists for,
# run first on the repo that shipped it. Each carries the reason the list
# never could.
#
# The migration is also the first evidence for it. The old list had SEVENTEEN
# entries; twelve of them (`word`, `code`, `doctrine`, `collision`,
# `candidate`, `ontology`, `workspace`, `migration`, `token`, `recipe`,
# `ruling`, `convergence`) silenced nothing whatsoever — the declarations are
# plural (`words()`, `tokens()`, `collisions()`) or compound
# (`workspace_root`, `_migrate`), so no collision was ever raised on them.
# Nobody could know that, because a bare string in a config file is never
# read against anything. Five were doing real work, and they are what is left.
#
# Inserted directly, like the words: seeding is offline and deterministic,
# while `except_add`'s divergence probe needs a scan of the tree. Python
# declares no named types, so nothing here was comparable — `unchecked` is
# the honest record of that, not a passing grade.
EXCEPTIONS = [
    ("scan", ".monty/**", "`monty scan` runs the scan; a command named after the thing it "
     "performs is the surface being literal"),
    ("sync", ".monty/**", "a verb at the surface: `monty sync` IS syncing, and means it"),
    ("drift", ".monty/**", "`monty drift` measures drift — the command hands back the thing "
     "the word names"),
    ("vitals", ".monty/**", "`monty vitals` prints the vitals"),
    ("surface", ".monty/**", "`monty surface` and `surface.py` both deal in surfaces — one "
     "the dependency's, one the code's, and the word covers both by design"),
    ("divergence", ".monty/scan/**", "`divergence()` in the lint returns divergences; below "
     "the surface, a function that hands back exactly what the word names and is called "
     "anything else would be the drift"),
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
    ("The seam is the evidence", 30,
     "There is no word for proof-of-use, because a seam IS proof of use: if a "
     "surface is genuinely used there is a seam, and if there is no seam it is "
     "a phantom. Static seams — an import that resolves, a call that lands, a "
     "config key read — are deterministic, so they gate. Observed seams "
     "(traces, telemetry) only cover paths that happened to run, so absence "
     "proves nothing: they may raise confidence, never fail a build, and never "
     "promote a phantom. A phantom is a claim about STATIC evidence — if one is "
     "wrong the probe is wrong, and the repair is to teach the probe, not to "
     "widen what counts as proof until nothing is ever a phantom."),
    ("A collision is judged on what the word names", 40,
     "Not every symbol sharing a word's name is drift, and treating them alike "
     "produces a list nobody reads. A basic VERB below the surface is fine — "
     "Store.open, Keyring.open and Ledger.open all do ordinary work at a layer "
     "nobody authors against, and English has one word for it. A primary verb "
     "at the surface should be literal, and usually IS the word, meaning it. A "
     "NOUN colliding is the real defect, because a noun names a thing and two "
     "things with one name is the failure a vocabulary exists to prevent. A "
     "VALUE TYPE should be deliberately consistent: the same value wears the "
     "same name everywhere, and the test is whether you could pass one where "
     "the other is expected. So the word carries its part of speech (`pos`), "
     "the judgment follows from it, and a collision kept is an `exception` — "
     "with its reason and the paths it holds in, in the database where the "
     "rest of the vocabulary lives. What an exception may NEVER do is silence "
     "a divergence: it says a symbol may share the name, never that the name "
     "may mean two values, and the gate reports the second whether or not the "
     "first was granted."),
]


def seed() -> str:
    conn = connect()
    for name, kind, owner, code, definition, test in WORDS:
        conn.execute(
            "INSERT OR REPLACE INTO word (name, kind, owner, definition, test, note, code, pos) "
            "VALUES (?,?,?,?,?,NULL,?,?)",
            (name, kind, owner, definition, test, code, POS_OF.get(name)),
        )
    for title, ord_, body in DOCTRINE:
        conn.execute("INSERT OR REPLACE INTO doctrine (title, ord, body) VALUES (?,?,?)", (title, ord_, body))
    for word, scope, why in EXCEPTIONS:
        conn.execute(
            "INSERT OR REPLACE INTO exception (word, scope, why, judged, checked, granted_on) "
            "VALUES (?,?,?,?,'unchecked','2026-08-13')",
            (word, scope, why, POS_OF.get(word)),
        )
    conn.commit()
    return (f"seeded {len(WORDS)} words, {len(DOCTRINE)} doctrine blocks, "
            f"{len(EXCEPTIONS)} exceptions")
