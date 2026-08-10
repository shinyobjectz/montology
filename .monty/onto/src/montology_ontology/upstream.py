"""The org ontology: one vocabulary, N repos.

An organization authors its vocabulary ONCE — in any repo montology has
initialized (the `.monty/ontology.db` IS the artifact) — and every other
repo inherits it:

    monty init --from git@github.com:acme/ontology.git
    monty onto pull        # refresh from the pinned upstream

The merge is deliberate about custody:

  * upstream rows carry their origin and are REPLACED wholesale on every
    pull — the org's vocabulary is the org's to change;
  * local rows (origin NULL) always survive — a repo's own words are its
    own;
  * a name defined in BOTH places is a conflict: local wins, loudly —
    reconcile deliberately, never silently;
  * upstream RENAMES are how a rename crosses the fleet: every pull
    reports them with the exact `monty migrate` command, so each repo's
    code catches up on its own clean tree.

Sources: a git URL (private repos = access control for free), a local
path (a monorepo sibling, a mounted share), or an http(s) URL to the db
file. The pin lives in `montology.toml [ontology] upstream`.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from montology_core import workspace_root

from .db import connect, db_path

_MERGED_TABLES = ("word", "token", "doctrine", "overload", "collision", "renamed")
_PK = {"word": "name", "token": "name", "doctrine": "title",
       "overload": "dont_say", "collision": "term", "renamed": "was"}


def _ensure_origin(conn: sqlite3.Connection) -> None:
    for table in _MERGED_TABLES:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if cols and "origin" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN origin TEXT")


def _looks_like_git(source: str) -> bool:
    return (source.startswith(("git+", "git@", "ssh://"))
            or (source.startswith(("http://", "https://"))
                and not source.endswith(".db")))


def _fetch_db(source: str) -> Path:
    """The upstream db as a local file. Raises ValueError with the repair."""
    if _looks_like_git(source):
        tmp = Path(tempfile.mkdtemp(prefix="monty-upstream-"))
        url = source.removeprefix("git+")
        got = subprocess.run(["git", "clone", "--depth", "1", url, str(tmp / "repo")],
                            capture_output=True, text=True, timeout=300)
        if got.returncode != 0:
            raise ValueError(f"could not clone {url}: {got.stderr.strip()[-200:]} "
                             "— check the URL and your access.")
        for candidate in (tmp / "repo" / ".monty" / "ontology.db",
                          tmp / "repo" / "ontology.db"):
            if candidate.exists():
                return candidate
        raise ValueError(f"{url} has no .monty/ontology.db — is it a montology workspace?")
    if source.startswith(("http://", "https://")):
        tmp = Path(tempfile.mkdtemp(prefix="monty-upstream-")) / "ontology.db"
        try:
            with urllib.request.urlopen(source, timeout=60) as r:
                tmp.write_bytes(r.read())
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"could not download {source}: {e}") from None
        return tmp
    p = Path(source).expanduser()
    for candidate in (p, p / ".monty" / "ontology.db", p / "ontology.db"):
        if candidate.is_file():
            return candidate
    raise ValueError(f"no ontology found at {source} — pass a workspace dir, "
                     "a .db file, a git URL, or an http(s) URL to the db.")


def _pin(root: Path, source: str) -> None:
    toml = root / ".monty" / "montology.toml"
    text = toml.read_text() if toml.exists() else ""
    if "[ontology]" in text:
        text = re.sub(r'(\[ontology\][^\[]*?upstream\s*=\s*")[^"]*(")',
                      rf"\g<1>{source}\g<2>", text, count=1, flags=re.S)
        if f'upstream = "{source}"' not in text:
            text = text.replace("[ontology]", f'[ontology]\nupstream = "{source}"', 1)
    else:
        text = text.rstrip() + f'\n\n[ontology]\nupstream = "{source}"\n'
    toml.write_text(text)


def pinned_upstream(root: Path | None = None) -> str | None:
    import tomllib

    root = root or workspace_root()
    toml = root / ".monty" / "montology.toml"
    if not toml.exists():
        return None
    try:
        return tomllib.loads(toml.read_text()).get("ontology", {}).get("upstream")
    except tomllib.TOMLDecodeError:
        return None


def pull(source: str | None = None, root: Path | None = None) -> str:
    """Inherit (or refresh) the org vocabulary. Local rows always survive."""
    root = root or workspace_root()
    source = source or pinned_upstream(root)
    if not source:
        return ("no upstream pinned. Repair: monty onto pull <source> "
                "(a git URL, a workspace path, or an http(s) .db URL) — "
                "the source is remembered in montology.toml.")
    try:
        remote_db = _fetch_db(source)
    except ValueError as e:
        return f"REFUSED — {e}"

    remote = sqlite3.connect(f"file:{remote_db}?mode=ro", uri=True)
    remote.row_factory = sqlite3.Row
    local = connect()
    _ensure_origin(local)

    inherited = 0
    conflicts: list[str] = []
    for table in _MERGED_TABLES:
        try:
            rows = remote.execute(f"SELECT * FROM {table}").fetchall()
        except sqlite3.OperationalError:
            continue  # older upstream without this table
        pk = _PK[table]
        local.execute(f"DELETE FROM {table} WHERE origin = ?", (source,))
        for row in rows:
            data = {k: row[k] for k in row.keys() if k != "origin"}
            have = local.execute(
                f"SELECT origin FROM {table} WHERE {pk} = ?", (data[pk],)).fetchone()
            if have is not None and have[0] is None:
                conflicts.append(f"{table}:{data[pk]}")
                continue  # local wins, loudly (below)
            cols = ", ".join(data) + ", origin"
            marks = ", ".join("?" for _ in data) + ", ?"
            local.execute(
                f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({marks})",
                [*data.values(), source])
            inherited += 1
    local.commit()

    # renames are how a rename crosses the fleet
    fleet: list[str] = []
    try:
        for r in remote.execute("SELECT was, now FROM renamed"):
            fleet.append(f"  upstream renamed {r['was']!r} -> {r['now']!r} — "
                         f"propagate here: monty migrate {r['was']} {r['now']} --apply")
    except sqlite3.OperationalError:
        pass

    _pin(root, source)
    report = [f"inherited {inherited} row(s) from {source} (upstream rows refreshed; "
              "local rows untouched)"]
    if conflicts:
        report.append("CONFLICTS — defined both locally and upstream; LOCAL WINS, "
                      "reconcile deliberately: " + ", ".join(conflicts[:10]))
    report.extend(fleet)
    return "\n".join(report)
