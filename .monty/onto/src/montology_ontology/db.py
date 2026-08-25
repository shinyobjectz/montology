"""The ontology: a repo's vocabulary as a database, not a doc.

One SQLite file inside the `.monty/` marker. The tables:

  * ``word`` — one term, one meaning: name, kind, an optional owner (the
    word it lives inside), a definition, the one-line "what is it" test,
    and an optional dotted CODE (``har``, ``har.cell``) that scan and
    tag systems can resolve.
  * ``doctrine`` — the decisions worth writing down, ordered; a decision
    that is not written down gets re-litigated.
  * ``overload`` — "do not say X, say Y": the words a repo has ruled on.
  * ``collision`` — boundary rulings with frameworks: whose word it is,
    what theirs means, which of us moved. At a framework's boundary you
    speak the framework's word; the table says who yielded, so the choice
    never gets re-litigated.
  * ``renamed`` — the ledger old material is read through: was → now,
    when, why. A renamed word's old name is BLOCKED from re-use.
  * ``amended`` — the ledger a word's own TEXT is read through: which
    field changed, what it said before, when and why. A rename retires a
    name; an amendment keeps the name and corrects what it claims.
  * ``token`` — DESIGN values as vocabulary: a named color, spacing step,
    radius, shadow, font or breakpoint. A hex code is a word that means
    one thing; the style lint aligns the code to these.
  * ``gen_runs`` — the assay: every generative attempt (word definitions),
    with outcome and failed laws. Memory, queryable.
  * ``surface`` — what a thing exposes: its named, callable, importable
    face. Ours and a dependency's alike; whose it is, is the ``kind``
    column, not a second table.
  * ``seam`` — one point where two surfaces meet. The seam IS the
    evidence of use: a surface with no seam is a phantom.
  * ``bearing`` — the edge between a word and a surface: what actually
    implements this term. An edge between two things that already have
    words earns no word of its own.
  * ``exception`` — a symbol may share a word's name, HERE, for this
    reason. The reason and the scope are the whole point: a bare
    allow-list carries neither, so nobody can tell a decision from a
    shrug. An exception never says the NAME may mean two things — that
    is the divergence law, and no exception silences it.
  * ``route`` — the edge between a word and a WORD: say this, not that,
    HERE. The register and scope are the whole point: `workspace` is a
    correct word in code and a wrong one on the surface, and a ruling
    that cannot say where it applies cannot be enforced anywhere.

Prose renders FROM this (``monty sync`` → the words skill); it is never
the source. That is the whole trade: a vocabulary kept in prose stays
correct only as long as someone remembers to keep it correct.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from montology_core import workspace_root

# Tests pin DB_PATH directly; when None it resolves lazily from the workspace.
DB_PATH: Path | None = None

CODE_RE = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9-]*)*$")

# What a word NAMES — the dimension a collision is judged on. Deliberately
# three, not a grammar:
#
#   verb  — an action. English has one word for opening a thing, and a
#           symbol doing that ordinary work below the surface is not a
#           second meaning. At the surface the verb IS the operation.
#   noun  — a thing. Two things with one name is the failure a vocabulary
#           exists to prevent, so a colliding noun answers for itself: does
#           this symbol denote the word's thing, or a second thing?
#   value — a noun whose whole promise is interchangeability: the same
#           value wears the same name everywhere. The test is "could you
#           pass one where the other is expected?" — and where the code
#           declares its types, montology can ask it (see `divergence`).
POS = ("verb", "noun", "value")


def db_path() -> Path:
    if DB_PATH is not None:
        return DB_PATH
    return workspace_root() / ".monty" / "ontology.db"


def _enforced_kinds() -> set[str]:
    """Which kinds a code declaration may not be named after — the same list
    the scanner gates on, read here so `add` can ask for what a collision on
    this word will need and nothing more. Read rather than imported: the
    vocabulary must not depend on the scanner."""
    import tomllib

    try:
        with (workspace_root() / ".monty" / "montology.toml").open("rb") as fh:
            scan = tomllib.load(fh).get("scan", {})
        return set(scan.get("enforced_kinds", ["core", "inner"]))
    except (OSError, ValueError):
        return {"core", "inner"}


SCHEMA = """
CREATE TABLE IF NOT EXISTS word (
  name        TEXT PRIMARY KEY,
  kind        TEXT NOT NULL,          -- core | inner | adopted | custom
  owner       TEXT,                   -- which word it lives inside
  definition  TEXT NOT NULL,
  test        TEXT,                   -- the one-line "what is it" test
  note        TEXT,
  code        TEXT UNIQUE,            -- dotted, socialite-style: har, har.cell
  origin      TEXT,                   -- NULL = this repo's own; else the upstream source
  pos         TEXT                    -- verb | noun | value: what KIND of thing the
                                      -- word is, which is how a collision is judged.
                                      -- `kind` is provenance (whose word it is); this
                                      -- is part of speech (what it names), and the two
                                      -- answer different questions.
);

CREATE TABLE IF NOT EXISTS doctrine (
  title       TEXT PRIMARY KEY,
  ord         INTEGER NOT NULL,
  body        TEXT NOT NULL,
  origin      TEXT
);

CREATE TABLE IF NOT EXISTS overload (
  dont_say    TEXT PRIMARY KEY,
  say         TEXT NOT NULL,
  why         TEXT,
  origin      TEXT
);

CREATE TABLE IF NOT EXISTS collision (
  term          TEXT PRIMARY KEY,     -- the contested name
  theirs        TEXT NOT NULL,        -- whose word collides (the framework/system)
  their_meaning TEXT NOT NULL,
  ruling        TEXT NOT NULL,        -- which side moved, and what to say now
  decided       TEXT,
  origin        TEXT
);

CREATE TABLE IF NOT EXISTS renamed (
  was         TEXT PRIMARY KEY,
  now         TEXT NOT NULL,
  renamed_on  TEXT,
  why         TEXT,
  origin      TEXT
);

CREATE TABLE IF NOT EXISTS amended (
  word        TEXT NOT NULL,          -- whose record changed; the name does not move
  field       TEXT NOT NULL,          -- definition | test | note | code | owner
  was         TEXT,                   -- what that field said before (NULL = it said nothing)
  amended_on  TEXT,
  why         TEXT
  -- Append-only, like gen_runs: an amendment is an EVENT, so there is no
  -- key to overwrite and no origin column — an upstream word arrives with
  -- its text already correct. This row is the recovery path for the text
  -- it replaced, which is the whole reason amending beats an UPDATE.
);

CREATE TABLE IF NOT EXISTS token (
  name      TEXT PRIMARY KEY,        -- brand-primary, space-2
  category  TEXT NOT NULL,           -- color | space | radius | shadow | font | breakpoint
  value     TEXT NOT NULL,           -- the one value the name means
  note      TEXT,
  origin    TEXT
);

CREATE TABLE IF NOT EXISTS guard_runs (
  ran_at    TEXT NOT NULL,
  path      TEXT NOT NULL,
  verdict   TEXT NOT NULL,           -- deny | allow | advisory
  findings  TEXT
);

CREATE TABLE IF NOT EXISTS gen_runs (
  ran_at      TEXT NOT NULL,
  task        TEXT NOT NULL,
  target      TEXT NOT NULL,
  model       TEXT NOT NULL,
  outcome     TEXT NOT NULL,          -- accepted | refused | errored | handoff
  laws_failed TEXT
);

CREATE TABLE IF NOT EXISTS surface (
  id          TEXT PRIMARY KEY,       -- probe:owner — stable across runs
  owner       TEXT NOT NULL,          -- the package/service/app; the repo itself for ours
  kind        TEXT NOT NULL,          -- first-party | package | service | api | model
  version     TEXT,                   -- carried from the start: a seam to a symbol
                                      -- a version no longer exposes is a DIFFERENT
                                      -- finding from a phantom (out of scope for v1)
  exposes     TEXT NOT NULL,          -- JSON array: the named, callable, importable face
  declared_at TEXT,                   -- the manifest or config that claims it
  probe       TEXT NOT NULL,          -- which probe emitted this
  first_seen  TEXT
);

CREATE TABLE IF NOT EXISTS seam (
  from_id     TEXT NOT NULL,          -- surface.id
  to_id       TEXT NOT NULL,          -- surface.id
  kind        TEXT NOT NULL,          -- import | call | config | binding
  direction   TEXT NOT NULL,          -- out (we call them) | in (they call us)
  at          TEXT NOT NULL,          -- file:line — a seam is a PLACE
  probe       TEXT NOT NULL,
  first_seen  TEXT,
  PRIMARY KEY (from_id, to_id, kind, at)
);

CREATE TABLE IF NOT EXISTS proposal (
  id          TEXT PRIMARY KEY,       -- short, quotable in a review
  title       TEXT NOT NULL,
  why         TEXT,                   -- the case for the change
  author      TEXT,
  status      TEXT NOT NULL,          -- open | merged | closed
  opened_at   TEXT,
  merged_at   TEXT
);

CREATE TABLE IF NOT EXISTS change (
  proposal_id TEXT NOT NULL,
  ord         INTEGER NOT NULL,
  intent      TEXT NOT NULL,          -- word.add, route.add — an intent, never SQL
  fields      TEXT NOT NULL,          -- JSON: what that intent takes
  verdict     TEXT,                   -- approved | rejected | NULL (undecided)
  note        TEXT,
  PRIMARY KEY (proposal_id, ord)
);

CREATE TABLE IF NOT EXISTS genus (
  word_name   TEXT NOT NULL,          -- the word that is a kind of something
  genus_name  TEXT NOT NULL,          -- the more general word it is a kind of
  ruled_on    TEXT,
  why         TEXT,
  origin      TEXT,
  PRIMARY KEY (word_name, genus_name)
);

CREATE TABLE IF NOT EXISTS route (
  from_term   TEXT NOT NULL,          -- the term being routed AWAY from
  to_word     TEXT NOT NULL,          -- what to say instead
  register    TEXT NOT NULL,          -- code | surface | prose | all
  scope       TEXT,                   -- path glob; NULL = the register's
                                      -- configured default. A route with
                                      -- NEITHER cannot be scoped, and an
                                      -- unscopable route may never gate.
  ruled_on    TEXT,
  why         TEXT,
  origin      TEXT,                   -- where the ruling came from
  PRIMARY KEY (from_term, to_word, register)
);

CREATE TABLE IF NOT EXISTS bearing (
  word_name   TEXT NOT NULL,
  surface_id  TEXT NOT NULL,
  note        TEXT,
  PRIMARY KEY (word_name, surface_id)
);

CREATE TABLE IF NOT EXISTS exception (
  word        TEXT NOT NULL,          -- the word a symbol may share the name of
  scope       TEXT NOT NULL,          -- path glob; '**' = tree-wide, and SAID to be
  why         TEXT NOT NULL,          -- required: a reasonless exception is a shrug
  judged      TEXT,                   -- the case it was granted under: verb|noun|value
  checked     TEXT,                   -- what the divergence probe saw at grant time:
                                      -- consistent | unchecked (nothing comparable)
  granted_on  TEXT,
  origin      TEXT,
  PRIMARY KEY (word, scope)
);
"""


def connect(path: Path | None = None, *, readonly: bool = False) -> sqlite3.Connection:
    target = path or db_path()
    if readonly:
        c = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(target)
        c.executescript(SCHEMA)
        _migrate(c)
    c.row_factory = sqlite3.Row
    return c


def _migrate(conn: sqlite3.Connection) -> None:
    """Additive only — the db is user data the moment a word lands."""
    for table in ("word", "token", "doctrine", "overload", "collision", "renamed"):
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if cols and "origin" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN origin TEXT")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(word)")}
    if cols and "pos" not in cols:
        conn.execute("ALTER TABLE word ADD COLUMN pos TEXT")
    if cols and "rigidity" not in cols:
        conn.execute("ALTER TABLE word ADD COLUMN rigidity TEXT")


def check(name: str, c: sqlite3.Connection | None = None) -> list[str]:
    """Is this name spoken for? Human-readable findings; [] = free.

    THE GATE: run before naming anything — a class, a concept, a tag.
    Checks the name and the code namespace both."""
    if c is None and not db_path().exists():
        return []
    conn = c or connect(readonly=True)
    low = name.strip().lower()
    findings: list[str] = []
    w = conn.execute("SELECT * FROM word WHERE lower(name)=?", (low,)).fetchone()
    if w:
        code = f" [{w['code']}]" if w["code"] else ""
        pos = f", {w['pos']}" if "pos" in w.keys() and w["pos"] else ""
        findings.append(f"TAKEN  {w['name']} ({w['kind']}{pos}){code} — {w['definition']}")
    # An exception is the answer to "may I name something this?", so it
    # belongs in the same finding list as the refusals — otherwise the
    # recorded decision is invisible exactly where it would be read.
    try:
        excepted = conn.execute("SELECT * FROM exception WHERE lower(word)=? ORDER BY scope",
                                (low,)).fetchall()
    except sqlite3.OperationalError:
        excepted = []
    for e in excepted:
        where = "tree-wide" if e["scope"] == TREE_WIDE else e["scope"]
        findings.append(f"EXCEPTED  a symbol may share {e['word']!r} in {where} "
                        f"({e['judged'] or 'unjudged'}) — {e['why']}")
    cw = conn.execute("SELECT name, code FROM word WHERE code=?", (low,)).fetchone()
    if cw and not w:
        findings.append(f"CODE   {cw['code']} belongs to {cw['name']!r}")
    # The word's own history. Guarded where the other lookups are not: this
    # table is younger than the databases in the wild, and a readonly
    # connection never runs the schema that would create it.
    try:
        amends = conn.execute("SELECT * FROM amended WHERE lower(word)=? "
                              "ORDER BY rowid DESC", (low,)).fetchall()
    except sqlite3.OperationalError:
        amends = []
    if amends:
        a, earlier = amends[0], len(amends) - 1
        findings.append(f"AMENDED  {a['word']}'s {a['field']} changed on {a['amended_on']}"
                        + (f" — {a['why']}" if a["why"] else "")
                        + f". It said: {a['was']!r}."
                        + (f" ({earlier} earlier in the ledger.)" if earlier else ""))
    o = conn.execute("SELECT * FROM overload WHERE lower(dont_say)=?", (low,)).fetchone()
    if o:
        findings.append(f"RULED  do not say {o['dont_say']!r} — say {o['say']!r}"
                        + (f" ({o['why']})" if o["why"] else ""))
    r = conn.execute("SELECT * FROM renamed WHERE lower(was)=?", (low,)).fetchone()
    if r:
        findings.append(f"RENAMED  {r['was']!r} became {r['now']!r} on {r['renamed_on']}"
                        + (f" — {r['why']}" if r["why"] else "")
                        + ". The old name stays retired.")
    col = conn.execute("SELECT * FROM collision WHERE lower(term)=?", (low,)).fetchone()
    if col:
        findings.append(f"COLLISION ({col['theirs']})  their meaning: {col['their_meaning']} "
                        f"— ruling: {col['ruling']}")
    return findings


def add(name: str, definition: str, *, test: str | None = None,
        note: str | None = None, kind: str = "custom",
        owner: str | None = None, code: str | None = None,
        pos: str | None = None) -> str:
    """Author a word — check-first is the contract: a taken name is refused
    WITH its findings, because one word means one thing."""
    if pos and pos not in POS:
        return (f"REFUSED — pos {pos!r} is not one of {', '.join(POS)}. It is what a "
                "word NAMES, not whose it is: `kind` already carries provenance.")
    # Required for a NEW word that can actually gate, and optional for one that
    # cannot. Three things were being conflated:
    #
    #   the COLUMN is nullable, because an upgrade that fails a build nobody
    #   changed is not an upgrade, and every database predates it;
    #
    #   a word of an ENFORCED kind must say what it names, because a collision
    #   on it cannot otherwise be judged and will sit in an advisory list until
    #   somebody happens to read one — measured in lazyriver, where fourteen
    #   such words produced eighteen unjudgeable advisories;
    #
    #   a word of an unenforced kind never raises a collision, so demanding the
    #   dimension that judges one is asking for an answer nothing will read.
    #
    # Requiring it of everything was tried first and broke twenty tests that
    # author throwaway vocabulary. That is the cost of asking a question where
    # there is no decision to make.
    if not pos and kind in _enforced_kinds():
        return ("REFUSED — say what this word NAMES: --pos verb | noun | value.\n"
                "  verb   an action. At a surface it IS the operation; below one,\n"
                "         ordinary work sharing the word is not a second meaning.\n"
                "  noun   a thing. Two things wearing it is the defect — though two\n"
                "         declarations may be two renderings of one thing.\n"
                "  value  a noun promising ONE shape everywhere it appears. Pick this\n"
                "         only if you could pass any one where any other is expected.\n"
                "Without it a collision on this word cannot be judged, so the gate\n"
                "cannot do its job and the exception cannot be recorded either.")
    findings = check(name)
    if findings:
        return ("REFUSED — the name is spoken for:\n" + "\n".join(findings)
                + "\nPick a different word; one word means one thing.")
    conn = connect()
    if owner:
        if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (owner.lower(),)).fetchone():
            known = [r[0] for r in conn.execute("SELECT name FROM word ORDER BY name")]
            return (f"REFUSED — owner {owner!r} is not a word yet. Add it first, "
                    f"or pick from: {', '.join(known[:20]) or '(none yet)'}")
    if code:
        if not CODE_RE.match(code):
            return f"REFUSED — code {code!r} is not dotted-lowercase (like `har` or `har.cell`)."
        taken = conn.execute("SELECT name FROM word WHERE code=?", (code,)).fetchone()
        if taken:
            return f"REFUSED — code {code!r} already belongs to {taken[0]!r}."
        if "." in code:
            prefix = code.rsplit(".", 1)[0]
            if not conn.execute("SELECT 1 FROM word WHERE code=?", (prefix,)).fetchone():
                return (f"REFUSED — code prefix {prefix!r} resolves to no word. "
                        "Dotted codes live INSIDE a word that holds the prefix.")
    conn.execute("INSERT INTO word (name, kind, owner, definition, test, note, code, pos) "
                 "VALUES (?,?,?,?,?,?,?,?)",
                 (name.strip(), kind, owner, definition.strip(), test, note, code, pos))
    conn.commit()
    tail = f" [{code}]" if code else ""
    said = f"{kind}{', ' + pos if pos else ''}{', inside ' + owner if owner else ''}"
    out = f"added  {name} ({said}){tail} — {definition.strip()}"
    if not pos:
        out += ("\n  note: no part of speech — a collision on this word cannot be "
                f"judged until it has one: monty onto amend {name} --pos noun|verb|value")
    return out


def rule(dont_say: str, say: str, why: str | None = None) -> str:
    """Record an overload ruling: from now on, X is said as Y."""
    conn = connect()
    conn.execute("INSERT OR REPLACE INTO overload (dont_say, say, why) VALUES (?,?,?)", (dont_say, say, why))
    conn.commit()
    return f"ruled  do not say {dont_say!r} — say {say!r}"


REGISTERS = ("code", "surface", "prose", "all")

# What a scope hint in a ruling's parenthetical tells us about WHERE it
# applies. Only these two registers can be inferred; everything else is
# left to a human, because guessing a scope is worse than admitting none.
_REGISTER_HINTS = (
    ("surface", ("surface", "person reads", "a user", "the ui", "on screen",
                 "read it", "app surface")),
    ("code", ("in code", "the code", "as a symbol", "a field", "the field")),
)

_SCOPED = re.compile(r"^(?P<term>[^(]+?)\s*\((?P<hint>[^)]*)\)\s*$")


def _primary(say: str) -> str:
    """The word a ruling points at. A ruling may elaborate ('Artifact — the
    surface word; …') or offer alternatives ('session · key · credits'); the
    route carries the first, and `why` keeps the sentence whole."""
    return re.split(r"\s*[—–;,·|]\s*|\s+/\s+", say.strip())[0].strip()


def route_add(from_term: str, to_word: str, *, register: str = "all",
              scope: str | None = None, why: str | None = None,
              ruled_on: str | None = None, origin: str | None = None) -> str:
    """Record that a term routes to a word, and WHERE that holds.

    A target that is not (yet) a word is recorded and reported, never
    refused: `Artifact` was retired in code and reinstated on the surface,
    and a ledger that could not hold that could not describe the decision.
    An orphan route is a finding, not an error at the door.
    """
    if register not in REGISTERS:
        return (f"REFUSED — register {register!r} is not one of "
                f"{', '.join(REGISTERS)}. The register is what makes a ruling "
                f"enforceable: `workspace` is right in code and wrong on the surface.")
    conn = connect()
    note = ""
    if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (to_word.lower(),)).fetchone():
        note = (f"\n  note: {to_word!r} is not a word yet — the route is recorded, "
                f"and `monty onto routes --orphans` will keep reporting it "
                f"until you add it or repoint the route.")
    # `all` and a named register are mutually exclusive for one pair: `all`
    # already covers the named one, so keeping both would double every
    # finding and make scoping a route look like adding a second ruling.
    # Scoping is a MOVE.
    moved = ""
    if register == "all":
        cur = conn.execute("DELETE FROM route WHERE lower(from_term)=? AND lower(to_word)=? "
                           "AND register<>'all'", (from_term.lower(), to_word.lower()))
    else:
        cur = conn.execute("DELETE FROM route WHERE lower(from_term)=? AND lower(to_word)=? "
                           "AND register='all'", (from_term.lower(), to_word.lower()))
    if cur.rowcount:
        moved = f" (narrowed from 'all')" if register != "all" else " (widened to 'all')"
    conn.execute(
        "INSERT OR REPLACE INTO route (from_term, to_word, register, scope, ruled_on, why, origin) "
        "VALUES (?,?,?,?,?,?,?)",
        (from_term.strip(), to_word.strip(), register, scope, ruled_on, why, origin))
    conn.commit()
    note = moved + note
    where = f" in {register}" + (f" ({scope})" if scope else "")
    return f"routed  {from_term!r} → {to_word!r}{where}{note}"


def routes(register: str | None = None) -> list[dict]:
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        sql = "SELECT * FROM route"
        args: list = []
        if register:
            sql += " WHERE register=?"
            args.append(register)
        return [dict(r) for r in conn.execute(sql + " ORDER BY from_term, register", args)]
    except sqlite3.OperationalError:
        return []


def route_drop(from_term: str, to_word: str, register: str) -> str:
    conn = connect()
    cur = conn.execute("DELETE FROM route WHERE from_term=? AND to_word=? AND register=?",
                       (from_term, to_word, register))
    conn.commit()
    return (f"dropped  {from_term!r} → {to_word!r} in {register}" if cur.rowcount
            else f"no such route: {from_term!r} → {to_word!r} in {register}")


def route_drafts() -> list[dict]:
    """What the existing rulings and renames IMPLY, parsed, written nowhere.

    Every ruling already carries its scope — in a parenthetical no machine
    can read. This lifts it into columns so a human can confirm it row by
    row. Where the parenthetical does not name a register, the draft says
    so rather than guessing: an unscopable route is advisory forever, and
    that is the honest outcome, not a defect to paper over.
    """
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    known = {r[0].lower() for r in conn.execute("SELECT name FROM word")}
    have = {(r["from_term"].lower(), r["register"]) for r in routes()}
    out: list[dict] = []

    try:
        rulings = list(conn.execute("SELECT dont_say, say, why FROM overload"))
    except sqlite3.OperationalError:
        rulings = []
    for r in rulings:
        m = _SCOPED.match(r["dont_say"])
        term = (m.group("term") if m else r["dont_say"]).strip()
        hint = (m.group("hint") if m else "").strip()
        register = "all"
        for name, needles in _REGISTER_HINTS:
            if any(n in hint.lower() for n in needles):
                register = name
                break
        target = _primary(r["say"])
        if (term.lower(), register) in have:
            continue
        have.add((term.lower(), register))   # `artifact` and `Artifact` are one term
        out.append({
            "from_term": term, "to_word": target, "register": register,
            "scope": None, "hint": hint, "why": r["why"],
            "source": "overload", "known_target": target.lower() in known,
        })

    for r in conn.execute("SELECT was, now, renamed_on, why FROM renamed"):
        term, target = r["was"].strip(), _primary(r["now"])
        if (term.lower(), "all") in have or target.endswith("/"):
            continue  # `bend -> harness/` renamed a DIRECTORY, not a word
        have.add((term.lower(), "all"))
        out.append({
            "from_term": term, "to_word": target, "register": "all",
            "scope": None, "hint": "", "why": r["why"], "ruled_on": r["renamed_on"],
            "source": "renamed", "known_target": target.lower() in known,
        })
    return out


def words(kind: str | None = None) -> list[dict]:
    if DB_PATH is None and not db_path().exists():
        return []
    conn = connect(readonly=db_path().exists())
    cols = "name, kind, owner, definition, test, code, pos"
    if "pos" not in {r[1] for r in conn.execute("PRAGMA table_info(word)")}:
        cols = cols.replace(", pos", "")   # a db older than the column, read-only
    sql = f"SELECT {cols} FROM word"  # noqa: S608 — the columns are ours, not a caller's
    args: list = []
    if kind:
        sql += " WHERE kind=?"
        args.append(kind)
    return [{"pos": None, **dict(r)}
            for r in conn.execute(sql + " ORDER BY kind, name", args)]


def overloads() -> list[dict]:
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM overload ORDER BY dont_say")]
    except sqlite3.OperationalError:
        return []


def doctrines() -> list[dict]:
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM doctrine ORDER BY ord")]
    except sqlite3.OperationalError:
        return []


TOKEN_CATEGORIES = ("color", "space", "radius", "shadow", "font", "breakpoint", "recipe")


def token_add(name: str, category: str, value: str, note: str | None = None) -> str:
    """Name a design value. Same contract as words: one name, one value."""
    if category not in TOKEN_CATEGORIES:
        return f"REFUSED — category must be one of: {', '.join(TOKEN_CATEGORIES)}"
    conn = connect()
    have = conn.execute("SELECT value FROM token WHERE lower(name)=?", (name.lower(),)).fetchone()
    if have and have[0] != value.strip():
        return (f"REFUSED — token {name!r} already means {have[0]!r}. One name, one "
                "value; re-value it deliberately by deleting first, or pick a new name.")
    conn.execute("INSERT OR REPLACE INTO token (name, category, value, note) VALUES (?,?,?,?)",
                 (name.strip(), category, value.strip(), note))
    conn.commit()
    return f"token  {name} ({category}) = {value.strip()}"


def tokens(category: str | None = None) -> list[dict]:
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        conn.execute("SELECT 1 FROM token LIMIT 1")
    except sqlite3.OperationalError:
        return []
    sql = "SELECT * FROM token"
    args: list = []
    if category:
        sql += " WHERE category=?"
        args.append(category)
    return [dict(r) for r in conn.execute(sql + " ORDER BY category, name", args)]


def collide(term: str, theirs: str, their_meaning: str, ruling: str) -> str:
    """Record a boundary collision ruling. The ruling says which side moved
    ("WE MOVED — ours became X" / "theirs; always qualify") so the next
    reader inherits the decision, not the argument."""
    from datetime import UTC, datetime

    conn = connect()
    conn.execute("INSERT OR REPLACE INTO collision (term, theirs, their_meaning, ruling, decided) VALUES (?,?,?,?,?)",
                 (term.strip(), theirs.strip(), their_meaning.strip(), ruling.strip(),
                  str(datetime.now(UTC).date())))
    conn.commit()
    return f"ruled  {term!r} vs {theirs}: {ruling.strip()}"


def rename_word(was: str, now: str, why: str) -> str:
    """Rename a word and ledger it: the row moves, the old name is blocked,
    and material written before the date stays readable through the entry.
    `why` is required — a rename without a reason is churn."""
    from datetime import UTC, datetime

    if not why.strip():
        return "REFUSED — a rename needs its why; that is what the ledger is FOR."
    conn = connect()
    row = conn.execute("SELECT * FROM word WHERE lower(name)=?", (was.lower(),)).fetchone()
    taken = check(now, conn)
    if taken:
        return "REFUSED — the new name is spoken for:\n" + "\n".join(taken)
    if row:
        conn.execute("UPDATE word SET name=? WHERE name=?", (now.strip(), row["name"]))
    conn.execute("INSERT OR REPLACE INTO renamed (was, now, renamed_on, why) VALUES (?,?,?,?)",
                 (was.strip(), now.strip(), str(datetime.now(UTC).date()), why.strip()))
    conn.commit()
    moved = "row moved, " if row else "no existing row (history recorded), "
    return f"renamed  {was!r} -> {now!r} ({moved}old name retired, ledgered)"


# What an amendment may touch. NOT the name: renaming retires the old name
# and is read through its own ledger, so it stays `rename`, and NOT the
# kind, which decides whether the word is enforced at the gate — that is a
# ruling about the vocabulary, not a correction of one word's text.
#
# `pos` IS amendable, on the other side of that same line: it decides how a
# collision is JUDGED, never whether the word is gated, and a word recorded
# as a noun that is plainly a verb is a mistake in the record — exactly what
# amend is for.
AMENDABLE = ("definition", "test", "note", "code", "owner", "pos")


def _shown(value: str | None) -> str:
    return repr(value) if value else "(nothing)"


def _no_word_to_amend(conn: sqlite3.Connection, name: str) -> str:
    """`add` refuses a name that IS taken; amend refuses one that is not —
    the same contract read from the other side, so the refusal carries the
    same material: everything known about the name, and the way forward."""
    from difflib import get_close_matches

    known = [r[0] for r in conn.execute("SELECT name FROM word ORDER BY name")]
    out = [f"REFUSED — {name!r} is not a word; amend corrects what is already recorded."]
    out += check(name, conn)  # renamed? ruled on? then the finding says where it went
    near = get_close_matches(name.strip().lower(), [k.lower() for k in known], n=3, cutoff=0.7)
    if near:
        out.append(f"  did you mean: {', '.join(near)}?")
    out.append(f'  author it instead: monty onto add "{name.strip()}" "<definition>"')
    return "\n".join(out)


def _nothing_to_amend(conn: sqlite3.Connection, word: str) -> str:
    """Called with no field at all. The refusal doubles as the read path:
    what this word has already been amended to say, oldest first."""
    out = [f"REFUSED — amend needs a field: {', '.join('--' + f for f in AMENDABLE)}. "
           "The NAME is not one of them; that is `monty onto rename`, which "
           "retires the old name instead of correcting it."]
    rows = conn.execute("SELECT * FROM amended WHERE lower(word)=? ORDER BY rowid",
                        (word.lower(),)).fetchall()
    if rows:
        out.append(f"  ledgered so far for {word}:")
        out += [f"    {r['amended_on']}  {r['field']} said {_shown(r['was'])}"
                + (f" — {r['why']}" if r["why"] else "") for r in rows]
    return "\n".join(out)


def amend(name: str, *, definition: str | None = None, test: str | None = None,
          note: str | None = None, code: str | None = None,
          owner: str | None = None, pos: str | None = None,
          why: str | None = None) -> str:
    """Correct what a word already says — the counterpart to `add`.

    A recorded meaning goes wrong on its own: a later ruling narrows it,
    the test was written loosely, the code was filed under the wrong
    parent. Until this there was no authoring path for that — the repair
    was an UPDATE against the database, editing the source of truth behind
    the door that is supposed to guard it, while the gate went on policing
    prose drift with no supported way to fix the prose.

    So: the name and its history stay, a field left None is left alone,
    every field that actually CHANGES is ledgered with the text it
    replaced, and an amendment that would change nothing is refused —
    a no-op would write a change that never happened. Passing an empty
    string clears an optional field, because "" is a thing a note can
    stop saying; a definition is the one field that cannot be emptied.
    """
    from datetime import UTC, datetime

    conn = connect()
    row = conn.execute("SELECT * FROM word WHERE lower(name)=?",
                       (name.strip().lower(),)).fetchone()
    if row is None:
        return _no_word_to_amend(conn, name)

    given = {f: v for f, v in (("definition", definition), ("test", test), ("note", note),
                               ("code", code), ("owner", owner), ("pos", pos))
             if v is not None}
    if not given:
        return _nothing_to_amend(conn, row["name"])
    proposed = {f: (v.strip() or None) for f, v in given.items()}

    if "pos" in proposed and proposed["pos"] and proposed["pos"] not in POS:
        return (f"REFUSED — pos {proposed['pos']!r} is not one of {', '.join(POS)}. "
                "It is what the word NAMES; `kind` already carries whose it is.")
    if "definition" in proposed and proposed["definition"] is None:
        return (f"REFUSED — {row['name']!r} cannot be left without a definition: that is "
                "a name squatting on meaning, and the lint fails on it. Amend it to "
                "what it should say, or `monty onto rename` it out of the way.")
    if "owner" in proposed and (new_owner := proposed["owner"]):
        if new_owner.lower() == row["name"].lower():
            return f"REFUSED — {row['name']!r} cannot live inside itself."
        if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?",
                            (new_owner.lower(),)).fetchone():
            known = [r[0] for r in conn.execute("SELECT name FROM word ORDER BY name")]
            return (f"REFUSED — owner {new_owner!r} is not a word yet. Add it first, "
                    f"or pick from: {', '.join(known[:20]) or '(none yet)'}")
        # Ownership is a tree like codes are. Walk up from the proposed
        # owner: if the chain comes back to this word, the move would close
        # a loop nothing could render.
        seen, up = {row["name"].lower()}, new_owner
        while up:
            if up.lower() in seen:
                return (f"REFUSED — {new_owner!r} already lives inside {row['name']!r}; "
                        "owning it back would close the loop. Move the child out first.")
            seen.add(up.lower())
            parent = conn.execute("SELECT owner FROM word WHERE lower(name)=?",
                                  (up.lower(),)).fetchone()
            up = parent[0] if parent else None
    if "code" in proposed:
        new_code = proposed["code"]
        children = ([r[0] for r in conn.execute("SELECT name FROM word WHERE code LIKE ?",
                                                (row["code"] + ".%",))] if row["code"] else [])
        if children and new_code != row["code"]:
            return (f"REFUSED — {len(children)} word(s) live inside code {row['code']!r} "
                    f"({', '.join(children[:6])}). Re-coding this one strands them: a "
                    "dotted code's prefix must resolve to a word. Re-code the children first.")
        if new_code:
            if not CODE_RE.match(new_code):
                return f"REFUSED — code {new_code!r} is not dotted-lowercase (like `har` or `har.cell`)."
            taken = conn.execute("SELECT name FROM word WHERE code=? AND name<>?",
                                 (new_code, row["name"])).fetchone()
            if taken:
                return f"REFUSED — code {new_code!r} already belongs to {taken[0]!r}."
            if "." in new_code:
                prefix = new_code.rsplit(".", 1)[0]
                if not conn.execute("SELECT 1 FROM word WHERE code=?", (prefix,)).fetchone():
                    return (f"REFUSED — code prefix {prefix!r} resolves to no word. "
                            "Dotted codes live INSIDE a word that holds the prefix.")

    changed = {f: v for f, v in proposed.items() if v != row[f]}
    if not changed:
        return (f"REFUSED — nothing to amend: {row['name']} already says exactly that "
                f"({', '.join(proposed)}). An amendment that changes nothing would "
                "ledger a correction that never happened.")

    when = str(datetime.now(UTC).date())
    for field, value in changed.items():
        conn.execute("INSERT INTO amended (word, field, was, amended_on, why) VALUES (?,?,?,?,?)",
                     (row["name"], field, row[field], when, (why or "").strip() or None))
    # The column names are ours — AMENDABLE keys, never the caller's string;
    # the values are bound.
    sets = ", ".join(f"{f}=?" for f in changed)
    conn.execute(f"UPDATE word SET {sets} WHERE name=?", (*changed.values(), row["name"]))  # noqa: S608
    conn.commit()
    out = [f"amended  {row['name']} ({when}, ledgered — the old text stays recoverable)"]
    out += [f"  {f}: {_shown(row[f])} -> {_shown(v)}" for f, v in changed.items()]
    if row["origin"]:
        # Inherited rows are replaced wholesale on every pull — the org's
        # vocabulary is the org's to change. Said out loud, because a
        # correction that quietly evaporates on the next pull is worse than
        # one that was refused.
        out.append(f"  note: inherited from {row['origin']} — `monty onto pull` "
                   "replaces it wholesale. Amend it upstream too, or this is temporary.")
    return "\n".join(out)


# ── exceptions: a symbol may share a word's name, HERE, for this reason ───

TREE_WIDE = "**"


def _shapes(rows: list[dict] | None) -> dict[str, list[dict]]:
    """Declared types of one name, grouped by what they say. Two groups is
    two things wearing one noun; the caller decides what that costs."""
    out: dict[str, list[dict]] = {}
    for r in rows or []:
        out.setdefault(r["value"], []).append(r)
    return out


def _divergence_lines(word: str, shapes: dict[str, list[dict]]) -> list[str]:
    lines = [f"  {word!r} is declared as {len(shapes)} different values:"]
    for value, rows in shapes.items():
        at = ", ".join(f"{r['file']}:{r['line']}" for r in rows[:3])
        lines.append(f"    {value}\n      {at}")
    return lines


def except_add(word: str, why: str, *, scope: str | None = None,
               types: list[dict] | None = None, origin: str | None = None) -> str:
    """Record that a symbol may share this word's name — with its reason and
    the place it holds.

    The four cases turn on the word's part of speech, so a word without one
    cannot be judged and is refused with the repair. `types` is what the
    scan measured about this name where the language declares its types; it
    is passed IN because measuring code is the scan's job, not the
    database's. Passing nothing means nothing was comparable, which is
    recorded as `unchecked` rather than read as agreement.
    """
    from datetime import UTC, datetime

    if not why.strip():
        return ("REFUSED — an exception needs its why. A reasonless allow-list is how "
                "a gate stops being read: six months on, nobody can tell a decision "
                "from a shrug, and the entry outlives the reason it was granted for.")
    conn = connect()
    row = conn.execute("SELECT * FROM word WHERE lower(name)=?",
                       (word.strip().lower(),)).fetchone()
    if row is None:
        return (f"REFUSED — {word!r} is not a word, so nothing collides with it and "
                "there is nothing to except. Check what you meant: "
                f"monty onto check {word.strip()}")
    pos = row["pos"] if "pos" in row.keys() else None
    if not pos:
        return (f"REFUSED — {row['name']!r} has no part of speech, and the four cases "
                "turn on it: a verb below the surface is ordinary, a noun answering "
                "for a second thing is the defect this gate exists for, and a value "
                "type promises interchangeability. Repair: "
                f"monty onto amend {row['name']} --pos verb|noun|value --why "
                "\"what it names\"")

    shapes = _shapes(types)
    checked = "consistent" if len(shapes) == 1 else ("unchecked" if not shapes else "diverged")
    notes: list[str] = []
    if len(shapes) > 1:
        # THE VALUE-TYPE GUARD. A value type's whole content is that one name
        # holds one value; two declared shapes contradict the word itself, so
        # there is nothing to except yet — the word or the code is wrong.
        if pos == "value":
            return "\n".join([
                f"REFUSED — {row['name']!r} is a value type, and the code already "
                "declares it as more than one value. An exception says a SYMBOL may "
                "share the name; it cannot say the NAME may mean two values.",
                *_divergence_lines(row["name"], shapes),
                "  Could you pass one where the other is expected? If not, two things "
                "are wearing one noun: rename one of them, or amend the word if it is "
                "the definition that is wrong. `monty lint` fails on this either way — "
                "no exception silences it.",
            ])
        notes += ["  warn: the code declares this name as more than one value —"]
        notes += ["  " + line for line in _divergence_lines(row["name"], shapes)[1:]]
        notes += ["  a noun may have two renderings of one thing; if these are two "
                  "THINGS, the exception is the wrong repair and a rename is the right "
                  "one. `monty lint` keeps reporting it."]

    scope = (scope or TREE_WIDE).strip() or TREE_WIDE
    conn.execute(
        "INSERT OR REPLACE INTO exception (word, scope, why, judged, checked, granted_on, origin) "
        "VALUES (?,?,?,?,?,?,?)",
        (row["name"], scope, why.strip(), pos, checked,
         str(datetime.now(UTC).date()), origin))
    conn.commit()
    where = "tree-wide" if scope == TREE_WIDE else scope
    out = [f"excepted  {row['name']!r} ({pos}) in {where} — {why.strip()}"]
    if scope == TREE_WIDE:
        out.append("  note: tree-wide. Shane's `open` case is not \"open is always "
                   "fine\" but \"open is fine BELOW the surface\" — a scope is what "
                   "makes that difference sayable: --where \"lib/**\"")
    if checked == "unchecked":
        out.append("  note: unchecked — nothing declared this name as a type in a "
                   "language montology can compare, so nothing verified that these "
                   "two are the same thing. The reason above is the only evidence.")
    return "\n".join(out + notes)


def exceptions(word: str | None = None) -> list[dict]:
    if DB_PATH is None and not db_path().exists():
        return []
    conn = connect(readonly=db_path().exists())
    sql = "SELECT * FROM exception"
    args: list = []
    if word:
        sql += " WHERE lower(word)=?"
        args.append(word.strip().lower())
    try:
        return [dict(r) for r in conn.execute(sql + " ORDER BY word, scope", args)]
    except sqlite3.OperationalError:
        return []


def except_drop(word: str, scope: str | None = None) -> str:
    conn = connect()
    scope = (scope or TREE_WIDE).strip() or TREE_WIDE
    cur = conn.execute("DELETE FROM exception WHERE lower(word)=? AND scope=?",
                       (word.strip().lower(), scope))
    conn.commit()
    return (f"dropped  the exception on {word!r} in {scope}" if cur.rowcount
            else f"no exception on {word!r} in {scope}")


# ── the genus: the one structural relation that gates something ────────────
#
# It is called `genus` and not `kind-of` because `kind` already means
# provenance here — whose word it is — and one root meaning two things is the
# failure the vocabulary exists to prevent. `genus` is also the older and more
# exact word: a definition is a genus narrowed by a differentia, which is what
# every definition in this database already is.

# OntoClean's metaproperty, and only this one. Identity and unity need a
# judgement the tool cannot supply, and a metaproperty nobody fills in
# correctly is worse than none.
#
#   rigid      — what a thing IS, and cannot stop being: a person, a file.
#   anti-rigid — a role a thing PLAYS for a while: a student, a reviewer.
#
# The constraint that follows: a rigid word may not be a kind of an anti-rigid
# one. `person kind-of student` is the classic error — every student is a
# person, but a person is not a kind of student, because they stop.
RIGIDITY = ("rigid", "anti-rigid")


def genus_chain(word: str, conn: sqlite3.Connection | None = None) -> list[str]:
    """Every word this one is a kind of, transitively, nearest first.

    A cycle is reported by simply not walking it twice: a vocabulary can
    contain one (it is a finding, not a crash), and an instrument that hangs
    on it is useless exactly when it is needed — the same rule `chains`
    follows for routes.
    """
    c = conn or connect(readonly=True)
    if not _has_genus(c):
        return []
    seen, out, front = {word.lower()}, [], [word.lower()]
    while front:
        nxt = []
        for name in front:
            for row in c.execute("SELECT genus_name FROM genus WHERE lower(word_name)=?", (name,)):
                g = row[0]
                if g.lower() in seen:
                    continue
                seen.add(g.lower())
                out.append(g)
                nxt.append(g.lower())
        front = nxt
    return out


def _has_genus(conn: sqlite3.Connection) -> bool:
    """A database written before the genus landed simply has no genus, which is
    a fact and not a failure — the same rule the settings instrument follows.
    A read-only connection cannot migrate, and crashing a reader over a table
    the writer will create is a worse answer than an empty list."""
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='genus'").fetchone())


def genera(word: str | None = None) -> list[dict]:
    conn = connect(readonly=True)
    if not _has_genus(conn):
        return []
    sql = "SELECT * FROM genus"
    args: list = []
    if word:
        sql += " WHERE lower(word_name)=?"
        args.append(word.lower())
    return [dict(r) for r in conn.execute(sql + " ORDER BY word_name, genus_name", args)]


def rigidity_set(word: str, value: str) -> str:
    """Judge what kind of thing a word names, so its subsumptions can be checked."""
    if value not in RIGIDITY:
        return (f"REFUSED — rigidity is {' or '.join(RIGIDITY)}, not {value!r}. "
                "Rigid is what a thing IS and cannot stop being; anti-rigid is a "
                "role it plays for a while.")
    conn = connect()
    if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (word.lower(),)).fetchone():
        return f"REFUSED — {word!r} is not a word. Add it first (`monty onto add`)."
    conn.execute("UPDATE word SET rigidity=? WHERE lower(name)=?", (value, word.lower()))
    conn.commit()
    return f"judged  {word} is {value}"


def genus_add(word: str, genus: str, *, why: str | None = None,
              ruled_on: str | None = None, origin: str | None = None) -> str:
    """Record that a word is a kind of another word.

    Refused rather than recorded when it cannot mean anything: an unknown word
    at either end, a word being a kind of itself, a cycle, or a subsumption
    OntoClean rules out. Unlike a route — which may point at a word that does
    not exist yet, because a ledger has to be able to describe a decision taken
    before its target landed — a genus asserts something about two things that
    must both already be here for the assertion to have content.
    """
    conn = connect()
    if word.lower() == genus.lower():
        return f"REFUSED — {word!r} cannot be a kind of itself."
    for name, role in ((word, "the word"), (genus, "the genus")):
        if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (name.lower(),)).fetchone():
            return (f"REFUSED — {name!r} is not a word, and {role} has to be one. "
                    f"Repair: `monty onto add {name!r} \"<definition>\"` first.")

    if word.lower() in {g.lower() for g in genus_chain(genus, conn)}:
        path = " → ".join([genus, *genus_chain(genus, conn)])
        return (f"REFUSED — that closes a cycle: {path}. A word cannot be a kind "
                f"of something that is already a kind of it.")

    rows = {r["name"].lower(): r for r in conn.execute(
        "SELECT name, rigidity, owner FROM word WHERE lower(name) IN (?,?)",
        (word.lower(), genus.lower()))}
    w, g = rows[word.lower()], rows[genus.lower()]
    if w["rigidity"] == "rigid" and g["rigidity"] == "anti-rigid":
        return (f"REFUSED — {word!r} is rigid and {genus!r} is anti-rigid. A thing "
                f"cannot permanently be a kind of something it stops being: every "
                f"{genus} is a {word}, not the other way round. Repair: reverse it, "
                f"or re-judge one of them with `monty onto rigidity`.")

    conn.execute("INSERT OR REPLACE INTO genus (word_name, genus_name, ruled_on, why, origin) "
                 "VALUES (?,?,?,?,?)", (word, genus, ruled_on, why, origin))
    conn.commit()
    line = f"genus  {word} is a kind of {genus}"
    # The confusion this relation exists to survive. `scan.collision` lives
    # inside `scan` and is NOT a kind of scan; saying both is usually a sign
    # that containment was mistaken for subsumption.
    if w["owner"] and w["owner"].lower() == genus.lower():
        line += (f"\n  note: {genus!r} is also {word!r}'s owner. Containment says "
                 f"where a word LIVES; a genus says what it IS. They are often "
                 f"different — check this one is both.")
    return line


def genus_drop(word: str, genus: str) -> str:
    conn = connect()
    cur = conn.execute("DELETE FROM genus WHERE lower(word_name)=? AND lower(genus_name)=?",
                       (word.lower(), genus.lower()))
    conn.commit()
    return (f"dropped  {word} is no longer a kind of {genus}" if cur.rowcount
            else f"nothing to drop — {word!r} was not recorded as a kind of {genus!r}.")


def inherited(word: str) -> list[dict]:
    """The rulings a word gets from what it is a kind of.

    This is what makes the genus worth having: it is not decoration on a
    diagram, it changes what the gate knows. An inherited ruling that is
    invisible is a trap, so everything that shows a word's own rulings shows
    these beside them, saying which ancestor they came from.
    """
    conn = connect(readonly=True)
    out: list[dict] = []
    for ancestor in genus_chain(word, conn):
        low = ancestor.lower()
        for r in conn.execute("SELECT dont_say, say, why FROM overload WHERE lower(say)=?", (low,)):
            out.append({"from": ancestor, "kind": "overload", "detail":
                        f"do not say {r['dont_say']!r} — say {r['say']!r}"})
        for r in conn.execute("SELECT term, theirs, ruling FROM collision WHERE lower(term)=?", (low,)):
            out.append({"from": ancestor, "kind": "collision", "detail":
                        f"{r['term']} vs {r['theirs']}: {r['ruling']}"})
        for r in conn.execute("SELECT was, now FROM renamed WHERE lower(now)=?", (low,)):
            out.append({"from": ancestor, "kind": "renamed", "detail":
                        f"{r['was']} was retired in favour of {r['now']}"})
    return out


def collisions() -> list[dict]:
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM collision ORDER BY term")]
    except sqlite3.OperationalError:
        return []


def renames() -> list[dict]:
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM renamed ORDER BY renamed_on, was")]
    except sqlite3.OperationalError:
        return []


def amendments(word: str | None = None) -> list[dict]:
    """The amendment ledger, oldest first — where the old text is recovered
    from. Not rendered into the words skill, deliberately: the skill states
    what a word means NOW, and unlike an old NAME (which is still sitting in
    old code and old tickets) an old definition appears nowhere but here."""
    if not db_path().exists():
        return []
    conn = connect(readonly=True)
    sql = "SELECT * FROM amended"
    args: list = []
    if word:
        sql += " WHERE lower(word)=?"
        args.append(word.strip().lower())
    try:
        return [dict(r) for r in conn.execute(sql + " ORDER BY amended_on, rowid", args)]
    except sqlite3.OperationalError:
        return []


def record_run(task: str, target: str, model: str, outcome: str,
               laws_failed: list[str]) -> None:
    from datetime import UTC, datetime

    conn = connect()
    conn.execute("INSERT INTO gen_runs VALUES (?,?,?,?,?,?)",
                 (datetime.now(UTC).isoformat(), task, target, model, outcome,
                  "; ".join(laws_failed)))
    conn.commit()
