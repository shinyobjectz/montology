"""The database: house words and ingested taxonomies, one SQLite file.

Two tables, deliberately separate:

  * ``word`` — OUR vocabulary: a term montology defines, with a one-line
    definition and a test. Authored only in ``seed.py``.
  * ``taxonomy`` — THEIR vocabularies: rows ingested from registered sources
    (``sources.py``), namespaced by source id so ``iab-content:53`` and a
    house word can never collide.

The join is the point: a house word may ``map_to`` taxonomy rows, which is
how "what we call it" stays connected to "what the industry transacts in".
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from montology_core import workspace_root

# Tests pin DB_PATH directly; when None it resolves lazily from the
# workspace (the tracked data/ store — the user asked for the dbs in git).
DB_PATH: Path | None = None


def db_path() -> Path:
    """Where the ontology db lives: pinned, or the workspace's data/."""
    if DB_PATH is not None:
        return DB_PATH
    return workspace_root() / "data" / "ontology.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS word (
  name        TEXT PRIMARY KEY,
  kind        TEXT NOT NULL,          -- core | inner | adopted
  owner       TEXT,                   -- which core word it lives inside
  definition  TEXT NOT NULL,
  test        TEXT,                   -- the one-line "what is it" test
  note        TEXT,
  code        TEXT                   -- optional dotted code, socialite-style
);

CREATE TABLE IF NOT EXISTS taxonomy (
  source      TEXT NOT NULL,          -- sources.py id, e.g. 'iab-content'
  code        TEXT NOT NULL,          -- the source's own id for the row
  name        TEXT NOT NULL,
  parent      TEXT,                   -- parent code within the same source
  tier        INTEGER,
  path        TEXT,                   -- 'Tier1 > Tier2 > name' for display
  PRIMARY KEY (source, code)
);

CREATE TABLE IF NOT EXISTS mapping (
  word        TEXT NOT NULL REFERENCES word(name),
  source      TEXT NOT NULL,
  code        TEXT NOT NULL,
  note        TEXT,
  PRIMARY KEY (word, source, code)
);

CREATE INDEX IF NOT EXISTS taxonomy_name ON taxonomy(name);
"""


def connect(path: Path | None = None, *, readonly: bool = False) -> sqlite3.Connection:
    target = path or db_path()
    if readonly:
        c = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(target)
        c.executescript(SCHEMA)
    c.row_factory = sqlite3.Row
    return c


def _migrate(conn: sqlite3.Connection) -> None:
    """Additive migrations only — the db is user data once custom words land."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(word)")}
    if "code" not in cols:
        conn.execute("ALTER TABLE word ADD COLUMN code TEXT")
    if "owner" not in cols:  # pre-migration dbs
        conn.execute("ALTER TABLE word ADD COLUMN owner TEXT")


def add(name: str, definition: str, *, test: str | None = None,
        note: str | None = None, kind: str = "custom",
        owner: str | None = None, code: str | None = None) -> str:
    """Author a word of YOUR OWN — the same table our words live in, so
    every surface (onto check, taxonomy_search, the MCP tools) speaks it
    immediately. Check-first is the contract: a taken name is refused with
    its findings, because one word means one thing. Custom words survive
    re-seeding — the seed only replaces its own names."""
    findings = check(name)
    if findings:
        return "REFUSED — the name is spoken for:\n" + "\n".join(findings) \
            + "\nPick a different word; one word means one thing."
    conn = connect()
    _migrate(conn)
    if owner:
        have = conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (owner.lower(),)).fetchone()
        if not have:
            known = [r[0] for r in conn.execute("SELECT name FROM word ORDER BY name")]
            return (f"REFUSED — owner {owner!r} is not a word yet. Add it first, "
                    f"or pick from: {', '.join(known[:20])}")
    if code:
        taken = conn.execute("SELECT name FROM word WHERE code=?", (code,)).fetchone()
        if taken:
            return f"REFUSED — code {code!r} already belongs to {taken[0]!r}."
    conn.execute("INSERT INTO word (name, kind, owner, definition, test, note, code) "
                 "VALUES (?,?,?,?,?,?,?)",
                 (name.strip(), kind, owner, definition.strip(), test, note, code))
    conn.commit()
    tail = f" [{code}]" if code else ""
    return f"added  {name} ({kind}{', inside ' + owner if owner else ''}){tail} — {definition.strip()}"


def map_word(word: str, source: str, taxo_code: str, note: str | None = None) -> str:
    """Pin a house word to the taxonomy row the industry uses for the same
    idea — the join that makes the ontology RELATIONAL. Both ends must
    exist: an unmapped word is fine, a mapping to nothing is a typo."""
    conn = connect()
    _migrate(conn)
    if not conn.execute("SELECT 1 FROM word WHERE lower(name)=?", (word.lower(),)).fetchone():
        return f"REFUSED — no word named {word!r}. `monty onto add` it first."
    row = conn.execute("SELECT name, path FROM taxonomy WHERE source=? AND code=?",
                       (source, taxo_code)).fetchone()
    if row is None:
        near = conn.execute(
            "SELECT code, name FROM taxonomy WHERE source=? AND name LIKE ? LIMIT 5",
            (source, f"%{word}%")).fetchall()
        hint = ("; near matches: " + ", ".join(f"{r['code']} ({r['name']})" for r in near)) if near else ""
        return (f"REFUSED — {source}:{taxo_code} is not an ingested taxonomy row"
                f" (did you `monty data pull {source}`?){hint}")
    conn.execute("INSERT OR REPLACE INTO mapping VALUES (?,?,?,?)",
                 (word, source, taxo_code, note))
    conn.commit()
    return f"mapped  {word} -> {source}:{taxo_code}  ({row['path'] or row['name']})"


def mappings(word: str | None = None) -> list[dict]:
    conn = connect()
    sql = ("SELECT m.word, m.source, m.code, m.note, t.name, t.path FROM mapping m "
           "LEFT JOIN taxonomy t ON t.source = m.source AND t.code = m.code")
    args: list = []
    if word:
        sql += " WHERE lower(m.word)=?"
        args.append(word.lower())
    return [dict(r) for r in conn.execute(sql + " ORDER BY m.word", args)]


def words(kind: str | None = None) -> list[dict]:
    """The vocabulary as rows — ours and yours, distinguishable by kind."""
    conn = connect(readonly=db_path().exists())
    sql = "SELECT name, kind, definition, test FROM word"
    args: list = []
    if kind:
        sql += " WHERE kind=?"
        args.append(kind)
    return [dict(r) for r in conn.execute(sql + " ORDER BY kind, name", args)]


def check(name: str, c: sqlite3.Connection | None = None) -> list[str]:
    """Is this name spoken for? Returns human-readable findings; [] = free.

    The agent-facing gate: run before naming anything. Checks house words
    first, then exact hits in every ingested taxonomy.
    """
    conn = c or connect(readonly=db_path().exists())
    low = name.strip().lower()
    findings: list[str] = []
    w = conn.execute("SELECT * FROM word WHERE lower(name)=?", (low,)).fetchone()
    if w:
        findings.append(f"TAKEN  {w['name']} ({w['kind']}) — {w['definition']}")
        try:
            for m in conn.execute(
                "SELECT source, code FROM mapping WHERE lower(word)=?", (low,)
            ):
                findings.append(f"       maps to {m['source']}:{m['code']}")
        except sqlite3.OperationalError:
            pass
    for t in conn.execute(
        "SELECT source, code, name, path FROM taxonomy WHERE lower(name)=? LIMIT 10", (low,)
    ):
        findings.append(f"IN TAXONOMY  {t['source']}:{t['code']} — {t['path'] or t['name']}")
    return findings
