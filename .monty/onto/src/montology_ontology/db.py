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
  * ``token`` — DESIGN values as vocabulary: a named color, spacing step,
    radius, shadow, font or breakpoint. A hex code is a word that means
    one thing; the style lint aligns the code to these.
  * ``gen_runs`` — the assay: every generative attempt (word definitions),
    with outcome and failed laws. Memory, queryable.

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


def record_run(task: str, target: str, model: str, outcome: str,
               laws_failed: list[str]) -> None:
    from datetime import UTC, datetime

    conn = connect()
    conn.execute("INSERT INTO gen_runs VALUES (?,?,?,?,?,?)",
                 (datetime.now(UTC).isoformat(), task, target, model, outcome,
                  "; ".join(laws_failed)))
    conn.commit()
