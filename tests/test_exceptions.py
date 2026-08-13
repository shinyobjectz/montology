"""Judging a collision: part of speech, the exception, and the one law an
exception may never silence.

The fixture is the case that produced this feature, reduced: a value-typed
word (`name`) declared as two different values in two modules, and a verb
(`open`) doing ordinary work in several. Eighteen advisories on the real
tree came down to one genuine finding, and it was the value type.
"""

import pytest


@pytest.fixture()
def repo(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "store.ex").write_text(
        "defmodule Store do\n  def open(name, opts), do: {:ok, []}\nend\n")
    (tmp_path / "lib" / "ledger.ex").write_text(
        "defmodule Ledger do\n  @type name :: term()\n"
        "  def open(name, opts \\\\ []), do: {:ok, name}\nend\n")
    (tmp_path / "lib" / "snapshot.ex").write_text(
        "defmodule Snapshot do\n"
        "  @type name :: %{Ledger.ref() => non_neg_integer()}\n"
        "  def name(%__MODULE__{at: at}), do: at\nend\n")
    (tmp_path / "surface").mkdir()
    (tmp_path / "surface" / "controller.ex").write_text(
        "defmodule Controller do\n  def open(conn, params), do: conn\nend\n")
    return tmp_path


@pytest.fixture()
def vocab(onto_db):
    onto_db.add("open", "naming the ledgers to read, and being given a snapshot",
                kind="core", pos="verb")
    onto_db.add("name", "the transaction each of a snapshot's ledgers was read at",
                kind="core", pos="value")
    return onto_db


# ── part of speech: a dimension of the word, not of the exception ─────────

def test_pos_is_recorded_and_validated(onto_db):
    assert "REFUSED" in onto_db.add("thing", "a thing", pos="gerund")
    assert onto_db.add("open", "an operation", pos="verb").startswith("added")
    assert [w["pos"] for w in onto_db.words()] == ["verb"]


def test_a_word_without_pos_says_so(onto_db):
    got = onto_db.add("ledger", "the append-only sequence")
    assert "no part of speech" in got and "--pos" in got


def test_pos_is_amendable_and_ledgered(onto_db):
    onto_db.add("ledger", "the append-only sequence", kind="core")
    got = onto_db.amend("ledger", pos="noun", why="it names a thing")
    assert got.startswith("amended") and "pos" in got
    assert [a["field"] for a in onto_db.amendments("ledger")] == ["pos"]
    assert "REFUSED" in onto_db.amend("ledger", pos="adverb")


# ── the exception: a reason, a scope, and a ledger row ────────────────────

def test_an_exception_needs_its_why(onto_db, vocab):
    got = onto_db.except_add("open", "   ")
    assert got.startswith("REFUSED") and "reasonless" in got


def test_an_exception_needs_a_part_of_speech(onto_db):
    onto_db.add("ledger", "the append-only sequence", kind="core")
    got = onto_db.except_add("ledger", "the module is the ledger")
    assert got.startswith("REFUSED") and "no part of speech" in got
    assert "monty onto amend ledger --pos" in got


def test_an_exception_on_a_non_word_is_refused(onto_db):
    got = onto_db.except_add("nothing", "because")
    assert got.startswith("REFUSED") and "not a word" in got


def test_an_exception_is_recorded_with_its_reason(onto_db, vocab):
    got = onto_db.except_add("open", "ordinary work below the surface", scope="lib/**")
    assert got.startswith("excepted") and "verb" in got
    row = onto_db.exceptions("open")[0]
    assert row["scope"] == "lib/**" and row["judged"] == "verb"
    assert row["why"] == "ordinary work below the surface"
    assert row["checked"] == "unchecked"      # nothing declared `open` as a type


def test_a_tree_wide_exception_says_it_is_tree_wide(onto_db, vocab):
    got = onto_db.except_add("open", "everywhere")
    assert "tree-wide" in got and "BELOW the surface" in got
    assert onto_db.exceptions("open")[0]["scope"] == onto_db.TREE_WIDE


def test_the_exception_reaches_check_where_naming_happens(onto_db, vocab):
    onto_db.except_add("open", "ordinary below the surface", scope="lib/**")
    assert any("EXCEPTED" in f and "lib/**" in f for f in onto_db.check("open"))


# ── the value-type guard ─────────────────────────────────────────────────

def test_a_value_type_divergence_refuses_the_exception(repo, onto_db, vocab):
    from montology_scan import type_declarations

    types = [t for t in type_declarations(repo) if t["name"] == "name"]
    got = onto_db.except_add("name", "kept consistent on purpose", scope="lib/**",
                             types=types)
    assert got.startswith("REFUSED")
    assert "term()" in got and "non_neg_integer()" in got
    assert "pass one where the other is expected" in got
    assert not onto_db.exceptions("name")


def test_a_consistent_value_type_is_excepted_and_says_it_checked(repo, onto_db, vocab):
    from montology_scan import type_declarations

    (repo / "lib" / "snapshot.ex").write_text(
        "defmodule Snapshot do\n  @type name :: term()\n"
        "  def name(%__MODULE__{at: at}), do: at\nend\n")
    types = [t for t in type_declarations(repo) if t["name"] == "name"]
    got = onto_db.except_add("name", "one value, one name", scope="lib/**", types=types)
    assert got.startswith("excepted")
    assert onto_db.exceptions("name")[0]["checked"] == "consistent"


def test_a_noun_divergence_warns_but_is_granted(repo, onto_db):
    from montology_scan import type_declarations

    onto_db.add("name", "what a thing is called", kind="core", pos="noun")
    types = [t for t in type_declarations(repo) if t["name"] == "name"]
    got = onto_db.except_add("name", "two renderings of one thing", types=types)
    assert got.startswith("excepted") and "warn" in got
    assert onto_db.exceptions("name")[0]["checked"] == "diverged"


def test_divergence_fails_the_gate_no_matter_what_was_excepted(repo, onto_db, vocab):
    """The whole point. An exception recorded blind — or recorded while the
    code still agreed with itself — cannot suppress the divergence later."""
    from montology_scan import lint

    onto_db.except_add("name", "recorded before the second type existed", scope="lib/**")
    report = lint(repo)
    fails = [r for r in report if r.startswith("FAIL")]
    assert any("'name'" in f and "2 different values" in f for f in fails)
    assert any("No exception silences this" in f for f in fails)
    assert report[-1].startswith("FAIL")


def test_divergence_ignores_names_the_vocabulary_makes_no_claim_about(repo, onto_db):
    """Two modules declaring their own `option` type are two modules, not
    drift — without a word there is no claim to violate."""
    from montology_scan import divergence

    (repo / "lib" / "a.ex").write_text("defmodule A do\n  @type option :: :one\nend\n")
    (repo / "lib" / "b.ex").write_text("defmodule B do\n  @type option :: :two\nend\n")
    onto_db.add("option", "a choice", kind="core", pos="value")
    assert any("option" in d for d in divergence(repo))
    onto_db.amend("option", pos="", why="not actually a value type")
    assert divergence(repo) == []


# ── the gate: scope, coverage, and the repair ────────────────────────────

def test_an_exception_holds_only_where_it_says(repo, onto_db, vocab):
    from montology_scan import lint

    onto_db.except_add("open", "ordinary below the surface", scope="lib/**")
    warned = [r for r in lint(repo) if r.startswith("warn") and "'open'" in r]
    assert warned and all("surface/controller.ex" in w for w in warned)


def test_the_repair_speaks_the_case(repo, onto_db, vocab):
    from montology_scan import lint

    report = lint(repo)
    verb = next(r for r in report if "'open'" in r and r.startswith("warn"))
    assert "is a verb" in verb and "monty onto except open" in verb
    value = next(r for r in report if "function 'name'" in r)
    assert "is a value type" in value and "pass this function's value" in value


def test_an_unjudged_word_asks_for_its_pos_before_anything_else(repo, onto_db):
    from montology_scan import lint

    onto_db.add("open", "naming the ledgers to read", kind="core")
    warned = next(r for r in lint(repo) if "'open'" in r)
    assert "has no part of speech" in warned and "--pos verb|noun|value" in warned


def test_every_exception_is_shown_and_a_stale_one_is_named(repo, onto_db, vocab):
    from montology_scan import lint

    onto_db.except_add("open", "ordinary below the surface", scope="lib/**")
    onto_db.except_add("name", "nothing is declared here", scope="vendor/**")
    report = lint(repo)
    assert any("note except 'open' (verb) covers 7 declaration(s)" not in r for r in report)
    assert any(r.startswith("note except 'open'") and "covers" in r for r in report)
    assert any(r.startswith("note except 'name'") and "may be stale" in r for r in report)


def test_the_old_allow_list_is_honoured_and_reported(repo, onto_db, vocab):
    from montology_scan import except_drafts, lint

    (repo / ".monty" / "montology.toml").write_text(
        'name = "t"\n[scan]\nallow = ["open"]\n')
    report = lint(repo)
    assert not [r for r in report if r.startswith("warn") and "'open'" in r]
    assert any("still live in montology.toml" in r for r in report)
    drafts = except_drafts(repo)
    assert [d["word"] for d in drafts] == ["open"] and drafts[0]["pos"] == "verb"


# ── the firewall agrees with the gate ─────────────────────────────────────

def test_the_guard_honours_a_recorded_exception(tmp_path, onto_db, monkeypatch):
    from montology_scan.guard import check_text

    # the guard reads the db by its place in the workspace, not by DB_PATH
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    monkeypatch.setattr(onto_db, "DB_PATH", tmp_path / ".monty" / "ontology.db")
    onto_db.add("open", "naming the ledgers to read", kind="core", pos="verb")
    repo = tmp_path
    (repo / ".monty" / "montology.toml").write_text(
        'name = "t"\n[scan]\ncollisions = "enforce"\n')
    text = "defmodule Keyring do\n  def open(opts), do: opts\nend\n"
    blocking, _ = check_text(repo, str(repo / "lib" / "keyring.ex"), text)
    assert any("collides" in b for b in blocking)

    onto_db.except_add("open", "ordinary below the surface", scope="lib/**")
    blocking, _ = check_text(repo, str(repo / "lib" / "keyring.ex"), text)
    assert not blocking
    # ...and only there: the scope binds the firewall exactly as it binds the gate
    blocking, _ = check_text(repo, str(repo / "surface" / "controller.ex"), text)
    assert any("collides" in b for b in blocking)


# ── the measurement the guard stands on ──────────────────────────────────

def test_type_declarations_pair_each_name_with_what_it_holds(repo):
    from montology_scan import type_declarations

    (repo / "t.ts").write_text("type Name = { a: string };\ninterface Held { id: string }\n")
    rows = {(r["name"], r["value"]) for r in type_declarations(repo)}
    assert ("name", "term()") in rows
    assert ("name", "%{Ledger.ref() => non_neg_integer()}") in rows
    assert ("Name", "{ a: string }") in rows
    assert ("Held", "{ id: string }") in rows
