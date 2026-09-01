"""GDScript (Godot 4), read the same way every other language is read.

A Godot project's vocabulary lives in `class_name` lines, signals and the
members scripts export — the names a designer says out loud. The grammar
puts every one of them under a `(name)` node, so the reader is small; the
cases below exist so that a future grammar bump that renames one of them is
a red test and not a silent "no declarations here".
"""

import pytest

SOURCE = """\
class_name Player
extends CharacterBody3D

signal died(cause: String)
const SPEED := 5.0
const MAX_HP: int = 10
var health: int = 10
@export var name_tag: String = "p"
var untyped = 3
enum State { IDLE, RUN }

class Inventory:
	var items: Array = []
	func add(i) -> void:
		pass

static func make() -> Player:
	return Player.new()

func _ready() -> void:
	pass
"""


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "game"\n')
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "player.gd").write_text(SOURCE)
    return tmp_path


def _decls(repo):
    from montology_scan.surface import declarations

    got = declarations(repo)
    assert got["errors"] == 0
    assert "gdscript" not in got["skipped_langs"], "a covered language must not be skipped"
    return {(d["kind"], d["name"]) for d in got["decls"]}


def test_gdscript_is_covered_at_all():
    from montology_scan import languages_covered

    assert "gdscript" in languages_covered()


def test_every_kind_gdscript_declares(repo):
    got = _decls(repo)
    assert ("class", "Player") in got, "class_name names the script's word"
    assert ("class", "Inventory") in got, "inner class"
    assert ("function", "make") in got, "static func"
    assert ("function", "_ready") in got
    assert ("function", "add") in got, "method inside an inner class"
    assert ("signal", "died") in got
    assert ("const", "SPEED") in got
    assert ("variable", "health") in got
    assert ("variable", "name_tag") in got, "@export var is still a var"
    assert ("enum", "State") in got


def test_extends_is_a_mention_not_a_declaration(repo):
    """`extends CharacterBody3D` uses the engine's word; counting it as a
    declaration would make every script look like it redefines its base."""
    got = _decls(repo)
    assert not any(name == "CharacterBody3D" for _, name in got)


def test_typed_members_are_type_declarations(repo):
    from montology_scan.surface import type_declarations

    rows = {r["name"]: r["value"] for r in type_declarations(repo)}
    assert rows["health"] == "int"
    assert rows["name_tag"] == "String"
    assert rows["MAX_HP"] == "int"
    assert "SPEED" not in rows, "inferred := says no type out loud"
    assert "untyped" not in rows
