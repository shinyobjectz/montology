"""Montology's OWN vocabulary — the dogfood seed.

This seeds the montology repo's ontology (the system described in its own
terms). A target repo's ontology starts empty and is authored through
`monty onto add` — their words, not these.
"""

from __future__ import annotations

from .db import connect
from .questions import _id as _question_id

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
     "the parse-and-measure sweep of a codebase: every declaration measured, every dependency surface and the seams between them, checked against the vocabulary",
     "what the code claims"),
    ("collision", "core", "scan", "scan.collision",
     "a declaration named after a word that means something else — the failure scan exists to catch",
     "where code and vocabulary disagree"),
    ("act", "core", "scan", "scan.act",
     "one thing the code does, read off the tree: a subject, a verb and an object at a place — the half of a codebase that declarations cannot see",
     "what the code does, not what it declares"),
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
    ("intake", "core", "workspace", "ws.intake",
     "the phased questions a workspace starts with — asked in a form, answered on disk, each round written from the last — before any word is authored",
     "what was asked, what they said"),
    ("glossary", "core", "ontology", "onto.glossary",
     "the whole ontology rendered to one page — every word, ruling and doctrine block, from the database, with the intake it grew from as appendix",
     "what our words mean, on one page"),
    ("disclosure", "core", "ontology", "onto.disclosure",
     "how much of the vocabulary a render keeps resident and how much it points at — the always-loaded page, the reference pages behind it, the database behind those",
     "what every agent is made to carry"),
    ("gist", "core", "ontology", "onto.gist",
     "a definition rendered to its first sentence — what a resident page carries when the whole definition is not worth its place in context",
     "the short form of a meaning"),
    ("question", "core", "ontology", "onto.question",
     "something the vocabulary must be able to answer — kept as a requirement, linked to the words that answer it, and checked both ways",
     "what someone needs to be able to ask"),
    ("coverage", "core", "ontology", "onto.coverage",
     "the two-way check between questions and words: a question no word answers is a hole, and a word no question motivates is vocabulary nobody asked for",
     "does this vocabulary answer for itself"),
    ("proposal", "core", "ontology", "onto.proposal",
     "a set of changes to the vocabulary, reviewed before it lands — stored as intents rather than as a second copy of the words, so it reads as a diff of meaning and replays through the same door a person uses",
     "what someone wants the words to become"),
    ("intent", "core", "ontology", "onto.intent",
     "one named way to change the vocabulary, and the only way anything that is not a person at a terminal may do so",
     "how a change is asked for"),
    ("genus", "core", "ontology", "onto.genus",
     "the more general word a word is a kind of — containment says where a word lives, this says what it IS, and a word inherits its genus's rulings",
     "what kind of thing is it"),
    ("rigidity", "core", "ontology", "onto.rigidity",
     "whether a word names what a thing IS and cannot stop being, or a role it plays for a while — the one metaproperty that makes a wrong subsumption catchable",
     "could a thing stop being this"),
    ("edge", "core", "ontology", "onto.edge",
     "a relation the ontology holds between two things it names — containment, a route, a ruling, a bearing — and every one of them gates something, because an edge nothing can check is a drawing",
     "what connects two things we name"),
]

# What each word NAMES. Almost every term montology has is a NOUN, which is
# itself the finding: this vocabulary describes things, and the one verb in
# it (`sync`) is the one command whose name is also its meaning.
POS_OF = {
    "ontology": "noun", "word": "noun", "code": "value", "doctrine": "noun",
    "scan": "noun", "collision": "noun", "candidate": "noun", "act": "noun",
    "workspace": "noun", "migration": "noun", "ruling": "noun",
    "amendment": "noun", "token": "noun", "recipe": "noun", "drift": "noun",
    "vitals": "noun", "convergence": "noun", "sync": "verb",
    "surface": "noun", "seam": "noun", "phantom": "noun",
    "exception": "noun", "divergence": "noun",
    "intake": "noun", "glossary": "noun",
    "disclosure": "noun", "gist": "noun", "edge": "noun",
    "genus": "noun", "rigidity": "value",
    "proposal": "noun", "intent": "noun",
    "question": "noun", "coverage": "noun",
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
    ("glossary", ".monty/**", "`monty intake glossary` and `glossary()` hand back the glossary — "
     "the surface being literal"),
    ("coverage", ".monty/onto/**", "`coverage()` hands back the coverage — the same "
     "literalism as `divergence()`, `glossary()` and `gist()`: below the surface, a "
     "function that returns exactly what the word names and is called anything else "
     "would be the drift"),
    ("gist", ".monty/gen/**", "`gist()` in the renderer returns a gist — the same literalism as "
     "`divergence()` and `glossary()`: below the surface, a function that hands back exactly "
     "what the word names and is called anything else would be the drift"),
]

# What each word IS, where saying so is TRUE. montology's vocabulary is mostly
# flat, and that is a finding rather than a gap: inventing a hierarchy to have
# one is the over-modelling these tools are supposed to catch.
GENERA = [
    ("exception", "ruling", "an exception is a recorded boundary decision like any "
     "other — which is why it carries a reason and a place, and why a bare "
     "allow-list was never one"),
]

# The one OntoClean metaproperty. `candidate` is the clearest case in this
# vocabulary and the reason the check is worth having: a candidate is a ROLE a
# declared name plays until somebody defines it, so nothing that permanently is
# something may be a kind of candidate.
RIGIDITY_OF = {
    "word": "rigid", "ruling": "rigid", "exception": "rigid", "doctrine": "rigid",
    "seam": "rigid", "token": "rigid", "edge": "rigid",
    "candidate": "anti-rigid", "phantom": "anti-rigid",
}

# What montology's vocabulary is ANSWERABLE TO. Written as the questions a
# person actually arrives with — not as a summary of the words, which would
# make the coverage check circular and therefore worthless.
QUESTIONS = [
    ("Is this name already spoken for, and by what?",
     ["word", "code", "ruling", "exception"]),
    ("What decisions were taken about this word, and why?",
     ["doctrine", "ruling", "amendment"]),
    ("What in the code answers to this word, and where do the two meet?",
     ["surface", "seam", "phantom"]),
    ("What vocabulary is this codebase asking for that nobody has defined?",
     ["candidate", "scan", "collision", "divergence"]),
    ("What does the code DO to the things we name, and do we name any of it?",
     ["act"]),
    ("Is the generated prose still true of the database it claims to render?",
     ["sync", "drift", "glossary"]),
    ("How much of the vocabulary does an agent carry on every single turn?",
     ["disclosure", "gist"]),
    ("What would this change break, before anyone approves it?",
     ["proposal", "intent"]),
    ("What is this word a kind of, and what does it inherit by being one?",
     ["genus", "rigidity", "edge"]),
    ("Where does the vocabulary this repo starts with come from?",
     ["intake", "workspace", "ontology"]),
    ("Has the code caught up with a word we renamed?",
     ["migration", "vitals", "convergence"]),
    # Added because the coverage check found `recipe` and `token` motivated by
    # nothing — which turned out to be a hole in the QUESTIONS, not in the
    # vocabulary. That is the check working: it says where to look, not what
    # the answer is.
    ("Which values is the design allowed to use, and where has it drifted?",
     ["token", "recipe", "drift"]),
    ("What is this vocabulary answerable to, and is anything in it unasked for?",
     ["question", "coverage"]),
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
    ("The skill is a routing table, not the vocabulary", 50,
     "The words skill is loaded on every turn, so every character in it is rent "
     "an agent pays before it has done anything. The database already answers "
     "for any single word (`monty onto check`), which means a full render of "
     "the vocabulary into an always-loaded file is an O(words) copy of an O(1) "
     "store. So the render is TIERED: it stays whole while it fits, and past "
     "the budget it gives up the cheapest thing first — retired names (the "
     "guard blocks those at write time, so the ledger was never what enforced "
     "them), then adopted words (imported prose, one sentence resident and the "
     "source text a page away), then the argument behind a ruling, then a "
     "doctrine's body, and only last our own definitions. What leaves the page "
     "is reported by sync and by every lint, because a reader who cannot see "
     "that something left cannot ask for it. Raising `body_cap` is still "
     "allowed and still has to say why, but it now buys residency rather than "
     "postponing a wall."),
    ("An edge must be enforceable", 60,
     "Every relation montology holds gates something. Containment gates the code "
     "namespace — a dotted prefix must resolve to a word, so the namespace stays a "
     "tree. A route gates what may be said in a register. A ruling gates a name. A "
     "bearing is checked against the scan. That is not a coincidence, it is the "
     "admission test, and it is what decides which relations we copy from the "
     "vendors and which we do not.\n\n"
     "Palantir has link types and DTDL has relationships — hasPart, usedIn, cools, "
     "isBilledTo — and they are right to. Those edges exist to power RUNTIME OBJECT "
     "TRAVERSAL: Palantir has objects, DTDL has twins, Fabric has entity instances, "
     "and a link is how a query walks from one instance to the next. montology has "
     "no instances. It has words, and the code that answers to them. A hasPart "
     "between two words would assert something nothing here can check, and an "
     "ontology whose edges cannot be checked is a diagram — which is the artefact "
     "this repo exists to replace. So we do not grow them, and this is written down "
     "so the question is answered once rather than every time somebody new sees the "
     "canvas and reaches for the obvious thing.\n\n"
     "One relation DOES pass the test and we take it: the genus, the word a word is "
     "a kind of. It passes because a word inherits its genus's rulings and its guard "
     "behaviour, so drawing the edge changes what the gate does. It is called genus "
     "and not kind-of because `kind` already means provenance here — whose word it "
     "is — and one root meaning two things is the failure the vocabulary exists to "
     "prevent.\n\n"
     "Capabilities (Palantir's interfaces: Inspectable, Schedulable) are the "
     "strongest idea in their model and are DEFERRED rather than refused. They earn "
     "their place when something can target them — a function, an action, a rule "
     "that applies to every word carrying the capability. Until montology has a "
     "kinetic layer, a capability would gate nothing, and the test is the test."),
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
    for name, value in RIGIDITY_OF.items():
        conn.execute("UPDATE word SET rigidity=? WHERE lower(name)=?", (value, name))
    for text, by in QUESTIONS:
        qid = _question_id(text)
        conn.execute("INSERT OR IGNORE INTO question (id, text, asked_in, asked_at) "
                     "VALUES (?,?,?,?)", (qid, text, "seed", "2026-08-25"))
        for word in by:
            conn.execute("INSERT OR REPLACE INTO answers (question_id, word_name) "
                         "VALUES (?,?)", (qid, word))
    for word, genus, why in GENERA:
        conn.execute("INSERT OR REPLACE INTO genus (word_name, genus_name, why) "
                     "VALUES (?,?,?)", (word, genus, why))
    conn.commit()
    return (f"seeded {len(WORDS)} words, {len(DOCTRINE)} doctrine blocks, "
            f"{len(EXCEPTIONS)} exceptions, {len(GENERA)} genus, "
            f"{len(RIGIDITY_OF)} rigidity judgements, {len(QUESTIONS)} questions")
