"""Swift, read the same way every other language is read.

Swift is the grammar that fits montology's shared shapes worst, and the ways
it does not fit are exactly the ways a reader written from a Python intuition
would silently under-report: struct, class, enum and actor all arrive as one
node kind; an `extension` looks like a declaration and is not; a parameter
spells its own name and its type with the same field; and a name travels as
`simple_identifier`, which the migration sweep did not know about at all.
Each of those is a case below, because a reader that quietly sees nothing is
worse than no reader — it reports a clean tree it never actually read.
"""

import pytest

SOURCE = """\
import Foundation

public struct Harness: Sendable {
    let name: String
    var cell: Cell = Cell()
    func fly(to p: Pointer) -> Bool { true }
}

final class Runner {
    private var pointer: Pointer
    func run() { engram.store(mention) }
}

protocol Flyable {
    associatedtype Wing
    func fly()
}

enum Verdict: String {
    case tended
    func describe() -> String { "x" }
}

extension Harness: Flyable {
    func land() {}
}

actor Ledger {}

typealias RowID = String

func topLevel(_ n: Int) -> Int { n }
"""


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "app"\n')
    (tmp_path / "Sources").mkdir()
    (tmp_path / "Sources" / "Harness.swift").write_text(SOURCE)
    return tmp_path


def _decls(repo):
    from montology_scan.surface import declarations

    got = declarations(repo)
    assert got["errors"] == 0
    assert "swift" not in got["skipped_langs"], "a covered language must not be skipped"
    return {(d["kind"], d["name"]) for d in got["decls"]}


def test_swift_is_covered_at_all():
    from montology_scan import languages_covered

    assert "swift" in languages_covered()


def test_every_kind_swift_declares(repo):
    got = _decls(repo)
    assert ("struct", "Harness") in got
    assert ("class", "Runner") in got
    assert ("enum", "Verdict") in got
    assert ("actor", "Ledger") in got
    assert ("protocol", "Flyable") in got
    assert ("type", "RowID") in got
    assert ("type", "Wing") in got
    assert ("function", "topLevel") in got


def test_a_struct_is_not_reported_as_a_class(repo):
    """The grammar gives all four one node kind. Collapsing them would make
    `monty scan --candidates` say `class Verdict`, which is not what the file
    says and not what anyone on the team would call it."""
    kinds = {name: kind for kind, name in _decls(repo)}
    assert kinds["Harness"] == "struct"
    assert kinds["Verdict"] == "enum"
    assert kinds["Ledger"] == "actor"


def test_an_extension_does_not_declare_the_name_it_extends(repo):
    """`extension Harness` is a second mention of one word, not a second
    declaration of it — counted as a declaration it would look like the very
    collision the gate exists to catch, in the one file that is innocent."""
    got = _decls(repo)
    assert sum(1 for kind, name in got if name == "Harness") == 1
    # but the methods it adds are still the code's vocabulary
    assert ("method", "land") in got


def test_methods_are_found_inside_every_body_kind(repo):
    """A class body, an enum body and a protocol body are three node types in
    this grammar; missing one loses every method of that shape."""
    got = _decls(repo)
    assert ("method", "fly") in got        # struct/class body
    assert ("method", "describe") in got   # enum_class_body
    assert ("method", "run") in got


def test_one_alias_declared_as_two_things_is_a_divergence(tmp_path):
    from montology_scan.surface import type_declarations

    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "app"\n')
    (tmp_path / "a.swift").write_text("typealias RowID = String\n")
    (tmp_path / "b.swift").write_text("typealias RowID = Int\n")
    rows = [r for r in type_declarations(tmp_path) if r["name"] == "RowID"]
    assert {r["value"] for r in rows} == {"String", "Int"}


# ── bindings ────────────────────────────────────────────────────────────

def _binds(src):
    from tree_sitter_language_pack import get_parser

    from montology_scan.bindings import bindings

    return bindings(get_parser("swift").parse(src.encode()), "swift")


def test_the_three_ways_a_swift_file_says_what_a_name_is():
    got = _binds(
        "struct S {\n"
        "    let held: Pointer\n"
        "    let made = Pointer()\n"
        "    func fly(to p: Pointer) {}\n"
        "}\n")
    assert got["held"] == "Pointer"   # a property annotation
    assert got["made"] == "Pointer"   # a constructor call
    assert got["p"] == "Pointer"      # a parameter type


def test_an_external_label_is_not_the_parameter_name():
    """`func fly(to p: Pointer)` binds `p`, never `to`. The grammar spells
    both with the field `name`, so a single field lookup binds the label."""
    got = _binds("func fly(to p: Pointer, _ n: Int) {}\n")
    assert got["p"] == "Pointer" and got["n"] == "Int"
    assert "to" not in got and "_" not in got


def test_swift_decoration_comes_off_a_type():
    got = _binds(
        "struct S {\n"
        "    var many: [Row] = []\n"
        "    var maybe: Pointer?\n"
        "    var byKey: [String: Row] = [:]\n"
        "}\n")
    assert got["many"] == "Row"       # a container names its content
    assert got["maybe"] == "Pointer"  # an optional is still that type
    assert got["byKey"] == "Row"      # a dictionary by its value


# ── acts ────────────────────────────────────────────────────────────────

def _acts(src):
    from tree_sitter_language_pack import get_parser

    from montology_scan.acts import CALL_SHAPES, _parts

    shape = CALL_SHAPES["swift"]
    tree = get_parser("swift").parse(src.encode())
    out = []

    def walk(n):
        if n.type == shape["node"]:
            out.append(_parts(n, shape))
        for c in n.named_children:
            walk(c)

    walk(tree.root_node)
    return out


def test_a_swift_call_is_a_noun_a_verb_and_a_noun():
    got = _acts("func f() {\n"
                "    engram.store(mention)\n"
                "    ledger.append(row, at: index)\n"
                "}\n")
    assert ("engram", "store", ["mention"]) in got
    # a labelled argument names a thing exactly as a bare one does
    assert ("ledger", "append", ["row", "index"]) in got


def test_one_step_through_self_still_names_the_concept():
    got = _acts("func f() { self.harness.fly(pointer) }\n")
    assert ("harness", "fly", ["pointer"]) in got


def test_a_receiver_that_is_an_expression_names_nothing():
    """`Path(file).resolve()` has a receiver that is a call. An expression is
    not a concept, and recording one would invent an edge."""
    got = _acts("func f() { Path(file).resolve() }\n")
    assert all(recv is None for recv, _verb, _args in got)


# ── migration ───────────────────────────────────────────────────────────

def test_a_swift_rename_sweeps_by_token(repo):
    """The regression this file exists for: `simple_identifier` was missing
    from the sweep's identifier set, so migrate reported a Swift tree as
    already clean while every function and property still said the old word."""
    from montology_scan.rename import migrate

    (repo / "Sources" / "Rename.swift").write_text(
        'struct Pointer {}\n'
        'func hold(p: Pointer) -> Pointer { p }\n'
        'let pointer = "pointer in a string is untouchable"\n'
    )
    report = migrate("pointer", "cursor", root=repo)
    assert "already clean" not in report
    assert "Rename.swift" in report

    migrate("pointer", "cursor", apply=True, root=repo)
    text = (repo / "Sources" / "Rename.swift").read_text()
    assert "struct Cursor {}" in text
    assert "func hold(p: Cursor) -> Cursor" in text
    assert "let cursor =" in text
    # a string is not code: the sweep is by token, and never touches one
    assert '"pointer in a string is untouchable"' in text
