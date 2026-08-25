"""Acts: what the code DOES, as against what it declares.

The scan measured declarations — classes, functions, types, the things a
codebase NAMES. That is the noun side, and it is why every vocabulary built
with montology comes out about ninety percent nouns: montology's own is 30
nouns to 1 verb, qubie's is 100 to 9. A vocabulary of nouns describes a world
that never does anything.

An ACT is the other half: one thing the code does, read off the tree —
a SUBJECT (the declaration it happens inside), a VERB (the thing called), and
an OBJECT (what it is called on). `Engram.remember` calling `self.store(mention)`
is `Engram --store--> mention`, at a file and a line.

Two questions become askable, and neither could be asked before:

  is this verb a word? A verb the code performs a hundred times and the
  vocabulary never names is the verb-side `candidate` — vocabulary the codebase
  is asking for, in the half nobody was looking at.

  is what it acts ON a word? An act between two words is the vocabulary
  describing something real. An act between two things nobody has named is
  where the meaning has not been settled yet.

Noise is the whole difficulty here. A codebase performs `append`, `get` and
`len` constantly and none of it is domain vocabulary, so the mining is by
RECURRENCE and against a stop list, and every finding says how often it happens
and where. The instrument reports; it does not decide.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from .surface import LANG_BY_EXT, MAX_BYTES, _iter_files

# What a call means in each grammar. Deliberately only the shapes that carry a
# SUBJECT and a VERB — a bare `foo()` names no object and tells us nothing about
# what interacts with what.
ACT_QUERIES: dict[str, str] = {
    "python": """
        (call function: (attribute object: (identifier) @object
                                   attribute: (identifier) @verb)) @act
        (call function: (attribute object: (attribute attribute: (identifier) @object)
                                   attribute: (identifier) @verb)) @act
    """,
    "javascript": """
        (call_expression function: (member_expression
            object: (identifier) @object property: (property_identifier) @verb)) @act
    """,
    "typescript": """
        (call_expression function: (member_expression
            object: (identifier) @object property: (property_identifier) @verb)) @act
    """,
    "tsx": """
        (call_expression function: (member_expression
            object: (identifier) @object property: (property_identifier) @verb)) @act
    """,
    "go": """
        (call_expression function: (selector_expression
            operand: (identifier) @object field: (field_identifier) @verb)) @act
    """,
    "rust": """
        (call_expression function: (field_expression
            value: (identifier) @object field: (field_identifier) @verb)) @act
        (method_call_expression receiver: (identifier) @object name: (field_identifier) @verb) @act
    """,
    "ruby": """
        (call receiver: (identifier) @object method: (identifier) @verb) @act
    """,
}

# Verbs every codebase performs and no vocabulary should have to name. Not a
# judgement about the words — `get` is a fine English verb — but about whether
# seeing it a thousand times tells you anything about THIS domain.
PLUMBING = {
    "append", "extend", "insert", "pop", "get", "set", "put", "add", "remove",
    "join", "split", "strip", "lower", "upper", "format", "encode", "decode",
    "read", "write", "open", "close", "len", "keys", "values", "items", "copy",
    "update", "replace", "startswith", "endswith", "isdigit", "isalpha", "sort",
    "print", "log", "debug", "info", "warning", "error", "exception", "assert",
    "push", "map", "filter", "reduce", "forEach", "then", "catch", "test",
    "toString", "valueOf", "call", "apply", "bind", "json", "dumps", "loads",
    "group", "match", "search", "sub", "findall", "compile", "exists", "mkdir",
    "unwrap", "expect", "clone", "into", "iter", "collect", "push_str", "new",
    "commit", "execute", "fetchone", "fetchall", "cursor", "connect", "close",
    "self", "super", "init", "str", "repr", "dict", "list",
    "rsplit", "lstrip", "rstrip", "partition", "rpartition", "splitlines",
    "count", "index", "find", "title", "capitalize", "ljust", "rjust", "zfill",
}


def _enclosing(decls: list[dict], file: str, line: int) -> str | None:
    """Which declaration this act happens inside — the nearest one above it.

    An approximation, and said to be one: without a full scope resolution the
    nearest preceding declaration in the same file is the honest answer, and it
    is right for the shape almost all code has.
    """
    best, best_line = None, -1
    for d in decls:
        if d["file"] == file and d["line"] <= line and d["line"] > best_line:
            best, best_line = d["name"], d["line"]
    return best


def acts(root: Path | None = None, decls: list[dict] | None = None) -> dict:
    """Every act the tree can see. Deterministic; a language with no query map
    is SKIPPED and said to be skipped, the same rule the declarations follow."""
    from montology_core import workspace_root
    from tree_sitter_language_pack import get_language, get_parser

    from .surface import declarations

    root = root or workspace_root()
    if decls is None:
        decls = declarations(root)["decls"]

    out: list[dict] = []
    skipped: dict[str, int] = {}
    parsers: dict[str, tuple] = {}

    for f in _iter_files(root):
        lang = LANG_BY_EXT[f.suffix]
        query_src = ACT_QUERIES.get(lang)
        if query_src is None:
            skipped[lang] = skipped.get(lang, 0) + 1
            continue
        try:
            if lang not in parsers:
                language = get_language(lang)
                try:
                    from tree_sitter import Query, QueryCursor
                    parsers[lang] = (get_parser(lang), ("cursor", QueryCursor(Query(language, query_src))))
                except ImportError:
                    parsers[lang] = (get_parser(lang), ("query", language.query(query_src)))
            parser, (mode, q) = parsers[lang]
            if f.stat().st_size > MAX_BYTES:
                continue
            tree = parser.parse(f.read_bytes())
            caps = q.captures(tree.root_node) if mode == "cursor" else q.captures(tree.root_node)
        except Exception:  # noqa: BLE001 — one broken file is a count, not a crash
            continue

        # captures come back grouped by name; pair them up by position
        verbs = {n.start_point[0]: n for n in caps.get("verb", [])}
        objects = {n.start_point[0]: n for n in caps.get("object", [])}
        rel = str(f.relative_to(root))
        for line, vnode in verbs.items():
            onode = objects.get(line)
            if onode is None:
                continue
            verb = vnode.text.decode(errors="replace")
            obj = onode.text.decode(errors="replace")
            if verb.startswith("_") or obj in ("self", "this"):
                # `self.store(...)` still tells us the VERB, which is the half
                # that matters most; the subject is the enclosing declaration.
                if obj not in ("self", "this"):
                    continue
                obj = None
            out.append({"verb": verb, "object": obj, "lang": lang,
                        "file": rel, "line": line + 1,
                        "subject": _enclosing(decls, rel, line + 1)})
    return {"acts": out, "skipped": skipped}


def _norm(name: str | None) -> str:
    return (name or "").lower().replace("_", "-")


def domain_acts(root: Path | None = None) -> list[dict]:
    """The acts that are about THIS domain rather than about a library.

    The discriminator is montology's own thesis: an act is domain vocabulary
    when the thing it acts ON is something we name. `engram.store(...)` is about
    the system; `time.sleep(...)` is about the standard library, and counting
    both together buries the first under the second. Measured on qubie: 7,757
    acts, of which 100 land on a word — and the flat list without this filter
    was `time`, `sleep`, `monotonic`, `expanduser`, which says nothing about
    what qubie is.
    """
    from montology_ontology import words

    have = {w["name"].lower() for w in words()}
    out = []
    for a in acts(root)["acts"]:
        obj = _norm(a["object"])
        if not obj or obj not in have:
            continue
        subj = _norm(a["subject"])
        out.append({**a, "object": obj,
                    "subject_word": subj if subj in have else None,
                    "verb_is_word": a["verb"].lower() in have})
    return out


def unnamed_verbs(root: Path | None = None, top: int = 15) -> list[dict]:
    """What the vocabulary names, and everything it is made to DO that it does
    not name — grouped by the word, because that is the shape of the finding.

    `pointer` is a word in qubie. The code flies it, hides it, attaches it,
    hardens it and destroys it, and the vocabulary names none of those. A word
    with five verbs and no verbs is a noun standing in for a behaviour nobody
    has settled.
    """
    by_word: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    named: dict[str, set[str]] = defaultdict(set)
    for a in domain_acts(root):
        verb = a["verb"].lower()
        if verb in PLUMBING or len(verb) < 3 or not verb.isalpha():
            continue
        if a["verb_is_word"]:
            named[a["object"]].add(verb)
            continue
        where = by_word[a["object"]][verb]
        if len(where) < 4:
            where.append(f"{a['file']}:{a['line']}")

    rows = [{"word": word, "unnamed": sorted(verbs), "named": sorted(named.get(word, [])),
             "at": {v: w for v, w in verbs.items()}}
            for word, verbs in by_word.items()]
    rows.sort(key=lambda r: (-len(r["unnamed"]), r["word"]))
    return rows[:top]


def render(root: Path | None = None, top: int = 15) -> list[str]:
    rows = unnamed_verbs(root, top=top)
    if not rows:
        return ["nothing the vocabulary names is acted on by a verb it does not "
                "name — either the verbs are covered, or the tree cannot see "
                "what this code does."]
    total = sum(len(r["unnamed"]) for r in rows)
    out = [f"{total} verb(s) performed ON words this vocabulary names, and does "
           f"not name itself:", ""]
    for r in rows:
        held = f"  ({', '.join(r['named'])} named)" if r["named"] else ""
        out.append(f"  {r['word']} — acted on {len(r['unnamed'])} way(s) with no word{held}")
        for verb in r["unnamed"]:
            out.append(f"      .{verb:<20} {r['at'][verb][0]}")
    out += ["",
            "A vocabulary of nouns describes a world that never does anything. "
            "montology's own is 30 nouns to 1 verb; qubie's is 100 to 9.",
            "Name one: `monty onto add <verb> \"<definition>\" --pos verb`."]
    return out
