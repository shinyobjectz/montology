"""The firewall: drift cannot enter.

Everything else montology does is post-hoc — CI catches drift after it is
written. The guard runs BEFORE the write: an agent-harness hook
(PreToolUse on Write/Edit in Claude Code; any harness that can call a
command with the proposed change) pipes the pending edit in, and the
guard lints ONLY that text against the ontology in milliseconds:

  * a declaration named after a RETIRED word — a rename is a ruling, and
    the ruling includes the future; always blocks;
  * a declaration colliding with an enforced word — blocks under
    ``[scan] collisions = "enforce"``, advises otherwise;
  * a rogue design literal when tokens exist — the repair IS the fix
    (the nearest token, by name), so blocking costs the agent nothing.

Deny is exit 2 with the repair on stderr — the harness feeds it straight
back to the model, which corrects and retries. A human in vim never
meets this; an agent meets it exactly when it helps. Outside a montology
workspace the guard allows instantly: it must never break someone's
editor hooks in an uninitialized repo.

Config, montology.toml::

    [guard]
    names  = "block"   # block | warn | off   (retired words always block)
    design = "block"   # block | warn | off   (only fires when tokens exist)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from montology_core import find_root

from .styles import HEX_RE, color_distance, norm_color
from .surface import DECL_QUERIES, LANG_BY_EXT, _scan_config


def _proposed_text(payload: dict) -> tuple[str, str]:
    """(file_path, the text being written) from a hook payload. Covers
    Write (content), Edit (new_string), MultiEdit (edits[].new_string)."""
    tool_input = payload.get("tool_input", {})
    path = tool_input.get("file_path", "")
    if "content" in tool_input:
        return path, tool_input["content"]
    if "new_string" in tool_input:
        return path, tool_input["new_string"]
    if "edits" in tool_input:
        return path, "\n".join(e.get("new_string", "") for e in tool_input["edits"])
    return path, ""


def _declared_names(path: str, text: str) -> list[tuple[str, str]]:
    """(kind, name) declared in the proposed text — one file, one parse."""
    suffix = Path(path).suffix
    lang = LANG_BY_EXT.get(suffix)
    query_src = DECL_QUERIES.get(lang) if lang else None
    if not query_src:
        return []
    from tree_sitter_language_pack import get_language, get_parser

    language = get_language(lang)
    try:
        from tree_sitter import Query, QueryCursor

        q = QueryCursor(Query(language, query_src))
    except ImportError:
        q = language.query(query_src)
    tree = get_parser(lang).parse(text.encode())
    out = []
    for cap_name, nodes in q.captures(tree.root_node).items():
        if cap_name.startswith("name."):
            for node in nodes:
                out.append((cap_name.split(".", 1)[1], node.text.decode(errors="replace")))
    return out


def check_text(root: Path, path: str, text: str) -> tuple[list[str], list[str]]:
    """(blocking, advisory) findings for one proposed write."""
    from montology_ontology import db as odb

    cfg_scan = _scan_config(root)
    import tomllib

    toml = root / ".monty" / "montology.toml"
    cfg_guard = {}
    if toml.exists():
        try:
            cfg_guard = tomllib.loads(toml.read_text()).get("guard", {})
        except tomllib.TOMLDecodeError:
            pass
    names_mode = cfg_guard.get("names", "block")
    design_mode = cfg_guard.get("design", "block")

    db = root / ".monty" / "ontology.db"
    if not db.exists():
        return [], []
    conn = odb.connect(db, readonly=True)
    blocking: list[str] = []
    advisory: list[str] = []

    # ── names ──────────────────────────────────────────────────────────
    if names_mode != "off":
        retired = {r["was"].lower(): dict(r) for r in conn.execute("SELECT * FROM renamed")}
        enforced_kinds = set(cfg_scan.get("enforced_kinds", ["core", "inner"]))
        allow = {a.lower() for a in cfg_scan.get("allow", [])}
        enforce_collisions = cfg_scan.get("collisions", "advisory") == "enforce"
        words = {w["name"].lower(): dict(w) for w in conn.execute(
            "SELECT name, kind, definition FROM word") if w["kind"] in enforced_kinds}
        for kind, name in _declared_names(path, text):
            low = name.lower()
            if low in retired:
                r = retired[low]
                blocking.append(
                    f"{kind} {name!r}: the word {r['was']!r} was RENAMED to "
                    f"{r['now']!r} ({r['why'] or 'ruling on record'}). Name it "
                    f"{r['now']!r} — the old name stays retired.")
            elif low in words and low not in allow:
                w = words[low]
                msg = (f"{kind} {name!r} collides with the word {w['name']!r} — "
                       f"\"{w['definition'][:80]}\". Pick a different name, or the "
                       f"human records an exception in montology.toml [scan] allow.")
                (blocking if (enforce_collisions and names_mode == "block")
                 else advisory).append(msg)

    # ── design ─────────────────────────────────────────────────────────
    if design_mode != "off":
        tokens = {t["name"]: norm_color(t["value"]) for t in conn.execute(
            "SELECT name, value FROM token WHERE category='color'")}
        tokens = {k: v for k, v in tokens.items() if v}
        if tokens:
            values = set(tokens.values())
            seen: set[str] = set()
            for m in HEX_RE.finditer(text):
                c = norm_color(m.group(0))
                if not c or c in values or c in seen:
                    continue
                seen.add(c)
                nearest = min(tokens.items(), key=lambda kv: color_distance(c, kv[1]))
                dist = color_distance(c, nearest[1])
                if dist <= 90:
                    fix = (f"use the token {nearest[0]!r} ({nearest[1]}, Δ{dist}) — "
                           f"var(--{nearest[0]}) or the matching utility")
                else:
                    fix = (f"no token is close (nearest: {nearest[0]} Δ{dist}) — "
                           "use an existing token, or the human names this value first: "
                           f"monty design token <name> color \"{c}\"")
                msg = f"rogue color {c}: {fix}"
                (blocking if design_mode == "block" else advisory).append(msg)
    return blocking, advisory


def run_hook(stdin_text: str, err=None, out=None) -> int:
    """The hook entry: JSON in, verdict out. Exit 0 allow, exit 2 deny
    (stderr carries the repair — the harness feeds it to the model).
    `err`/`out` are line emitters: the CLI passes styled ones (rich strips
    styles when piped, so the model always receives plain text)."""
    err = err or (lambda s: print(s, file=sys.stderr))
    out = out or print
    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError:
        return 0  # a malformed payload must never block someone's editor
    path, text = _proposed_text(payload)
    if not text:
        return 0
    root = find_root(Path(path).parent if path else None)
    if root is None:
        return 0  # not a montology workspace — invisible
    try:
        blocking, advisory = check_text(root, path, text)
    except Exception:  # noqa: BLE001 — the guard fails OPEN, always
        return 0
    _log(root, path, "deny" if blocking else ("advisory" if advisory else "allow"),
         blocking + advisory)
    if blocking:
        err("montology guard: this edit introduces vocabulary drift —")
        for b in blocking:
            err(f"  • {b}")
        for a in advisory:
            err(f"  (advisory) {a}")
        err("Fix the flagged names/values and retry the edit.")
        return 2
    for a in advisory:
        out(f"montology guard (advisory): {a}")
    return 0


def _log(root: Path, path: str, verdict: str, findings: list[str]) -> None:
    """Every hook decision, recorded — the compliance dataset accumulates
    from ordinary usage. Logging must never block an edit: fail open."""
    try:
        import sqlite3
        from datetime import UTC, datetime

        db = root / ".monty" / "ontology.db"
        conn = sqlite3.connect(db, timeout=0.5)
        conn.execute("CREATE TABLE IF NOT EXISTS guard_runs (ran_at TEXT NOT NULL, "
                     "path TEXT NOT NULL, verdict TEXT NOT NULL, findings TEXT)")
        conn.execute("INSERT INTO guard_runs VALUES (?,?,?,?)",
                     (datetime.now(UTC).isoformat(), path, verdict,
                      "; ".join(findings)[:2000]))
        conn.commit()
        conn.close()
    except Exception:  # noqa: BLE001
        pass


def stats(root: Path | None = None) -> list[str]:
    """Repair-following, measured: a deny followed by an allow on the same
    path within 30 minutes is a COMPLIED denial — the agent read the
    repair and applied it."""
    import sqlite3
    from datetime import datetime

    from montology_core import workspace_root

    root = root or workspace_root()
    db = root / ".monty" / "ontology.db"
    if not db.exists():
        return ["no guard history — the log begins with the first hooked edit."]
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT ran_at, path, verdict FROM guard_runs "
                            "ORDER BY ran_at").fetchall()
    except sqlite3.OperationalError:
        return ["no guard history — the log begins with the first hooked edit."]
    if not rows:
        return ["no guard history — the log begins with the first hooked edit."]
    denies = [(t, p) for t, p, v in rows if v == "deny"]
    allows = [(t, p) for t, p, v in rows if v == "allow"]
    complied = 0
    for dt, dp in denies:
        d = datetime.fromisoformat(dt)
        if any(ap == dp and 0 < (datetime.fromisoformat(at) - d).total_seconds() < 1800
               for at, ap in allows):
            complied += 1
    total = len(rows)
    lines = [f"guard: {total} hooked edit(s) — {len(allows)} allowed, "
             f"{len(denies)} denied, {sum(1 for *_, v in rows if v == 'advisory')} advisory"]
    if denies:
        rate = complied / len(denies)
        lines.append(f"repair-following: {complied}/{len(denies)} denials were followed "
                     f"by a clean edit to the same file within 30 min ({rate:.0%}) — "
                     "the compliance measurement, accumulating from ordinary use")
    return lines
