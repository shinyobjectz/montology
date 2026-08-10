"""The warehouse connection and its two helpers.

One DuckDB file (warehouse/data/warehouse.duckdb, gitignored — user data
never ships). The registries attach read-only when present; a missing
registry degrades to a note, never an error, because the warehouse must
work before anyone has pulled taxonomies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from montology_core import workspace_root

# Tests pin these directly; when None they resolve lazily from the workspace.
WAREHOUSE_PATH: Path | None = None
_REGISTRIES: dict[str, Path] | None = None


def warehouse_path() -> Path:
    """Where the warehouse lives: pinned, or the workspace's data/
    (gitignored there — user data never ships)."""
    if WAREHOUSE_PATH is not None:
        return WAREHOUSE_PATH
    return workspace_root() / "data" / "warehouse.duckdb"


def _registries_map() -> dict[str, Path]:
    """The registries DuckDB attaches, when they exist."""
    if _REGISTRIES is not None:
        return _REGISTRIES
    data = workspace_root() / "data"
    return {"ontology": data / "ontology.db", "zoo": data / "zoo.db"}


def connect(path: Path | None = None) -> Any:
    """A DuckDB connection with the registries attached read-only.

    The sqlite extension autoloads on first ATTACH (a small download, once).
    Offline first use: the warehouse still opens; only the registry
    attachments are skipped, each with a printed note.
    """
    import duckdb

    target = path or warehouse_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(target))
    for name, registry in _registries_map().items():
        if not registry.exists():
            continue  # not pulled yet — monty data pull / zoo sync
        try:
            conn.execute(f"ATTACH '{registry}' AS {name} (TYPE sqlite, READ_ONLY)")
        except Exception as e:  # noqa: BLE001 — extension not fetchable offline
            print(f"[warehouse] {name} not attached: {e}", flush=True)
    return conn


def query(sql: str, conn: Any = None) -> str:
    """Run SQL, answer as an aligned text table (capped at 200 rows).

    Errors come back as text WITH the repair — the reader is a marketer or
    an agent mid-loop, and a traceback helps neither.
    """
    c = conn or connect()
    try:
        rel = c.sql(sql)
        if rel is None:
            return "ok (no result set)"
        rows = rel.fetchmany(201)
        cols = [d[0] for d in rel.description]
    except Exception as e:  # noqa: BLE001
        return (
            f"SQL error: {e}\n"
            "Tables live in the warehouse (main.*), the registries "
            "(ontology.word, ontology.taxonomy, zoo.model, zoo.artifact), or "
            "read files directly: SELECT * FROM 'file.csv'."
        )
    if not rows:
        return "(no rows)"
    widths = [max(len(str(col)), *(len(str(r[i])) for r in rows[:200])) for i, col in enumerate(cols)]
    out = ["  ".join(str(c).ljust(w) for c, w in zip(cols, widths))]
    out += ["  ".join(str(v).ljust(w) for v, w in zip(r, widths)) for r in rows[:200]]
    if len(rows) > 200:
        out.append("… (200-row display cap; aggregate or LIMIT for more)")
    return "\n".join(out)


def load_file(path: str, table: str, conn: Any = None) -> str:
    """Load a CSV/Parquet/JSON file into a named warehouse table.

    DuckDB sniffs the format and schema; the answer states what landed so
    the very next question can be SQL.
    """
    c = conn or connect()
    src = Path(path).expanduser()
    if not src.exists():
        return f"no such file: {path}"
    if not table.replace("_", "").isalnum():
        return f"table name {table!r} must be letters, digits and underscores"
    try:
        c.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM '{src}'")
        n = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        cols = [r[0] for r in c.execute(f"DESCRIBE {table}").fetchall()]
        return f"loaded {n} rows into {table} ({', '.join(cols[:12])}{'…' if len(cols) > 12 else ''})"
    except Exception as e:  # noqa: BLE001
        return f"could not load {path}: {e}"
