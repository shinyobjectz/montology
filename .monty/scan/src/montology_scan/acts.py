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

# What a call looks like in each grammar, as FIELDS rather than as a query.
#
# The first version matched captures and paired them by line, which silently
# dropped every line holding two calls and could never reach the ARGUMENTS —
# and the arguments are where the ontology is. `engram.store(mention)` is a
# noun, a verb and a noun; keeping only `engram` and `store` throws away the
# half that makes it a sentence.
CALL_SHAPES: dict[str, dict] = {
    "python": {"node": "call", "fn": "function", "recv_kind": "attribute",
               "recv": "object", "verb": "attribute", "args": "arguments"},
    "javascript": {"node": "call_expression", "fn": "function",
                   "recv_kind": "member_expression", "recv": "object",
                   "verb": "property", "args": "arguments"},
    "typescript": {"node": "call_expression", "fn": "function",
                   "recv_kind": "member_expression", "recv": "object",
                   "verb": "property", "args": "arguments"},
    "tsx": {"node": "call_expression", "fn": "function",
            "recv_kind": "member_expression", "recv": "object",
            "verb": "property", "args": "arguments"},
    "go": {"node": "call_expression", "fn": "function",
           "recv_kind": "selector_expression", "recv": "operand",
           "verb": "field", "args": "arguments"},
    "rust": {"node": "call_expression", "fn": "function",
             "recv_kind": "field_expression", "recv": "value",
             "verb": "field", "args": "arguments"},
    "ruby": {"node": "call", "fn": None, "recv_kind": None,
             "recv": "receiver", "verb": "method", "args": "arguments"},
}

# Names that are never a concept, whatever the grammar says.
_SKIP_NAMES = {"self", "this", "cls", "super", "None", "True", "False", "null"}

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
    "commit", "execute", "fetchone", "fetchall", "cursor", "connect",
    "init", "str", "repr", "dict", "list", "rsplit", "lstrip", "rstrip",
    "partition", "rpartition", "splitlines", "count", "index", "find", "title",
    "capitalize", "ljust", "rjust", "zfill", "startsWith", "endsWith", "slice",
}


def _text(node) -> str | None:
    return node.text.decode(errors="replace") if node is not None else None


def _parts(node, shape) -> tuple[str | None, str | None, list[str]]:
    """The receiver, the verb and the identifier arguments of one call."""
    if shape["fn"]:
        fn = node.child_by_field_name(shape["fn"])
        if fn is None or fn.type != shape["recv_kind"]:
            return None, None, []
        recv_node = fn.child_by_field_name(shape["recv"])
        # `Path(__file__).resolve()` has a receiver that is an expression, and an
        # expression names nothing. Only a plain name can be a concept — with
        # one step through an attribute, so `self.engram.store()` still says
        # `engram`.
        if recv_node is not None and recv_node.type == shape["recv_kind"]:
            recv_node = recv_node.child_by_field_name(shape["verb"])
        recv = _text(recv_node) if recv_node is not None and recv_node.type in (
            "identifier", "property_identifier", "field_identifier") else None
        verb = _text(fn.child_by_field_name(shape["verb"]))
    else:
        recv = _text(node.child_by_field_name(shape["recv"]))
        verb = _text(node.child_by_field_name(shape["verb"]))

    args: list[str] = []
    arglist = node.child_by_field_name(shape["args"])
    if arglist is not None:
        for child in arglist.named_children:
            # a bare name, or the value of a keyword argument — both name a
            # thing; anything more complex is an expression, not a concept
            if child.type in ("identifier", "shorthand_property_identifier"):
                args.append(_text(child))
            elif child.type in ("keyword_argument", "pair"):
                value = child.child_by_field_name("value")
                if value is not None and value.type == "identifier":
                    args.append(_text(value))
            elif child.type == "attribute":
                attr = child.child_by_field_name("attribute")
                if attr is not None:
                    args.append(_text(attr))
    return recv, verb, [a for a in args if a and a not in _SKIP_NAMES]


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
    from tree_sitter_language_pack import get_parser

    from .surface import declarations

    root = root or workspace_root()
    if decls is None:
        decls = declarations(root)["decls"]

    out: list[dict] = []
    skipped: dict[str, int] = {}
    parsers: dict[str, object] = {}

    def walk(node, shape, rel, lang):
        if node.type == shape["node"]:
            recv, verb, args = _parts(node, shape)
            if verb and not verb.startswith("_"):
                line = node.start_point[0] + 1
                subject = _enclosing(decls, rel, line)
                if recv in _SKIP_NAMES:
                    recv = None
                # One act per (receiver, verb) and one per argument: the second
                # is the triple — a noun, a verb and a noun — and it is the
                # reason this reads as an ontology rather than as a call log.
                out.append({"verb": verb, "object": recv, "arg": None, "lang": lang,
                            "file": rel, "line": line, "subject": subject})
                for a in args:
                    out.append({"verb": verb, "object": recv, "arg": a, "lang": lang,
                                "file": rel, "line": line, "subject": subject})
        for child in node.named_children:
            walk(child, shape, rel, lang)

    for f in _iter_files(root):
        lang = LANG_BY_EXT[f.suffix]
        shape = CALL_SHAPES.get(lang)
        if shape is None:
            skipped[lang] = skipped.get(lang, 0) + 1
            continue
        try:
            if lang not in parsers:
                parsers[lang] = get_parser(lang)
            if f.stat().st_size > MAX_BYTES:
                continue
            tree = parsers[lang].parse(f.read_bytes())
        except Exception:  # noqa: BLE001 — one broken file is a count, not a crash
            continue
        walk(tree.root_node, shape, str(f.relative_to(root)), lang)

    return {"acts": out, "skipped": skipped}


def _norm(name: str | None) -> str:
    return (name or "").lower().replace("_", "-")


def domain_acts(root: Path | None = None, *, typed: bool = True) -> list[dict]:
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

    from .bindings import bindings_for

    have = {w["name"].lower() for w in words()}
    binds = bindings_for(root) if typed else {}

    def resolve(name: str | None, file: str) -> tuple[str | None, str]:
        """What this name IS, and how we know.

        A name bound to a type resolves BY TYPE, which survives a rename of the
        variable. A name that is simply spelled like a word resolves BY NAME,
        which does not — and the two must not be drawn alike, because one is
        evidence and the other is a coincidence that happens to be useful.
        """
        if not name:
            return None, "none"
        ty = _norm(binds.get(file, {}).get(name))
        if ty and ty in have:
            return ty, "by-type"
        low = _norm(name)
        return (low, "by-name") if low in have else (None, "none")

    out = []
    for a in acts(root)["acts"]:
        obj, how = resolve(a["object"], a["file"])
        if not obj:
            continue
        subj, subj_how = resolve(a["subject"], a["file"])
        out.append({**a, "object": obj, "resolved": how,
                    "subject_word": subj, "subject_resolved": subj_how,
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
    proven: dict[str, set[str]] = defaultdict(set)
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
        if a["resolved"] == "by-type":
            proven[a["object"]].add(verb)

    rows = [{"word": word, "unnamed": sorted(verbs), "named": sorted(named.get(word, [])),
             "proven": sorted(proven.get(word, [])),
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
            how = "by type" if verb in r["proven"] else "by name"
            out.append(f"      .{verb:<20} {r['at'][verb][0]:<38} ({how})")
    out += ["",
            "A vocabulary of nouns describes a world that never does anything. "
            "montology's own is 30 nouns to 1 verb; qubie's is 100 to 9.",
            "Name one: `monty onto add <verb> \"<definition>\" --pos verb`."]
    return out
