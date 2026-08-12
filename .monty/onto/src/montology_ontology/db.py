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


def db_path() -> Path:
    if DB_PATH is not None:
        return DB_PATH
    return workspace_root() / ".monty" / "ontology.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS word (
  name        TEXT PRIMARY KEY,
  kind        TEXT NOT NULL,          -- core | inner | adopted | custom
  owner       TEXT,                   -- which word it lives inside
  definition  TEXT NOT NULL,
  test        TEXT,                   -- the one-line "what is it" test
  note        TEXT,
  code        TEXT UNIQUE,            -- dotted, socialite-style: har, har.cell
  origin      TEXT                    -- NULL = this repo's own; else the upstream source
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
        findings.append(f"TAKEN  {w['name']} ({w['kind']}){code} — {w['definition']}")
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
        owner: str | None = None, code: str | None = None) -> str:
    """Author a word — check-first is the contract: a taken name is refused
    WITH its findings, because one word means one thing."""
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
    conn.execute("INSERT INTO word (name, kind, owner, definition, test, note, code) "
                 "VALUES (?,?,?,?,?,?,?)",
                 (name.strip(), kind, owner, definition.strip(), test, note, code))
    conn.commit()
    tail = f" [{code}]" if code else ""
    return f"added  {name} ({kind}{', inside ' + owner if owner else ''}){tail} — {definition.strip()}"


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
    sql = "SELECT name, kind, owner, definition, test, code FROM word"
    args: list = []
    if kind:
        sql += " WHERE kind=?"
        args.append(kind)
    return [dict(r) for r in conn.execute(sql + " ORDER BY kind, name", args)]


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
AMENDABLE = ("definition", "test", "note", "code", "owner")


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
          owner: str | None = None, why: str | None = None) -> str:
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
                               ("code", code), ("owner", owner)) if v is not None}
    if not given:
        return _nothing_to_amend(conn, row["name"])
    proposed = {f: (v.strip() or None) for f, v in given.items()}

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
