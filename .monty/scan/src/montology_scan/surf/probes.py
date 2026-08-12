"""The probe seam: how one ecosystem tells montology what it stands on.

Montology must not become a dependency analyzer per language. It owns the
schema, the join to the vocabulary, and the report; each ecosystem
contributes a **probe** that emits the same two row shapes and nothing else:

    surfaces(root) -> [{id, owner, kind, version, exposes, declared_at, probe}] | None
    seams(root, surfaces) -> [{from_id, to_id, kind, direction, at, probe}]

`None` from ``surfaces()`` means "nothing of mine to read in this repo" — a
probe that cannot run SAYS so, because silence reads as "covered" when it
was not. That is `surface.py`'s rule for missing grammars, carried over.

Two things follow from the shape, and both are the point:

  * **Our own code is just a probe.** A package we build and a package we
    buy are both surfaces; `kind` is the only difference. That is what
    makes a seam between our code and a dependency expressible at all —
    and what makes the INTERNAL dependency graph fall out for free.
  * **Manifest-less things are first class.** A hosted service has no
    lockfile and still has a surface and seams; a probe that reads a deploy
    config emits the same rows a package probe does.

WHAT IS A SEAM HERE: an import that resolves to a surface we found. Not a
manifest entry — a manifest is a claim, and the whole point of this feature
is that a claim is not a fact. A dependency declared and never imported is
exactly the phantom the gate exists to produce.
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from ..surface import EXCLUDE_DIRS, MAX_BYTES, _scan_config

__all__ = ["PROBES", "Probe", "first_party_id", "mine", "sid"]


def mine(surfaces: list[dict], name: str) -> list[dict]:
    """The surfaces this probe may resolve seams against.

    One component can be claimed by two probes and is merged into ONE
    record before seams are read; such a record answers to every probe that
    found it, so filtering on the singular `probe` field alone would hide
    it from all but the first."""
    return [s for s in surfaces if name in (s.get("probes") or [s["probe"]])]


# ── identity ─────────────────────────────────────────────────────────────

def sid(probe: str, owner: str) -> str:
    """A surface's stable id. Stable across runs is the whole requirement:
    bearings point at these, so a churning id would drop the join."""
    return f"{probe}:{owner}"


def first_party_id(owner: str) -> str:
    """Ours. Deliberately NOT namespaced by probe — a component we build is
    the repo's whichever language it happens to be written in, and that is
    what lets one word bear on it regardless of ecosystem."""
    return sid("repo", owner)


def _norm(name: str) -> str:
    """PEP 503-ish: the same distribution written three ways is one owner."""
    return re.sub(r"[-_.]+", "-", name).strip().lower()


# ── walking ──────────────────────────────────────────────────────────────

def _walk(root: Path, match: Callable[[Path], bool]) -> list[Path]:
    """Files under `root` matching `match`, honouring [scan] include/exclude.

    Same traversal rule as `surface.py`: hidden directories are skipped
    unless [scan] include names them, which is how a repo whose own source
    lives under `.monty` still gets measured.
    """
    cfg = _scan_config(root)
    exclude = EXCLUDE_DIRS | set(cfg.get("exclude", []))
    out: list[Path] = []
    seen: set[Path] = set()
    stack = [root] + [root / inc for inc in cfg.get("include", [])
                      if (root / inc).is_dir()]
    while stack:
        d = stack.pop()
        if d in seen:
            continue
        seen.add(d)
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.name in exclude or e.name.startswith("."):
                continue
            if e.is_dir():
                stack.append(e)
            elif match(e):
                out.append(e)
    return out


def _under(f: Path, d: Path) -> bool:
    return f == d or d in f.parents


def _owner_index(surfaces: list[dict], root: Path) -> list[tuple[Path, str]]:
    """First-party surfaces by the directory their manifest sits in, deepest
    first — so a file inside a workspace member belongs to the member, not
    to the root manifest that also encloses it."""
    idx = [(root / Path(s["declared_at"]).parent, s["id"])
           for s in surfaces
           if s["kind"] == "first-party" and s.get("declared_at")]
    return sorted(idx, key=lambda t: len(str(t[0])), reverse=True)


class Probe:
    """Marker base. A probe is two functions and a name; subclassing only
    documents that."""

    name: str

    def surfaces(self, root: Path) -> list[dict] | None:  # pragma: no cover
        raise NotImplementedError

    def seams(self, root: Path, surfaces: list[dict]) -> list[dict]:  # pragma: no cover
        raise NotImplementedError


# ── python ───────────────────────────────────────────────────────────────

_REQ = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(.*)$")


def _req(spec: str) -> tuple[str | None, str | None]:
    """PEP 508 far enough: name, and whatever constrains it."""
    head = spec.split(";", 1)[0].strip()
    m = _REQ.match(head)
    if not m:
        return None, None
    return m.group(1), (m.group(2).strip() or None)


def _requirements(data: dict) -> list[str]:
    proj = data.get("project") or {}
    out = list(proj.get("dependencies") or [])
    for extra in (proj.get("optional-dependencies") or {}).values():
        out += list(extra or [])
    for group in (data.get("dependency-groups") or {}).values():
        out += [g for g in (group or []) if isinstance(g, str)]
    return out


def _provides(d: Path, name: str, data: dict) -> list[str]:
    """The import names a first-party package puts on the table.

    Read from the build config where it is declared, guessed from layout
    where it is not — the guess is the common case and it is cheap to
    correct, because a wrong guess shows up as a phantom, loudly."""
    mods: list[str] = []
    wheel = (((data.get("tool") or {}).get("hatch") or {})
             .get("build", {}).get("targets", {}).get("wheel", {}))
    for p in wheel.get("packages") or []:
        mods.append(Path(str(p)).name)
    guess = _norm(name).replace("-", "_")
    for cand in (d / "src" / guess, d / guess):
        if (cand / "__init__.py").exists():
            mods.append(guess)
    src = d / "src"
    if src.is_dir():
        try:
            for c in src.iterdir():
                if c.is_dir() and (c / "__init__.py").exists():
                    mods.append(c.name)
        except OSError:
            pass
    return sorted(set(mods)) or [guess]


@lru_cache(maxsize=1)
def _dist_modules() -> dict[str, list[str]]:
    """distribution -> the modules it actually installs, from the live env.

    `pyyaml` imports as `yaml`; no amount of string mangling gets there.
    Absent env information we fall back to the mangling, and a wrong guess
    surfaces as a phantom rather than as silence."""
    try:
        from importlib.metadata import packages_distributions
    except ImportError:  # pragma: no cover
        return {}
    try:
        mapping = packages_distributions()
    except Exception:  # noqa: BLE001 — a broken env is a degraded probe, not a crash
        return {}
    out: dict[str, list[str]] = {}
    for mod, dists in mapping.items():
        for d in dists:
            out.setdefault(_norm(d), []).append(mod)
    return out


class PythonProbe(Probe):
    name = "python"

    def surfaces(self, root: Path) -> list[dict] | None:
        manifests = _walk(root, lambda p: p.name == "pyproject.toml")
        if not manifests:
            return None

        parsed: list[tuple[Path, dict]] = []
        for m in manifests:
            try:
                parsed.append((m, tomllib.loads(m.read_text())))
            except (OSError, tomllib.TOMLDecodeError):
                continue

        # Pass one: ours. Must complete before deps are read, or a workspace
        # member would be recorded as a package we buy.
        found: dict[str, dict] = {}
        ours: dict[str, str] = {}
        for m, data in parsed:
            proj = data.get("project") or {}
            name = proj.get("name")
            if not name:
                continue
            i = first_party_id(_norm(name))
            ours[_norm(name)] = i
            rec = found.setdefault(i, {
                "id": i, "owner": name, "kind": "first-party",
                "version": proj.get("version"), "exposes": [],
                "declared_at": str(m.relative_to(root)), "probe": self.name,
            })
            rec["exposes"] = sorted(set(rec["exposes"]) | set(_provides(m.parent, name, data)))

        # Pass two: theirs.
        for m, data in parsed:
            for spec in _requirements(data):
                dep, ver = _req(spec)
                if not dep:
                    continue
                key = _norm(dep)
                if key in ours:
                    continue  # a workspace member is ours, not a purchase
                i = sid(self.name, key)
                if i in found:
                    continue
                found[i] = {
                    "id": i, "owner": dep, "kind": "package", "version": ver,
                    "exposes": _dist_modules().get(key, [key.replace("-", "_")]),
                    "declared_at": str(m.relative_to(root)), "probe": self.name,
                }
        return list(found.values())

    def seams(self, root: Path, surfaces: list[dict]) -> list[dict]:
        ours = mine(surfaces, self.name)
        by_mod: dict[str, str] = {}
        for s in ours:
            for mod in s["exposes"]:
                by_mod.setdefault(mod, s["id"])
        owners = _owner_index(ours, root)
        if not owners:
            return []

        out: list[dict] = []
        for f in _walk(root, lambda p: p.suffix in (".py", ".pyi")):
            frm = next((i for d, i in owners if _under(f, d)), None)
            if frm is None:
                continue
            try:
                if f.stat().st_size > MAX_BYTES:
                    continue
                tree = ast.parse(f.read_bytes())
            except (OSError, SyntaxError, ValueError):
                continue  # one unparseable file is a gap, not a crash
            rel = str(f.relative_to(root))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    tops = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        continue  # relative: inside ONE surface, not between two
                    tops = [(node.module or "").split(".")[0]]
                else:
                    continue
                for top in tops:
                    if not top or top in sys.stdlib_module_names:
                        continue
                    to = by_mod.get(top)
                    if to is None or to == frm:
                        continue
                    out.append({"from_id": frm, "to_id": to, "kind": "import",
                                "direction": "out", "at": f"{rel}:{node.lineno}",
                                "probe": self.name})

        # A tool that is CONFIGURED is used: `[tool.ruff]` in the manifest
        # that declares ruff is the same evidence an import would be, for a
        # thing that is run rather than imported.
        by_owner = {_norm(s["owner"]): s["id"] for s in ours}
        for f in _walk(root, lambda p: p.name == "pyproject.toml"):
            frm = next((i for d, i in owners if _under(f, d)), None)
            if frm is None:
                continue
            try:
                data = tomllib.loads(f.read_text())
            except (OSError, tomllib.TOMLDecodeError):
                continue
            rel = str(f.relative_to(root))
            for section in (data.get("tool") or {}):
                to = by_owner.get(_norm(str(section)))
                if to is None or to == frm:
                    continue
                out.append({"from_id": frm, "to_id": to, "kind": "config",
                            "direction": "out", "at": f"{rel}:tool.{section}",
                            "probe": self.name})
        return out


# ── node ─────────────────────────────────────────────────────────────────

_JS_EXT = {".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
           ".cjs": "javascript", ".ts": "typescript", ".tsx": "tsx",
           ".mts": "typescript", ".cts": "typescript"}

_CSS_EXT = {".css", ".scss", ".sass", ".less", ".pcss", ".postcss"}
_CSS_IMPORT = re.compile(
    r"""@import\s+(?:url\(\s*['"]?([^'")]+)|['"]([^'"]+)['"])""")

_JS_IMPORTS = """
    (import_statement source: (string) @mod)
    (export_statement source: (string) @mod)
    (call_expression
      function: (identifier) @_req
      arguments: (arguments (string) @mod)
      (#eq? @_req "require"))
    (call_expression
      function: (import)
      arguments: (arguments (string) @mod))
"""

_NODE_BUILTIN = {
    "assert", "buffer", "child_process", "cluster", "console", "crypto",
    "dgram", "dns", "events", "fs", "http", "http2", "https", "module", "net",
    "os", "path", "perf_hooks", "process", "punycode", "querystring",
    "readline", "stream", "string_decoder", "timers", "tls", "tty", "url",
    "util", "v8", "vm", "worker_threads", "zlib",
}


def _js_package(spec: str) -> str | None:
    """The package a specifier names. Subpaths collapse to their package —
    `lodash/fp` is a seam to lodash — because the surface is the package."""
    s = spec.strip()
    if not s or s.startswith((".", "/")) or s.startswith("node:"):
        return None
    parts = s.split("/")
    if s.startswith("@"):
        return "/".join(parts[:2]) if len(parts) >= 2 else None
    return parts[0] or None


class NodeProbe(Probe):
    name = "node"

    def surfaces(self, root: Path) -> list[dict] | None:
        manifests = _walk(root, lambda p: p.name == "package.json")
        if not manifests:
            return None

        parsed: list[tuple[Path, dict]] = []
        for m in manifests:
            try:
                data = json.loads(m.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                parsed.append((m, data))

        found: dict[str, dict] = {}
        ours: dict[str, str] = {}
        for m, data in parsed:
            name = data.get("name")
            if not isinstance(name, str) or not name:
                continue
            i = first_party_id(name)
            ours[name] = i
            found.setdefault(i, {
                "id": i, "owner": name, "kind": "first-party",
                "version": data.get("version") if isinstance(data.get("version"), str) else None,
                "exposes": [name], "declared_at": str(m.relative_to(root)),
                "probe": self.name,
            })

        for m, data in parsed:
            for field in ("dependencies", "devDependencies", "peerDependencies",
                          "optionalDependencies"):
                for dep, ver in (data.get(field) or {}).items():
                    if not isinstance(dep, str) or dep in ours:
                        continue
                    i = sid(self.name, dep)
                    if i in found:
                        continue
                    found[i] = {
                        "id": i, "owner": dep, "kind": "package",
                        "version": ver if isinstance(ver, str) else None,
                        "exposes": [dep], "declared_at": str(m.relative_to(root)),
                        "probe": self.name,
                    }
        return list(found.values())

    def seams(self, root: Path, surfaces: list[dict]) -> list[dict]:
        ours = mine(surfaces, self.name)
        by_pkg = {mod: s["id"] for s in ours for mod in s["exposes"]}
        owners = _owner_index(ours, root)
        if not owners:
            return []
        try:
            from tree_sitter_language_pack import get_language, get_parser
        except ImportError:  # pragma: no cover
            return []

        cache: dict[str, tuple] = {}

        def _runner(lang: str):
            if lang not in cache:
                language = get_language(lang)
                try:
                    from tree_sitter import Query, QueryCursor
                    cache[lang] = (get_parser(lang), QueryCursor(Query(language, _JS_IMPORTS)))
                except ImportError:
                    cache[lang] = (get_parser(lang), language.query(_JS_IMPORTS))
            return cache[lang]

        out: list[dict] = []
        met: set[str] = set()          # ids something was found to meet
        builtin_at: set[str] = set()   # first-party ids that use node builtins

        def _emit(frm: str, to: str | None, kind: str, at: str) -> None:
            if to is None or to == frm:
                return
            met.add(to)
            out.append({"from_id": frm, "to_id": to, "kind": kind,
                        "direction": "out", "at": at, "probe": self.name})

        # 1. the import that resolves
        for f in _walk(root, lambda p: p.suffix in _JS_EXT):
            frm = next((i for d, i in owners if _under(f, d)), None)
            if frm is None:
                continue
            try:
                if f.stat().st_size > MAX_BYTES:
                    continue
                parser, q = _runner(_JS_EXT[f.suffix])
                tree = parser.parse(f.read_bytes())
                captures = q.captures(tree.root_node)
            except Exception:  # noqa: BLE001 — one file, or one missing grammar
                continue
            rel = str(f.relative_to(root))
            for node in captures.get("mod", []):
                spec = node.text.decode(errors="replace").strip("\"'`")
                if spec.startswith("node:"):
                    builtin_at.add(frm)
                    continue
                pkg = _js_package(spec)
                if pkg is None:
                    continue
                if pkg in _NODE_BUILTIN:
                    builtin_at.add(frm)
                    continue
                _emit(frm, by_pkg.get(pkg), "import", f"{rel}:{node.start_point[0] + 1}")

        # 2. the stylesheet that imports. `@import "tw-animate-css"` is a
        # seam by any honest reading; calling that package a phantom because
        # the import was not JavaScript is the probe being wrong.
        for f in _walk(root, lambda p: p.suffix in _CSS_EXT):
            frm = next((i for d, i in owners if _under(f, d)), None)
            if frm is None:
                continue
            try:
                if f.stat().st_size > MAX_BYTES:
                    continue
                text = f.read_text(errors="replace")
            except OSError:
                continue
            rel = str(f.relative_to(root))
            for hit in _CSS_IMPORT.finditer(text):
                spec = (hit.group(1) or hit.group(2) or "").strip().lstrip("~")
                pkg = _js_package(spec)
                if pkg is None:
                    continue
                line = text.count("\n", 0, hit.start()) + 1
                _emit(frm, by_pkg.get(pkg), "import", f"{rel}:{line}")

        # 3. the tool a script runs. `oxlint`, `wrangler`, `vite` are
        # invoked, never imported. The token must stand ALONE — a substring
        # match would meet a package by accident, and a false seam hides a
        # phantom, which is the one failure mode worth engineering against.
        for f in _walk(root, lambda p: p.name == "package.json"):
            frm = next((i for d, i in owners if _under(f, d)), None)
            if frm is None:
                continue
            try:
                data = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            scripts = data.get("scripts") if isinstance(data, dict) else None
            if not isinstance(scripts, dict):
                continue
            rel = str(f.relative_to(root))
            invoked: set[str] = set()
            for sname, body in scripts.items():
                if not isinstance(body, str):
                    continue
                for tok in set(re.split(r"[^A-Za-z0-9@/._-]+", body)):
                    if tok:
                        invoked.add(tok)
                        _emit(frm, by_pkg.get(tok), "call", f"{rel}:scripts.{sname}")

            # A package's command is often not its name — `typescript` is run
            # as `tsc`. The mapping is declared by the package itself, so we
            # read it where it is installed rather than carrying a list of
            # vendor knowledge: vendors are not vocabulary, and a hardcoded
            # alias table would rot. Absent node_modules, this rule is simply
            # skipped and whatever it would have met stays a phantom.
            for s in ours:
                if s["kind"] != "package" or s["id"] in met:
                    continue
                installed = f.parent / "node_modules" / s["owner"] / "package.json"
                try:
                    bins = json.loads(installed.read_text()).get("bin")
                except (OSError, json.JSONDecodeError, AttributeError):
                    continue
                names = ([s["owner"].split("/")[-1]] if isinstance(bins, str)
                         else list(bins) if isinstance(bins, dict) else [])
                if invoked.intersection(names):
                    _emit(frm, s["id"], "call", f"{rel}:scripts")

        # 4. `@types/foo` is met when `foo` is met. A typings package is
        # consumed by the compiler and never imported; the thing it types
        # being used IS the evidence that it is used. Runs last, because it
        # reads what every rule above established.
        for s in ours:
            if s["kind"] != "package" or not s["owner"].startswith("@types/"):
                continue
            declared = s.get("declared_at")
            if not declared:
                continue
            frm = next((i for d, i in owners if _under(root / declared, d)), None)
            if frm is None:
                continue
            subject = s["owner"][len("@types/"):]
            if subject == "node":
                hit = frm in builtin_at
            else:
                # @types/foo__bar types the scoped package @foo/bar
                name = "@" + subject.replace("__", "/") if "__" in subject else subject
                hit = by_pkg.get(name) in met
            if hit:
                _emit(frm, s["id"], "config", f"{declared}:@types")
        return out


# ── elixir ───────────────────────────────────────────────────────────────

_MIX_DEP = re.compile(r"\{\s*:([a-z][a-z0-9_]*)\s*,\s*([^}]*)\}")
_MIX_APP = re.compile(r"app:\s*:([a-z][a-z0-9_]*)")
_MIX_VSN = re.compile(r"version:\s*[\"']([^\"']+)")
_MIX_DEPS_BLOCK = re.compile(r"defp?\s+deps\s*do(.*?)\n\s*end", re.S)
_DEP_VERSION = re.compile(r"[\"']([^\"']+)[\"']")


def _camel(atom: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in atom.split("_") if p)


def _beam_modules(dep_dir: Path) -> list[str]:
    """The modules a built dependency actually exposes.

    A compiled Elixir dep names one .beam file per module, so the directory
    listing IS the module list — exact, and free. `:ecto_sql` provides
    `Ecto.Adapters.SQL`, which no amount of camelizing `ecto_sql` reaches;
    guessing there would invent a phantom out of a naming convention.
    """
    ebin = dep_dir / "ebin"
    try:
        mods = sorted(f.stem[len("Elixir."):] for f in ebin.glob("Elixir.*.beam"))
    except OSError:
        return []
    # Keep only ROOTS: a module no other module of this dep is a prefix of.
    roots: list[str] = []
    for m in mods:
        if not any(m.startswith(r + ".") for r in roots):
            roots.append(m)
    return roots


class ElixirProbe(Probe):
    name = "elixir"

    def surfaces(self, root: Path) -> list[dict] | None:
        manifests = _walk(root, lambda p: p.name == "mix.exs")
        if not manifests:
            return None

        found: dict[str, dict] = {}
        for m in manifests:
            try:
                text = m.read_text(errors="replace")
            except OSError:
                continue
            rel = str(m.relative_to(root))
            app = _MIX_APP.search(text)
            if not app:
                continue
            name = app.group(1)
            vsn = _MIX_VSN.search(text)
            i = first_party_id(name)
            found.setdefault(i, {
                "id": i, "owner": name, "kind": "first-party",
                "version": vsn.group(1) if vsn else None,
                "exposes": [_camel(name)], "declared_at": rel, "probe": self.name,
            })

            block = _MIX_DEPS_BLOCK.search(text)
            if not block:
                continue
            # Built deps give exact module names; an unbuilt tree falls back
            # to camelizing, and says as much by simply finding fewer seams.
            builds = sorted((m.parent / "_build").glob("*/lib"))
            for dep, rest in _MIX_DEP.findall(block.group(1)):
                if dep == name:
                    continue
                dep_id = sid(self.name, dep)
                if dep_id in found:
                    continue
                exposes: list[str] = []
                for lib in builds:
                    exposes = _beam_modules(lib / dep)
                    if exposes:
                        break
                ver = _DEP_VERSION.search(rest)
                found[dep_id] = {
                    "id": dep_id, "owner": dep, "kind": "package",
                    "version": ver.group(1) if ver else None,
                    "exposes": exposes or [_camel(dep)],
                    "declared_at": rel, "probe": self.name,
                }
        return list(found.values())

    def seams(self, root: Path, surfaces: list[dict]) -> list[dict]:
        ours = mine(surfaces, self.name)
        by_mod: dict[str, str] = {}
        for s in sorted(ours, key=lambda s: s["kind"] != "first-party"):
            for mod in s["exposes"]:
                by_mod.setdefault(mod, s["id"])
        owners = _owner_index(ours, root)
        if not owners:
            return []
        try:
            from tree_sitter import Query, QueryCursor
            from tree_sitter_language_pack import get_language, get_parser

            language = get_language("elixir")
            parser = get_parser("elixir")
            cursor = QueryCursor(Query(language, "(alias) @mod"))
        except Exception:  # noqa: BLE001 — no elixir grammar is a skip, not a crash
            return []

        out: list[dict] = []
        for f in _walk(root, lambda p: p.suffix in (".ex", ".exs")):
            frm = next((i for d, i in owners if _under(f, d)), None)
            if frm is None:
                continue
            try:
                if f.stat().st_size > MAX_BYTES:
                    continue
                captures = cursor.captures(parser.parse(f.read_bytes()).root_node)
            except Exception:  # noqa: BLE001
                continue
            rel = str(f.relative_to(root))
            for node in captures.get("mod", []):
                ref = node.text.decode(errors="replace")
                # Longest prefix wins: `Phoenix.LiveView.Socket` belongs to
                # whoever owns `Phoenix.LiveView`, not to whoever owns
                # `Phoenix` — the deeper claim is the more specific truth.
                parts = ref.split(".")
                to = None
                for n in range(len(parts), 0, -1):
                    to = by_mod.get(".".join(parts[:n]))
                    if to:
                        break
                if to is None or to == frm:
                    continue
                out.append({"from_id": frm, "to_id": to, "kind": "import",
                            "direction": "out", "at": f"{rel}:{node.start_point[0] + 1}",
                            "probe": self.name})
        return out


PROBES: list[Probe] = [PythonProbe(), NodeProbe(), ElixirProbe()]


# ── what no probe covers ─────────────────────────────────────────────────

# The manifest each ecosystem announces itself with. An entry here is a
# promise to SAY the ecosystem is unmeasured — never to quietly count it
# clean, which is how a repo with an unprobed half reads as tended.
_MANIFESTS = {
    "go.mod": "go", "Cargo.toml": "rust",
    "Gemfile": "ruby", "pom.xml": "java", "build.gradle": "gradle",
    "build.gradle.kts": "gradle", "composer.json": "php",
    "pubspec.yaml": "dart", "Package.swift": "swift", "*.csproj": "dotnet",
}


def unprobed(root: Path, covered: set[str]) -> list[str]:
    """Ecosystems this repo declares that no registered probe reads.

    Silence would read as "covered" when it was not — the same rule
    `surface.py` applies to a language with no declaration query. A repo
    whose Elixir half is unmeasured must say so, or its zero phantoms are
    a lie of omission."""
    names = {n for n in _MANIFESTS if not n.startswith("*")}
    hits: dict[str, list[str]] = {}
    for f in _walk(root, lambda p: p.name in names or p.suffix == ".csproj"):
        eco = _MANIFESTS.get(f.name, "dotnet")
        if eco in covered:
            continue
        hits.setdefault(eco, []).append(str(f.relative_to(root)))
    return [f"{eco}: no probe — {len(fs)} manifest(s) NOT measured ({', '.join(sorted(fs)[:3])})"
            for eco, fs in sorted(hits.items())]
