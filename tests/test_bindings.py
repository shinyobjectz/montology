"""Binding names to types, so an act is about a type and not about a spelling.

`pointer.fly()` resolved because somebody named a variable after the concept.
Rename it to `p` and the edge disappears though the code does the same thing —
an ontology whose edges depend on spelling is the diagram montology replaces.
"""

import pytest
from tree_sitter_language_pack import get_parser


def binds(src, lang="python"):
    from montology_scan.bindings import bindings

    return bindings(get_parser(lang).parse(src.encode()), lang)


def test_the_four_ways_a_file_says_what_a_name_is():
    got = binds(
        "def walk(target: Pointer, n: int):\n"
        "    p = Pointer()\n"
        "    q: Pointer = None\n"
        "    self.held = Pointer()\n"
    )
    assert got["target"] == "Pointer"      # a parameter annotation
    assert got["p"] == "Pointer"           # a constructor call
    assert got["q"] == "Pointer"           # a variable annotation
    assert got["held"] == "Pointer"        # an attribute
    assert got["n"] == "int"


def test_a_method_call_is_not_a_construction():
    """`line = text.strip()` bound `line` to `strip` until this was fixed. A
    wrong binding is worse than a missing one: it produces an edge that is
    confidently about the wrong thing."""
    got = binds("def f(text):\n    line = text.strip()\n    n = len(text)\n")
    assert "line" not in got and "n" not in got


def test_decoration_comes_off_a_type():
    """A container names its CONTENT: list[Pointer] is about pointers."""
    got = binds(
        "def f(a: list[Pointer], b: Optional[Engram], c: 'Trail', d: Step | None):\n"
        "    pass\n")
    assert got["a"] == "Pointer" and got["b"] == "Engram"
    assert got["c"] == "Trail" and got["d"] == "Step"


def test_typescript_says_it_its_own_way():
    got = binds("const p: Pointer = load();\nconst q = new Engram();\n"
                "const many: Pointer[] = [];\n", "typescript")
    assert got["p"] == "Pointer" and got["q"] == "Engram"
    assert got["many"] == "Pointer"        # `Pointer[]` is about pointers


def test_an_act_resolved_by_type_survives_renaming_the_variable(tmp_path, onto_db, monkeypatch):
    """The whole point. Both files do the same thing; only one names the
    variable after the concept, and both must produce the edge."""
    from montology_scan.acts import domain_acts

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "named.py").write_text("def a():\n    pointer.fly(1)\n")
    (tmp_path / "src" / "typed.py").write_text("def b():\n    p = Pointer()\n    p.fly(1)\n")
    onto_db.add("pointer", "what the person is looking at", kind="core", pos="noun")

    how = {a["file"]: a["resolved"] for a in domain_acts() if a["verb"] == "fly"}
    assert how["src/named.py"] == "by-name"
    assert how["src/typed.py"] == "by-type"     # the variable is called `p`


def test_by_name_and_by_type_are_not_drawn_alike(tmp_path, onto_db, monkeypatch):
    """Drawing them the same would be the canvas claiming a confidence it does
    not have."""
    from montology_canvas import graph

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "m.py").write_text(
        "class tour:\n    pass\n\n"
        "def tour_run():\n    p = Pointer()\n    p.fly(1)\n")
    onto_db.add("pointer", "what the person is looking at", kind="core", pos="noun")
    onto_db.add("tour", "a walk through the system", kind="core", pos="noun")

    node = next(n for n in graph()["nodes"] if n["id"] == "word:pointer")
    assert node["data"]["verbs_unnamed"] == ["fly"]
    assert node["data"]["verbs_proven"] == ["fly"]


def test_a_language_with_no_binding_shape_is_simply_empty():
    """Not an error: the act still resolves by name, and says that it did."""
    assert binds("class Thing { }", "go") == {}
