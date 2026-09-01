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

# Swift does not fit the left/right/annotation field model: a
# `property_declaration` keeps its type in an unnamed `type_annotation` child,
# and a `parameter` spells BOTH the argument name and its type with the field
# `name`. Rather than bend the shared shape until it lies about the other
# grammars, Swift reads through its own function below.
SHAPES["swift"] = {"dialect": "swift"}


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
        # a container names its CONTENT; `list[Pointer]` is about pointers, and
        # so is Swift's `[Row]` — a dictionary by its VALUE, `[String: Row]`.
        text = inner.split(",")[-1].split(":")[-1].strip() if inner else outer
    # Swift's optional sigils decorate a type without changing which one it is
    text = text.rstrip("?!").strip()
    text = text.rsplit(".", 1)[-1].strip()
    return text or None


def _swift_bindings(tree) -> dict[str, str]:
    """name -> type for one Swift file, read off the three places Swift says
    it out loud: a property's annotation, a property's constructor call, and a
    parameter's type. Swift is unusually generous here — an annotation is
    idiomatic where Python's is optional — so the binding rate is high."""
    out: dict[str, str] = {}

    def bind(name: str | None, type_node) -> None:
        ty = _type_name(type_node)
        if name and ty and ty[:1].isalpha():
            out[name] = ty

    def named(node, field: str) -> list:
        """Every child under `field` — Swift reuses `name` for both halves of
        a parameter and of a typealias, so one lookup is never enough."""
        return [node.child(i) for i in range(node.child_count)
                if node.field_name_for_child(i) == field]

    def walk(node):
        if node.type == "property_declaration":
            # `var cell: Cell = Cell()` / `let name: String`
            name_node = node.child_by_field_name("name")
            name = _text(name_node) if name_node is not None else None
            ann = next((c for c in node.named_children
                        if c.type == "type_annotation"), None)
            if ann is not None:
                bind(name, ann.named_children[0] if ann.named_children else None)
            else:
                # `let harness = Harness()` — a capitalised callee is a type by
                # convention, the same precision-over-recall rule as elsewhere.
                call = next((c for c in node.named_children
                             if c.type == "call_expression"), None)
                if call is not None and call.named_children:
                    fn = call.named_children[0]
                    if fn.type == "simple_identifier" and (_text(fn) or "")[:1].isupper():
                        bind(name, fn)
        elif node.type == "parameter":
            # `func fly(to p: Pointer)` — the external label is not the name
            names = named(node, "name")
            arg = next((n for n in names if n.type == "simple_identifier"), None)
            ty = next((n for n in names if n.type != "simple_identifier"), None)
            bind(_text(arg) if arg is not None else None, ty)
        for child in node.named_children:
            walk(child)

    walk(tree.root_node)
    return out


def bindings(tree, lang: str) -> dict[str, str]:
    """name -> type, for one file. File-scoped; see the note above."""
    shape = SHAPES.get(lang)
    if shape is None:
        return {}
    if shape.get("dialect") == "swift":
        return _swift_bindings(tree)
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
