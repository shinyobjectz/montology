"""Deprecated terms, scoped: what the ledger says to stop saying, still said.

THE RULE THIS MODULE EXISTS TO OBEY: **a finding that cannot be scoped
cannot gate.** Counted across a whole tree, `context` appears thousands of
times and the report becomes something you stop reading — at which point the
ruling it was enforcing may as well not exist. So a route earns enforcement
only by saying WHERE it applies; an unscopable one is reported as advisory,
forever, and says why.

A register is a place in the repo, named in `.monty/montology.toml`:

    [registers]
    surface = ["ui/**"]
    code    = ["harness/**", "nexus/**"]
    prose   = ["**/*.md"]

`workspace` is a correct word in `code` and a wrong one in `surface`; a
single tree-wide search can express neither.
"""

from __future__ import annotations

import re
import tomllib
from fnmatch import fnmatch
from pathlib import Path

from montology_core import workspace_root
from montology_ontology import routes, words

from .surface import EXCLUDE_DIRS, _scan_config

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".ex", ".exs",
            ".rs", ".go", ".rb", ".java", ".kt", ".swift", ".c", ".h", ".cpp",
            ".cs", ".php", ".lua", ".sql"}
PROSE_EXT = {".md", ".mdx", ".txt", ".rst"}
MAX_BYTES = 1_000_000

# What a register means when the repo has not said. `code` and `prose` are
# decidable from a file's kind alone; `surface` never is — it is a claim
# about which part of a product a person looks at, which only the repo knows.
_DEFAULT_REGISTERS = {"code": ["*"], "prose": ["*"], "all": ["*"]}


def register_config(root: Path | None = None) -> dict[str, list[str]]:
    root = root or workspace_root()
    f = root / ".monty" / "montology.toml"
    if not f.exists():
        return {}
    try:
        cfg = tomllib.loads(f.read_text()).get("registers", {})
    except tomllib.TOMLDecodeError:
        return {}
    return {k: list(v) for k, v in cfg.items() if isinstance(v, list)}


def _in_register(rel: str, suffix: str, register: str, cfg: dict) -> bool:
    globs = cfg.get(register)
    if globs is None:
        if register == "surface":
            return False          # undeclared: NOTHING is the surface
        globs = _DEFAULT_REGISTERS.get(register, ["*"])
    if not any(fnmatch(rel, g) or fnmatch(rel, g.rstrip("/*") + "/*") for g in globs):
        return False
    if register == "code":
        return suffix in CODE_EXT
    if register == "prose":
        return suffix in PROSE_EXT
    return suffix in CODE_EXT or suffix in PROSE_EXT


def scopable(route: dict, cfg: dict) -> bool:
    """A route can gate only if it names a place. `all` with no scope means
    'everywhere', which is precisely the finding that drowns."""
    if route.get("scope"):
        return True
    return route["register"] in cfg and route["register"] != "all"


def _files(root: Path) -> list[tuple[Path, str]]:
    """Every readable file, honouring [scan] include — a repo whose prose
    lives somewhere hidden (`.tickets/`) says so once, and every instrument
    that walks the tree picks it up."""
    cfg = _scan_config(root)
    exclude = EXCLUDE_DIRS | set(cfg.get("exclude", []))
    out: list[tuple[Path, str]] = []
    stack = [root] + [root / inc for inc in cfg.get("include", [])
                      if (root / inc).is_dir()]
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.name in exclude or e.name.startswith("."):
                continue
            if e.is_dir():
                stack.append(e)
            elif e.suffix in CODE_EXT or e.suffix in PROSE_EXT:
                out.append((e, str(e.relative_to(root))))
    return out


def _pattern(term: str) -> re.Pattern:
    """Word-boundary, case-insensitive, and tolerant of how a multi-word term
    is spelled in code: `adapter function` matches adapter_function too."""
    body = re.escape(term).replace(r"\ ", r"[\s_-]")
    return re.compile(rf"(?<![A-Za-z0-9_]){body}(?![A-Za-z0-9_])", re.I)


def stale(root: Path | None = None, *, limit: int = 12) -> dict:
    """Every route, measured where it applies.

    Returns {"findings": [...], "advisory": [...], "unscopable": [...]}.
    """
    root = root or workspace_root()
    cfg = register_config(root)
    rs = routes()
    if not rs:
        return {"findings": [], "advisory": [], "unscopable": [], "routes": 0,
                "registers": cfg}

    known = {w["name"].lower() for w in words()}
    pats = {r["from_term"]: _pattern(r["from_term"]) for r in rs}
    hits: dict[tuple, list[str]] = {}

    for f, rel in _files(root):
        try:
            if f.stat().st_size > MAX_BYTES:
                continue
            text = f.read_text(errors="replace")
        except OSError:
            continue
        for r in rs:
            key = (r["from_term"], r["to_word"], r["register"])
            if r.get("scope") and not fnmatch(rel, r["scope"]):
                continue
            if not r.get("scope") and not _in_register(rel, f.suffix, r["register"], cfg):
                continue
            found = pats[r["from_term"]].findall(text)
            if found:
                hits.setdefault(key, []).append(f"{rel} ({len(found)})")

    findings, advisory, unscopable = [], [], []
    for r in rs:
        key = (r["from_term"], r["to_word"], r["register"])
        where = sorted(hits.get(key, []), key=lambda s: -int(s.rsplit("(", 1)[1][:-1]))
        can_gate = scopable(r, cfg)
        row = {**r, "files": where, "count": len(where),
               "orphan": r["to_word"].lower() not in known,
               "shown": where[:limit], "more": max(0, len(where) - limit)}
        if not can_gate:
            unscopable.append(row)
        elif where:
            findings.append(row)
        else:
            advisory.append(row)
    findings.sort(key=lambda r: -r["count"])
    return {"findings": findings, "advisory": advisory, "unscopable": unscopable,
            "routes": len(rs), "registers": cfg}


def render(r: dict) -> list[str]:
    if not r["routes"]:
        return ["no routes yet — `monty onto route --drafts` reads what your "
                "existing rulings already imply."]
    out: list[str] = []
    for row in r["findings"]:
        scope = row["scope"] or f"[registers] {row['register']}"
        out.append(f"stale {row['from_term']!r} → say {row['to_word']!r} "
                   f"— {row['count']} file(s) in {scope}")
        out += [f"    {w}" for w in row["shown"]]
        if row["more"]:
            out.append(f"    … and {row['more']} more file(s)")
    if r["unscopable"]:
        out.append("")
        out.append(f"{len(r['unscopable'])} route(s) cannot be enforced — no register, "
                   "no scope. A finding that cannot be scoped cannot gate:")
        for row in r["unscopable"]:
            out.append(f"    {row['from_term']!r} → {row['to_word']!r}. Repair: "
                       f"`monty onto route {row['from_term']!r} --to {row['to_word']!r} "
                       f"--in code|surface|prose` , or --scope 'path/glob/**'.")
    clean = len(r["advisory"])
    out.append("")
    out.append(f"ok — {r['routes']} route(s): {len(r['findings'])} with live uses, "
               f"{clean} clean, {len(r['unscopable'])} unscopable")
    return out
