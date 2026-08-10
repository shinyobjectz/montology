"""Where the ontology bites the codebase. Every FAIL carries its repair.

Three laws, in the order they earn their keep:

  * **collision** — a declaration whose name is an enforced word. The
    vocabulary says the word means one thing; a class by that name now
    means another. Rename the symbol, or re-rule the word (an `allow`
    entry in montology.toml records the exception AS A DECISION).
  * **code-resolution** — every dotted code prefix resolves to a word, so
    the namespace stays a tree and a tag like `har.cell` can never point
    at nothing.
  * **definition** — a word without a definition is a name squatting on
    meaning.

`candidates` is the other direction — BUILD the ontology from the code:
recurring declared names with no word are the vocabulary the codebase is
asking for.
"""

from __future__ import annotations

import tomllib
from collections import Counter
from pathlib import Path

from montology_core import workspace_root
from montology_ontology import words

from .surface import declarations

# generic programming names never make good vocabulary candidates
_NOISE = {
    "main", "init", "new", "get", "set", "run", "test", "setup", "update",
    "create", "delete", "add", "remove", "handle", "process", "make", "build",
    "render", "parse", "load", "save", "read", "write", "index", "app",
    "config", "client", "server", "helper", "util", "utils", "data", "value",
    "item", "list", "name", "type", "error", "result", "response", "request",
    "check", "start", "stop", "close", "open", "call", "next", "state",
    # measured leaking through the 2026-08-10 stress battery (8 real repos)
    "constructor", "initialize", "window", "document", "string", "number",
    "boolean", "tests", "default", "props", "clear", "params", "options",
    "module", "view", "post", "json", "path", "connect", "join", "bind",
}


def _config(root: Path) -> dict:
    f = root / ".monty" / "montology.toml"
    if not f.exists():
        return {}
    try:
        return tomllib.loads(f.read_text())
    except tomllib.TOMLDecodeError:
        return {}


def lint(root: Path | None = None) -> list[str]:
    """Deterministic, model-free, CI-shaped: FAIL lines then a verdict."""
    root = root or workspace_root()
    cfg = _config(root).get("scan", {})
    enforced_kinds = set(cfg.get("enforced_kinds", ["core", "inner"]))
    allow = {a.lower() for a in cfg.get("allow", [])}

    vocab = words()
    report: list[str] = []

    # code-resolution + definition: db-level, no parse needed
    codes = {w["code"] for w in vocab if w["code"]}
    for w in vocab:
        if not w["definition"].strip():
            report.append(f"FAIL word {w['name']!r}: no definition — a name "
                          "squatting on meaning. Repair: monty onto add, or delete it.")
        if w["code"] and "." in w["code"]:
            prefix = w["code"].rsplit(".", 1)[0]
            if prefix not in codes:
                report.append(f"FAIL code {w['code']} ({w['name']}): prefix "
                              f"{prefix!r} resolves to no word. Repair: add the "
                              "owning word with that code, or re-code this one.")

    # collision: the scan against enforced words
    enforced = {w["name"].lower(): w for w in vocab if w["kind"] in enforced_kinds}
    surface = declarations(root)
    for d in surface["decls"]:
        low = d["name"].lower()
        if low in enforced and low not in allow:
            w = enforced[low]
            report.append(
                f"FAIL {d['file']}:{d['line']}: {d['kind']} {d['name']!r} collides with "
                f"the word {w['name']!r} ({w['kind']}) — \"{w['definition'][:80]}\". "
                f"Repair: rename the {d['kind']}, or record the exception in "
                f"montology.toml [scan] allow."
            )

    failed = sum(1 for r in report if r.startswith("FAIL"))
    for lang, n in surface["skipped_langs"].items():
        report.append(f"note: {n} {lang} file(s) skipped — no declaration query yet")
    report.append(
        ("FAIL" if failed else "ok")
        + f" — {len(surface['decls'])} declarations in {surface['files']} files, "
        f"{len(vocab)} words, {failed} failure(s)"
    )
    return report


def candidates(root: Path | None = None, top: int = 15) -> list[dict]:
    """Vocabulary the codebase is asking for: recurring declared names with
    no word. The agent's raw material for `monty onto add`."""
    root = root or workspace_root()
    have = {w["name"].lower() for w in words()}
    counts: Counter[str] = Counter()
    kinds: dict[str, str] = {}
    for d in declarations(root)["decls"]:
        low = d["name"].lower().lstrip("_")
        if low in have or low in _NOISE or len(low) < 4 or not low.isalpha():
            continue
        counts[low] += 1
        kinds.setdefault(low, d["kind"])
    return [{"name": name, "count": n, "kind": kinds[name]}
            for name, n in counts.most_common(top)]
