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

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "ontology.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS word (
  name        TEXT PRIMARY KEY,
  kind        TEXT NOT NULL,          -- core | inner | adopted
  owner       TEXT,                   -- which core word it lives inside
  definition  TEXT NOT NULL,
  test        TEXT,                   -- the one-line "what is it" test
  note        TEXT
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
    target = path or DB_PATH
    if readonly:
        c = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(target)
        c.executescript(SCHEMA)
    c.row_factory = sqlite3.Row
    return c


def add(name: str, definition: str, *, test: str | None = None,
        note: str | None = None, kind: str = "custom") -> str:
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
    conn.execute("INSERT INTO word VALUES (?,?,NULL,?,?,?)",
                 (name.strip(), kind, definition.strip(), test, note))
    conn.commit()
    return f"added  {name} ({kind}) — {definition.strip()}"


def words(kind: str | None = None) -> list[dict]:
    """The vocabulary as rows — ours and yours, distinguishable by kind."""
    conn = connect(readonly=DB_PATH.exists())
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
    conn = c or connect(readonly=DB_PATH.exists())
    low = name.strip().lower()
    findings: list[str] = []
    w = conn.execute("SELECT * FROM word WHERE lower(name)=?", (low,)).fetchone()
    if w:
        findings.append(f"TAKEN  {w['name']} ({w['kind']}) — {w['definition']}")
    for t in conn.execute(
        "SELECT source, code, name, path FROM taxonomy WHERE lower(name)=? LIMIT 10", (low,)
    ):
        findings.append(f"IN TAXONOMY  {t['source']}:{t['code']} — {t['path'] or t['name']}")
    return findings
