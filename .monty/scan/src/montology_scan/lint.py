"""Where the ontology bites the codebase. Every FAIL carries its repair.

Four laws, in the order they earn their keep:

  * **collision** — a declaration whose name is an enforced word. What that
    costs depends on what the word NAMES, which is why `pos` exists: a verb
    doing ordinary work below the surface is not a second meaning, while a
    noun answering for a second thing is the failure a vocabulary exists to
    prevent. A collision judged and kept is an `exception` — recorded in
    the database, with its reason and the paths it holds in.
  * **divergence** — one value-typed word declared as more than one value.
    This is the law an exception CANNOT silence, and the two are different
    findings on purpose: an exception says a symbol may share the name; it
    never says the name may mean two things.
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
from fnmatch import fnmatch
from pathlib import Path

from montology_core import workspace_root
from montology_ontology import TREE_WIDE, exceptions, words

from .surface import declarations, type_declarations

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


def _suggested_scope(file: str) -> str:
    """The glob to offer with an exception: the directory the collision is
    in, not the file. `open` is fine BELOW the surface, and a scope of one
    file cannot say that — while tree-wide says nothing at all."""
    parent = Path(file).parent
    return f"{parent}/**" if str(parent) not in (".", "") else TREE_WIDE


def _repair(w: dict, d: dict) -> str:
    """The four cases, as the repair. The old text prescribed a rename for
    all of them, which is wrong three times out of four and is how an
    advisory list becomes something nobody reads."""
    name, kind, pos = w["name"], d["kind"], w.get("pos")
    keep = f'monty onto except {name} --where "{_suggested_scope(d["file"])}" --why "…"'
    if pos == "verb":
        return (f"{name!r} is a verb. If this {kind} does the work the word names — at "
                f"the surface it IS the operation, below it English simply has one word "
                f"for the job — keep it and record why: {keep}. If it names some other "
                f"action, rename it.")
    if pos == "noun":
        return (f"{name!r} is a noun, and a noun names a thing: two things with one name "
                f"is the failure the vocabulary exists to prevent. If this {kind} denotes "
                f"exactly what the word denotes, keep it and say so: {keep}. If it denotes "
                f"a second thing, rename it — that one IS the defect.")
    if pos == "value":
        return (f"{name!r} is a value type: the same value wears the same name everywhere. "
                f"Could you pass this {kind}'s value where the word's is expected? If yes, "
                f"one name is right — record it: {keep}. If no, two things are wearing one "
                f"noun and renaming is the only repair.")
    return (f"{name!r} has no part of speech, so this collision cannot be judged — a verb "
            f"below the surface is ordinary, a noun answering for a second thing is a "
            f"defect. Say which it is (monty onto amend {name} --pos verb|noun|value), "
            f"then rename the {kind} or except it.")


def divergence(root: Path | None = None) -> list[str]:
    """One word, two declared values — the law no exception can silence.

    It fires only on words that CLAIM to name a thing (`pos` noun or value),
    because without that claim there is nothing to violate: two modules
    declaring their own `option` type are not drift, they are two modules.
    A value type FAILS — interchangeability is the whole of what the word
    promises. A noun WARNS: two declarations may be two renderings of one
    thing (a wire form and a struct), and only a human can say.
    """
    root = root or workspace_root()
    denoting = {w["name"].lower(): w for w in words()
                if (w.get("pos") or "") in ("noun", "value")}
    if not denoting:
        return []
    seen: dict[str, dict[str, list[dict]]] = {}
    for t in type_declarations(root):
        low = t["name"].lower()
        if low in denoting:
            seen.setdefault(low, {}).setdefault(t["value"], []).append(t)

    out: list[str] = []
    for low, shapes in sorted(seen.items()):
        if len(shapes) < 2:
            continue
        w = denoting[low]
        tag = "FAIL" if w["pos"] == "value" else "warn"
        sites = "; ".join(
            f"{rows[0]['file']}:{rows[0]['line']} {value}"
            for value, rows in shapes.items())
        out.append(
            f"{tag} word {w['name']!r} is a {w['pos']} and the code declares it as "
            f"{len(shapes)} different values — {sites}. Could you pass one where the "
            f"other is expected? If not, two things are wearing one noun. Repair: rename "
            f"one of them, or amend the word if the definition is what is wrong. No "
            f"exception silences this: an exception says a SYMBOL may share the name, "
            f"never that the NAME may mean two values.")
    return out


def legacy_allow(root: Path | None = None) -> list[str]:
    """`[scan] allow` in montology.toml: the reasonless list this replaces.
    Still honoured — an upgrade that fails a build nobody changed is not an
    upgrade — and still reported, because the whole complaint against it is
    that it is invisible."""
    root = root or workspace_root()
    return [str(a) for a in _config(root).get("scan", {}).get("allow", [])]


def except_drafts(root: Path | None = None) -> list[dict]:
    """What `[scan] allow` would become, one row per entry, so the migration
    is a review rather than a rewrite. The `why` is deliberately not
    invented: it is the thing the old list never had."""
    root = root or workspace_root()
    have = {e["word"].lower() for e in exceptions()}
    known = {w["name"].lower(): w for w in words()}
    out = []
    for name in legacy_allow(root):
        low = name.lower()
        if low in have:
            continue
        w = known.get(low)
        out.append({"word": w["name"] if w else name,
                    "pos": (w or {}).get("pos"),
                    "is_word": w is not None})
    return out


def lint(root: Path | None = None) -> list[str]:
    """Deterministic, model-free, CI-shaped: FAIL lines then a verdict."""
    root = root or workspace_root()
    cfg = _config(root).get("scan", {})
    enforced_kinds = set(cfg.get("enforced_kinds", ["core", "inner"]))
    allow = {a.lower() for a in cfg.get("allow", [])}
    # ADVISORY BY DEFAULT. "No declaration named after a word" is a strong
    # culture (it is ours) — but in most repos `class Journal` implementing
    # the journal concept is ordinary, and a first-run false-positive storm
    # is an uninstall. Enforce is the opt-in: [scan] collisions = "enforce".
    collisions_mode = cfg.get("collisions", "advisory")
    ctag = "FAIL" if collisions_mode == "enforce" else "warn"

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
    granted = exceptions()
    covered: dict[tuple[str, str], int] = {}
    surface = declarations(root)
    for d in surface["decls"]:
        low = d["name"].lower()
        if low not in enforced:
            continue
        hit = next((e for e in granted if e["word"].lower() == low
                    and (e["scope"] == TREE_WIDE or fnmatch(d["file"], e["scope"]))), None)
        if hit:
            covered[(hit["word"], hit["scope"])] = covered.get((hit["word"], hit["scope"]), 0) + 1
            continue
        if low in allow:
            continue
        w = enforced[low]
        pos = f", {w['pos']}" if w.get("pos") else ""
        hint = ("" if collisions_mode == "enforce"
                else " (advisory — promote with [scan] collisions = \"enforce\")")
        report.append(
            f"{ctag} {d['file']}:{d['line']}: {d['kind']} {d['name']!r} collides with "
            f"the word {w['name']!r} ({w['kind']}{pos}) — \"{w['definition'][:80]}\". "
            f"Repair: {_repair(w, d)}" + hint
        )

    # Every exception, SHOWN. One nobody ever sees again is how a stale one
    # survives for years — the same reason the surface gate prints its own.
    for e in granted:
        n = covered.get((e["word"], e["scope"]), 0)
        where = "tree-wide" if e["scope"] == TREE_WIDE else e["scope"]
        if n:
            report.append(f"note except {e['word']!r} ({e['judged'] or 'unjudged'}) covers "
                          f"{n} declaration(s) in {where} — {e['why']}")
        else:
            report.append(f"note except {e['word']!r} covers nothing in {where} — the "
                          f"exception may be stale. Repair: monty onto except "
                          f"{e['word']} --drop, or re-scope it.")
    if allow:
        report.append(
            f"note: {len(allow)} exception(s) still live in montology.toml [scan] allow — "
            "unledgered, reasonless, and unjudged (the four cases turn on a word's part "
            "of speech, which a list of strings cannot carry). Repair: monty onto except "
            "--drafts")

    # divergence: the law an exception cannot silence
    report.extend(divergence(root))

    # phantoms: the other direction. A collision is the vocabulary and the
    # code meaning different things by one name; a phantom a word bears on
    # is the vocabulary pointing at something the code no longer touches.
    try:
        from .surf import gate as surface_gate

        report.extend(surface_gate(root))
    except Exception as exc:  # noqa: BLE001 — a probe must not break the gate
        report.append(f"note surface: not measured ({type(exc).__name__}: {exc})")

    # routes: pure-table findings, so no false positive is possible — a
    # route pointing at a word that does not exist is wrong by inspection.
    # The scoped term SWEEP stays out of the gate deliberately (see `stale`):
    # it is advisory until a repo has scoped its routes.
    try:
        from montology_ontology import render_routes, route_analyse

        report.extend(x for x in render_routes(route_analyse())
                      if x.startswith(("FAIL", "warn")))
    except Exception as exc:  # noqa: BLE001
        report.append(f"note route: not analysed ({type(exc).__name__}: {exc})")

    failed = sum(1 for r in report if r.startswith("FAIL"))
    warned = sum(1 for r in report if r.startswith("warn"))
    for lang, n in surface["skipped_langs"].items():
        report.append(f"note: {n} {lang} file(s) skipped — no declaration query yet")
    report.append(
        ("FAIL" if failed else "ok")
        + f" — {len(surface['decls'])} declarations in {surface['files']} files, "
        f"{len(vocab)} words, {failed} failure(s)"
        + (f", {warned} advisory collision(s)" if warned else "")
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
