"""Declarations, measured: every named thing the codebase declares.

tree-sitter parses; per-language queries name the declaration nodes worth
knowing (classes, functions, types, modules — the things people NAME).
A language without a query map is skipped and SAID to be skipped; silence
would read as "covered" when it was not.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

# extension -> tree-sitter-language-pack language name
LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".ex": "elixir", ".exs": "elixir",
    ".rb": "ruby",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".lua": "lua",
    ".gd": "gdscript",
}

# what counts as "a declaration" per language: (query, capture kind label)
DECL_QUERIES: dict[str, str] = {
    "python": """
        (class_definition name: (identifier) @name.class)
        (function_definition name: (identifier) @name.function)
    """,
    "javascript": """
        (class_declaration name: (identifier) @name.class)
        (function_declaration name: (identifier) @name.function)
        (method_definition name: (property_identifier) @name.method)
        (variable_declarator name: (identifier) @name.const value: (arrow_function))
    """,
    "typescript": """
        (class_declaration name: (type_identifier) @name.class)
        (function_declaration name: (identifier) @name.function)
        (interface_declaration name: (type_identifier) @name.interface)
        (type_alias_declaration name: (type_identifier) @name.type)
        (enum_declaration name: (identifier) @name.enum)
        (method_definition name: (property_identifier) @name.method)
    """,
    "tsx": """
        (class_declaration name: (type_identifier) @name.class)
        (function_declaration name: (identifier) @name.function)
        (interface_declaration name: (type_identifier) @name.interface)
        (type_alias_declaration name: (type_identifier) @name.type)
    """,
    "go": """
        (type_spec name: (type_identifier) @name.type)
        (function_declaration name: (identifier) @name.function)
        (method_declaration name: (field_identifier) @name.method)
    """,
    "rust": """
        (struct_item name: (type_identifier) @name.struct)
        (enum_item name: (type_identifier) @name.enum)
        (trait_item name: (type_identifier) @name.trait)
        (function_item name: (identifier) @name.function)
        (mod_item name: (identifier) @name.module)
        (type_item name: (type_identifier) @name.type)
    """,
    "elixir": """
        (call target: (identifier) @_kw (arguments (alias) @name.module)
          (#eq? @_kw "defmodule"))
        (call target: (identifier) @_kw2
          (arguments (call target: (identifier) @name.function))
          (#match? @_kw2 "^(def|defp|defmacro)$"))
    """,
    "ruby": """
        (class name: (constant) @name.class)
        (module name: (constant) @name.module)
        (method name: (identifier) @name.method)
    """,
    "java": """
        (class_declaration name: (identifier) @name.class)
        (interface_declaration name: (identifier) @name.interface)
        (enum_declaration name: (identifier) @name.enum)
        (method_declaration name: (identifier) @name.method)
    """,
    # tree-sitter-swift collapses struct / class / enum / actor / extension into
    # one `class_declaration`, told apart by the `declaration_kind` token. An
    # extension is the useful exclusion: it carries a `user_type` where the
    # others carry a `type_identifier`, so matching the latter means an
    # `extension Harness` never counts as declaring `Harness` — it does not.
    "swift": """
        (class_declaration declaration_kind: "struct" name: (type_identifier) @name.struct)
        (class_declaration declaration_kind: "class" name: (type_identifier) @name.class)
        (class_declaration declaration_kind: "enum" name: (type_identifier) @name.enum)
        (class_declaration declaration_kind: "actor" name: (type_identifier) @name.actor)
        (protocol_declaration name: (type_identifier) @name.protocol)
        (typealias_declaration name: (type_identifier) @name.type)
        (associatedtype_declaration name: (type_identifier) @name.type)
        (source_file (function_declaration name: (simple_identifier) @name.function))
        (class_body (function_declaration name: (simple_identifier) @name.method))
        (enum_class_body (function_declaration name: (simple_identifier) @name.method))
        (protocol_body (protocol_function_declaration
          name: (simple_identifier) @name.method))
    """,
    "c": """
        (function_definition declarator: (function_declarator
          declarator: (identifier) @name.function))
        (struct_specifier name: (type_identifier) @name.struct)
    """,
    "cpp": """
        (function_definition declarator: (function_declarator
          declarator: (identifier) @name.function))
        (class_specifier name: (type_identifier) @name.class)
        (struct_specifier name: (type_identifier) @name.struct)
    """,
    # GDScript (Godot 4). `class_name Foo` names the script itself — the
    # word the rest of the project uses — so it is a class; an inner
    # `class Bar:` is also a class. A signal is a named thing people say out
    # loud ("the died signal"), so it counts; a plain `var` is a member and
    # counts as a variable, an `@export var` no differently.
    "gdscript": """
        (class_name_statement (name) @name.class)
        (class_definition (name) @name.class)
        (function_definition (name) @name.function)
        (signal_statement (name) @name.signal)
        (const_statement (name) @name.const)
        (variable_statement (name) @name.variable)
        (enum_definition (name) @name.enum)
    """,
}

# What a name is DECLARED TO BE, where the language says so out loud.
#
# A declaration query answers "what is named here"; this answers "and what
# does that name hold". Two type declarations of one name that do not say
# the same thing are two things wearing one noun — the only mechanical
# evidence available for the interchangeability test, and the reason the
# value-type guard is more than a promise. Languages absent here are absent
# on purpose: Python's `name: str` annotations are not declarations of a
# named type, and inferring one would be guessing.
TYPE_QUERIES: dict[str, str] = {
    "elixir": """
        (unary_operator
          operand: (call target: (identifier) @_kw
            (arguments (binary_operator
              left: (identifier) @type.name
              right: (_) @type.value)))
          (#match? @_kw "^(type|typep|opaque)$"))
    """,
    "typescript": """
        (type_alias_declaration name: (type_identifier) @type.name value: (_) @type.value)
        (interface_declaration name: (type_identifier) @type.name body: (_) @type.value)
    """,
    "tsx": """
        (type_alias_declaration name: (type_identifier) @type.name value: (_) @type.value)
        (interface_declaration name: (type_identifier) @type.name body: (_) @type.value)
    """,
    "go": """
        (type_spec name: (type_identifier) @type.name type: (_) @type.value)
    """,
    "rust": """
        (type_item name: (type_identifier) @type.name type: (_) @type.value)
        (struct_item name: (type_identifier) @type.name body: (_) @type.value)
    """,
    # Swift's grammar gives `typealias RowID = String` two `name` fields — the
    # alias and the aliased type — so the pair is taken by NODE type, not by
    # field. Only the alias is here: a struct body is a shape, not a value, and
    # two structs of one name in one module do not compile anyway.
    "swift": """
        (typealias_declaration name: (type_identifier) @type.name
                               name: (_) @type.value)
    """,
    # GDScript: `var health: int` says the type out loud; `var x := 1` and an
    # untyped `var y` say nothing and are not matched. Constants likewise.
    "gdscript": """
        (variable_statement (name) @type.name (type) @type.value)
        (const_statement (name) @type.name (type) @type.value)
    """,
}

EXCLUDE_DIRS = {".git", ".hg", "node_modules", ".venv", "venv", "__pycache__",
                "dist", "build", "target", ".next", ".turbo", "vendor",
                ".monty", ".claude", ".cursor", "deps", "_build", ".pytest_cache"}
MAX_BYTES = 1_000_000


def languages_covered() -> list[str]:
    return sorted(DECL_QUERIES)


def _scan_config(root: Path) -> dict:
    """[scan] from .monty/montology.toml — include (extra roots, may be
    hidden), exclude (extra dir names). Missing file = defaults."""
    import tomllib

    f = root / ".monty" / "montology.toml"
    if not f.exists():
        return {}
    try:
        return tomllib.loads(f.read_text()).get("scan", {})
    except tomllib.TOMLDecodeError:
        return {}


def _excluded(rel: Path, name: str, patterns: list[str]) -> bool:
    """Does this path match anything the workspace asked us not to read?

    Matched as a GLOB against the path from the root, and as a bare name, and
    against every parent directory of the path. All three, because the config
    is written in globs — `**/dist/**`, `_archive/**` — and for a long time
    only the bare-name form did anything. Every glob in every workspace
    silently matched nothing, which is the worst way for a filter to fail: the
    scan reported a confident count over files nobody meant to include.
    """
    text = str(rel)
    for pattern in patterns:
        # `**/*.min.js` must also match a .min.js sitting at the root: fnmatch
        # reads the `/` literally, so the anchored form alone never fires there.
        loose = pattern[3:] if pattern.startswith("**/") else pattern
        if (fnmatch(text, pattern) or fnmatch(name, pattern)
                or fnmatch(text, loose) or fnmatch(name, loose)):
            return True
        # `**/dist/**` should exclude the directory itself, not only what is
        # under it — otherwise the walk descends before the pattern can bite.
        bare = pattern.strip("*/")
        if bare and bare in rel.parts:
            return True
    return False


def _iter_files(root: Path) -> list[Path]:
    cfg = _scan_config(root)
    patterns = list(cfg.get("exclude", []))
    out: list[Path] = []
    stack = [root] + [root / inc for inc in cfg.get("include", [])
                      if (root / inc).is_dir()]
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.name in EXCLUDE_DIRS or e.name.startswith("."):
                continue
            try:
                rel = e.relative_to(root)
            except ValueError:
                continue
            if _excluded(rel, e.name, patterns):
                continue
            if e.is_dir():
                stack.append(e)
            elif e.suffix in LANG_BY_EXT:
                out.append(e)
    return out


def declarations(root: Path) -> dict:
    """Every named declaration under `root`, plus what was skipped.

    Returns {"decls": [{name, kind, lang, file, line}], "files": n,
    "skipped_langs": {...}, "errors": n}."""
    from tree_sitter_language_pack import get_language, get_parser

    decls: list[dict] = []
    skipped: dict[str, int] = {}
    errors = 0
    files = _iter_files(root)
    parsers: dict[str, tuple] = {}
    for f in files:
        lang = LANG_BY_EXT[f.suffix]
        query_src = DECL_QUERIES.get(lang)
        if query_src is None:
            skipped[lang] = skipped.get(lang, 0) + 1
            continue
        try:
            if lang not in parsers:
                language = get_language(lang)
                try:
                    from tree_sitter import Query, QueryCursor
                    query = Query(language, query_src)
                    runner = ("cursor", QueryCursor(query))
                except ImportError:
                    query = language.query(query_src)
                    runner = ("query", query)
                parsers[lang] = (get_parser(lang), runner)
            parser, (mode, q) = parsers[lang]
            if f.stat().st_size > MAX_BYTES:
                continue
            tree = parser.parse(f.read_bytes())
            captures = (q.captures(tree.root_node) if mode == "cursor"
                        else q.captures(tree.root_node))
            # both APIs: dict {capture_name: [nodes]} in tree-sitter >= 0.23
            for cap_name, nodes in captures.items():
                if not cap_name.startswith("name."):
                    continue
                kind = cap_name.split(".", 1)[1]
                for node in nodes:
                    decls.append({
                        "name": node.text.decode(errors="replace"),
                        "kind": kind, "lang": lang,
                        "file": str(f.relative_to(root)),
                        "line": node.start_point[0] + 1,
                    })
        except Exception:  # noqa: BLE001 — one broken file is a count, not a crash
            errors += 1
    return {"decls": decls, "files": len(files),
            "skipped_langs": skipped, "errors": errors}


def _normalised(text: str) -> str:
    """One declaration's right-hand side, comparable: whitespace collapsed.
    Nothing cleverer — a difference montology cannot see it does not claim
    to have checked, and formatting is the only difference it may erase."""
    return " ".join(text.split())


def type_declarations(root: Path) -> list[dict]:
    """Every declared type and what it holds: [{name, value, file, line, lang}].

    Pairs each name with its right-hand side per MATCH, never by position in
    two capture lists — an interface with no body would otherwise shift every
    later pair and invent divergences that are not there.
    """
    from tree_sitter_language_pack import get_language, get_parser

    out: list[dict] = []
    parsers: dict[str, tuple] = {}
    for f in _iter_files(root):
        lang = LANG_BY_EXT[f.suffix]
        query_src = TYPE_QUERIES.get(lang)
        if query_src is None:
            continue
        try:
            if lang not in parsers:
                language = get_language(lang)
                from tree_sitter import Query, QueryCursor

                parsers[lang] = (get_parser(lang), QueryCursor(Query(language, query_src)))
            parser, cursor = parsers[lang]
            if f.stat().st_size > MAX_BYTES:
                continue
            tree = parser.parse(f.read_bytes())
            for _pattern, caps in cursor.matches(tree.root_node):
                names, values = caps.get("type.name", []), caps.get("type.value", [])
                if not names or not values:
                    continue
                out.append({
                    "name": names[0].text.decode(errors="replace"),
                    "value": _normalised(values[0].text.decode(errors="replace")),
                    "lang": lang,
                    "file": str(f.relative_to(root)),
                    "line": names[0].start_point[0] + 1,
                })
        except Exception:  # noqa: BLE001 — one broken file is silence, not a crash
            continue
    return out
