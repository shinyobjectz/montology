"""A proposal: a pull request for meaning.

montology has a gate but had no review UNIT. Lint tells you the build is broken;
it never told you "here are six changes to the vocabulary, one of them renames a
word forty files depend on — approve or reject". Palantir's proposals are the
model, and we need them more than they do: the ontology is a SQLite file, so
git shows a vocabulary change as a binary blob and there is nothing to read.

A proposal stores INTENTS, not a second copy of the vocabulary. That matters
twice over. Replaying them on merge goes through the same functions a person at
a terminal uses, so an approved proposal can do nothing a CLI user could not.
And a stored intent is readable — `word.add cell` is a diff of MEANING, which
is the thing a binary diff could never be.

The verdict a reviewer needs is not "does this parse" but "what does this BREAK".
So `preview` copies the database, replays the changes into the copy, and runs
the real gate against it — reporting what is newly broken rather than what was
already broken. A rename that would strand forty declarations says so before
approval, not after.
"""

from __future__ import annotations

import json
import secrets
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .db import connect, db_path

OPEN, MERGED, CLOSED = "open", "merged", "closed"
APPROVED, REJECTED = "approved", "rejected"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def propose(title: str, changes: list[dict], *, why: str = "",
            author: str = "") -> str:
    """Open a proposal over a list of {intent, fields}."""
    from .intents import _intents

    if not changes:
        return "REFUSED — a proposal with no changes is a note; write it as doctrine."
    known = _intents()
    unknown = sorted({c.get("intent", "") for c in changes} - set(known))
    if unknown:
        return (f"REFUSED — not an intent: {', '.join(unknown)}. "
                f"Known: {', '.join(sorted(known))}")

    pid = secrets.token_hex(3)
    conn = connect()
    conn.execute("INSERT INTO proposal (id, title, why, author, status, opened_at) "
                 "VALUES (?,?,?,?,?,?)",
                 (pid, title, why or None, author or None, OPEN, _now()))
    for i, c in enumerate(changes):
        conn.execute("INSERT INTO change (proposal_id, ord, intent, fields) VALUES (?,?,?,?)",
                     (pid, i, c["intent"], json.dumps(c.get("fields") or {}, sort_keys=True)))
    conn.commit()
    return f"proposed  {pid}  {title}  ({len(changes)} change(s))"


def proposals(status: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM proposal", []
    if status:
        sql += " WHERE status=?"
        args.append(status)
    conn = connect(readonly=True)
    if not _has(conn):
        return []
    return [dict(r) for r in conn.execute(sql + " ORDER BY opened_at DESC", args)]


def _has(conn) -> bool:
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='proposal'").fetchone())


def changes(pid: str) -> list[dict]:
    conn = connect(readonly=True)
    if not _has(conn):
        return []
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM change WHERE proposal_id=? ORDER BY ord", (pid,))]
    for r in rows:
        r["fields"] = json.loads(r["fields"])
    return rows


def decide(pid: str, ord_: int, verdict: str, note: str = "") -> str:
    """Approve or reject ONE change. Per-change, because a proposal that bundles
    a good rename with a bad definition should not have to be rejected whole."""
    if verdict not in (APPROVED, REJECTED):
        return f"REFUSED — a verdict is {APPROVED} or {REJECTED}, not {verdict!r}."
    conn = connect()
    cur = conn.execute("UPDATE change SET verdict=?, note=? WHERE proposal_id=? AND ord=?",
                       (verdict, note or None, pid, ord_))
    conn.commit()
    if not cur.rowcount:
        return f"REFUSED — no change {ord_} in proposal {pid!r}."
    return f"{verdict}  {pid}#{ord_}"


def preview(pid: str) -> dict:
    """What this proposal would BREAK — the gate run against the merged world.

    The database is copied and the changes replayed into the copy, so nothing
    here can touch the real one. Only findings that are NEW are reported: a
    proposal is not answerable for what was already failing.
    """
    import tempfile

    from . import db as _db

    rows = [c for c in changes(pid) if c["verdict"] != REJECTED]
    if not rows:
        return {"ok": True, "new": [], "note": "nothing to preview"}

    before = _gate_findings()
    real = db_path()
    tmp = Path(tempfile.mkdtemp()) / "shadow.db"
    shutil.copy(real, tmp)

    kept, applied = _db.DB_PATH, []
    try:
        _db.DB_PATH = tmp
        from .intents import apply as apply_intent

        for c in rows:
            applied.append({"ord": c["ord"], "intent": c["intent"],
                            **apply_intent(c["intent"], c["fields"])})
        after = _gate_findings()
    finally:
        _db.DB_PATH = kept

    fresh = [line for line in after if line not in before]
    refused = [a for a in applied if not a["ok"]]
    # A reviewer needs to see everything this would newly raise; only a FAIL
    # may STOP a merge. Most workspaces run collisions advisory, and "your
    # change collides with 40 declarations" is exactly the thing to know before
    # approving even where it does not break the build.
    blocking = [line for line in fresh if line.startswith("FAIL")]
    return {"ok": not blocking and not refused, "new": fresh,
            "blocking": blocking, "applied": applied, "refused": refused}


def _gate_findings() -> list[str]:
    """The real gate, whichever database DB_PATH currently names."""
    try:
        from montology_scan import lint as scan_lint
    except Exception:  # noqa: BLE001 — the ontology must not need the scanner
        return []
    return [line for line in scan_lint()
            if line.startswith("FAIL") or line.startswith("warn")]


def merge(pid: str) -> str:
    """Replay the approved changes into the real database.

    Refused while anything is undecided, while nothing is approved, or while the
    preview says the gate would break. No new enforcement path and no second
    opinion about what correct means — it is the same lint.
    """
    rows = changes(pid)
    if not rows:
        return f"REFUSED — no proposal {pid!r}."
    conn = connect()
    status = conn.execute("SELECT status FROM proposal WHERE id=?", (pid,)).fetchone()
    if status and status[0] != OPEN:
        return f"REFUSED — {pid} is already {status[0]}."

    undecided = [c["ord"] for c in rows if not c["verdict"]]
    if undecided:
        return (f"REFUSED — {len(undecided)} change(s) undecided: "
                f"{', '.join(f'#{o}' for o in undecided)}. "
                f"Repair: `monty onto decide {pid} <n> approved|rejected`")

    approved = [c for c in rows if c["verdict"] == APPROVED]
    if not approved:
        return f"REFUSED — every change was rejected. Close it instead: `monty onto close {pid}`."

    seen = preview(pid)
    if not seen["ok"]:
        lines = seen["blocking"] + [r["line"] for r in seen.get("refused", [])]
        return ("REFUSED — the gate would fail after this merge:\n  "
                + "\n  ".join(lines)
                + "\n  Repair: fix the changes, or reject the ones that break it.")

    from .intents import apply as apply_intent

    done = [apply_intent(c["intent"], c["fields"]) for c in approved]
    conn.execute("UPDATE proposal SET status=?, merged_at=? WHERE id=?", (MERGED, _now(), pid))
    conn.commit()
    return (f"merged  {pid}  ({len(approved)} change(s))\n  "
            + "\n  ".join(d["line"] for d in done))


def close(pid: str) -> str:
    conn = connect()
    cur = conn.execute("UPDATE proposal SET status=? WHERE id=? AND status=?",
                       (CLOSED, pid, OPEN))
    conn.commit()
    return f"closed  {pid}" if cur.rowcount else f"REFUSED — no open proposal {pid!r}."
