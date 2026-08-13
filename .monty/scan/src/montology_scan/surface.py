"""Declarations, measured: every named thing the codebase declares.

tree-sitter parses; per-language queries name the declaration nodes worth
knowing (classes, functions, types, modules — the things people NAME).
A language without a query map is skipped and SAID to be skipped; silence
would read as "covered" when it was not.
"""

from __future__ import annotations

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


def _iter_files(root: Path) -> list[Path]:
    cfg = _scan_config(root)
    exclude = EXCLUDE_DIRS | set(cfg.get("exclude", []))
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
            if e.name in exclude or e.name.startswith("."):
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
