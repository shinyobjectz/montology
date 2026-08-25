"""What a name IS, so an act can be about a type rather than about a spelling.

`pointer.fly()` resolved because somebody named a variable after the concept.
That is coincidence dressed as evidence: rename the variable to `p` and the
edge disappears, though the code does exactly the same thing. An ontology whose
edges depend on spelling is the diagram montology exists to replace.

So names are BOUND to types, from the tree, with no language server:

  x = Pointer()          a constructor call names the type
  x: Pointer             an annotation says it outright
  def f(x: Pointer)      so does a parameter
  self.x = Pointer()     and an attribute

Measured on qubie: 1,990 bindings across 140 Python files. Deliberately NOT a
type checker — no inference across returns, no generics, no imports resolved.
Those need a language server, and montology's whole shape is one binary and a
grammar pack. What is here is what the file itself says out loud, which is most
of what real code says.

The honest limits, said rather than hidden:
  * bindings are FILE-scoped. Two functions in one file each with a local `x`
    of different types will collide, and the later one wins. Function-level
    scoping is possible and is not done yet.
  * a name with no binding is not an error. It resolves by spelling as before,
    and the act records WHICH — `by-type` or `by-name` — so a canvas can draw
    a proven edge differently from a plausible one.
"""

from __future__ import annotations

from pathlib import Path

# How each grammar says "this name is that type".
SHAPES: dict[str, dict] = {
    "python": {
        "assign": "assignment", "left": "left", "right": "right", "ann": "type",
        "ctor": "call", "ctor_fn": "function",
        "param": "typed_parameter", "param_ann": "type",
        "attr": "attribute", "attr_field": "attribute",
    },
    "typescript": {
        "assign": "variable_declarator", "left": "name", "right": "value",
        "ann": "type", "ctor": "new_expression", "ctor_fn": "constructor",
        "param": "required_parameter", "param_ann": "type",
        "attr": "member_expression", "attr_field": "property",
    },
    "javascript": {
        "assign": "variable_declarator", "left": "name", "right": "value",
        "ann": None, "ctor": "new_expression", "ctor_fn": "constructor",
        "param": None, "param_ann": None,
        "attr": "member_expression", "attr_field": "property",
    },
}
SHAPES["tsx"] = SHAPES["typescript"]


def _text(node) -> str | None:
    return node.text.decode(errors="replace") if node is not None else None


def _type_name(node) -> str | None:
    """The bare name of a type, with the decoration taken off.

    `list[Pointer]`, `Optional[Pointer]`, `"Pointer"` and `Pointer | None` all
    name a Pointer somewhere. This takes the last identifier, which is right far
    more often than it is wrong and is honest about being a heuristic.
    """
    if node is None:
        return None
    # TypeScript hands back the whole annotation, colon and all
    text = (_text(node) or "").strip().lstrip(":").strip().strip("'\"")
    if not text:
        return None
    for cut in ("|", "="):
        text = text.split(cut)[0].strip()
    while text.endswith("[]"):          # TS arrays: `Pointer[]` is about pointers
        text = text[:-2].strip()
    if "[" in text:
        inner = text[text.index("[") + 1:].rstrip("]")
        outer = text[:text.index("[")]
        # a container names its CONTENT; `list[Pointer]` is about pointers
        text = inner.split(",")[-1].strip() if inner else outer
    text = text.rsplit(".", 1)[-1].strip()
    return text or None


def bindings(tree, lang: str) -> dict[str, str]:
    """name -> type, for one file. File-scoped; see the note above."""
    shape = SHAPES.get(lang)
    if shape is None:
        return {}
    out: dict[str, str] = {}

    def bind(name: str | None, type_node) -> None:
        ty = _type_name(type_node)
        if name and ty and ty[:1].isalpha():
            out[name] = ty

    def walk(node):
        if node.type == shape["assign"]:
            left = node.child_by_field_name(shape["left"])
            right = node.child_by_field_name(shape["right"])
            ann = node.child_by_field_name(shape["ann"]) if shape["ann"] else None
            name = None
            if left is not None and left.type in ("identifier", "property_identifier"):
                name = _text(left)
            elif left is not None and left.type == shape["attr"]:
                # self.pointer = Pointer() — the attribute is the name
                name = _text(left.child_by_field_name(shape["attr_field"]))
            if name:
                if ann is not None:
                    bind(name, ann)
                elif right is not None and right.type == shape["ctor"]:
                    fn = right.child_by_field_name(shape["ctor_fn"])
                    # `line = text.strip()` is a call, not a construction. Only a
                    # bare, capitalised name is a type by convention in both
                    # Python and TypeScript — precision over recall, because a
                    # wrong binding is worse than a missing one: it produces an
                    # edge that is confidently about the wrong thing.
                    if (fn is not None and fn.type == "identifier"
                            and (_text(fn) or "")[:1].isupper()):
                        bind(name, fn)
        elif shape["param"] and node.type == shape["param"]:
            first = node.named_children[0] if node.named_children else None
            bind(_text(first) if first is not None else None,
                 node.child_by_field_name(shape["param_ann"]))
        for child in node.named_children:
            walk(child)

    walk(tree.root_node)
    return out


def bindings_for(root: Path | None = None) -> dict[str, dict[str, str]]:
    """Every file's bindings, keyed by path relative to the workspace."""
    from montology_core import workspace_root
    from tree_sitter_language_pack import get_parser

    from .surface import LANG_BY_EXT, MAX_BYTES, _iter_files

    root = root or workspace_root()
    parsers: dict[str, object] = {}
    out: dict[str, dict[str, str]] = {}
    for f in _iter_files(root):
        lang = LANG_BY_EXT[f.suffix]
        if lang not in SHAPES:
            continue
        try:
            if lang not in parsers:
                parsers[lang] = get_parser(lang)
            if f.stat().st_size > MAX_BYTES:
                continue
            got = bindings(parsers[lang].parse(f.read_bytes()), lang)
        except Exception:  # noqa: BLE001 — one broken file is a gap, not a crash
            continue
        if got:
            out[str(f.relative_to(root))] = got
    return out
