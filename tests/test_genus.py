"""The genus: the one structural relation that changes what the gate knows.

Named `genus` and not `kind-of` because `kind` already means provenance here,
and one root meaning two things is the failure the vocabulary exists to prevent.
"""

import pytest


@pytest.fixture()
def vocab(onto_db):
    onto_db.add("person", "a human being the system acts for", kind="core", pos="noun")
    onto_db.add("student", "someone enrolled on a course", kind="core", pos="noun")
    onto_db.add("reviewer", "someone who approves a proposal", kind="core", pos="noun")
    return onto_db


def test_a_genus_needs_two_words_that_exist(vocab):
    """Unlike a route — which may point at a word that does not exist yet,
    because a ledger must describe a decision taken before its target landed —
    a genus asserts something about two things that must both be here."""
    from montology_ontology import genus_add

    got = genus_add("student", "mammal")
    assert got.startswith("REFUSED") and "not a word" in got and "monty onto add" in got
    assert genus_add("student", "person").startswith("genus")


def test_a_word_is_not_a_kind_of_itself(vocab):
    from montology_ontology import genus_add

    assert "cannot be a kind of itself" in genus_add("person", "person")


def test_a_cycle_is_refused_with_the_path_shown(vocab):
    from montology_ontology import genus_add

    genus_add("student", "person")
    genus_add("reviewer", "student")
    got = genus_add("person", "reviewer")
    assert got.startswith("REFUSED") and "cycle" in got
    assert "reviewer → student → person" in got      # the path, not just the verdict


def test_ontoclean_catches_the_classic_error(vocab):
    """`person kind-of student` — every student is a person, but a person is
    not a kind of student, because they stop. Mechanically catchable once the
    words carry rigidity, and the only OntoClean metaproperty we keep."""
    from montology_ontology import genus_add, rigidity_set

    rigidity_set("person", "rigid")
    rigidity_set("student", "anti-rigid")

    got = genus_add("person", "student")
    assert got.startswith("REFUSED") and "rigid" in got and "anti-rigid" in got
    assert "not the other way round" in got
    assert genus_add("student", "person").startswith("genus")   # this way is fine


def test_rigidity_only_takes_the_two_values(vocab):
    from montology_ontology import rigidity_set

    assert rigidity_set("person", "sort-of").startswith("REFUSED")
    assert rigidity_set("nobody", "rigid").startswith("REFUSED")   # not a word
    assert rigidity_set("person", "rigid") == "judged  person is rigid"


def test_containment_is_not_subsumption(vocab):
    """`scan.collision` lives inside `scan` and is NOT a kind of scan. Saying
    both is usually containment mistaken for subsumption, so it is noted."""
    from montology_ontology import genus_add

    vocab.add("wing", "part of a bird", kind="core", owner="person", pos="noun")
    got = genus_add("wing", "person")
    assert got.startswith("genus") and "also" in got and "owner" in got
    assert "where a word LIVES" in got and "what it IS" in got


def test_a_word_may_be_a_kind_of_more_than_one_thing(vocab):
    """Composition over deep hierarchies — Palantir's own principle, and the
    reason this is a table rather than a column."""
    from montology_ontology import genus_add, genus_chain

    vocab.add("agent", "something that acts", kind="core", pos="noun")
    genus_add("student", "person")
    genus_add("student", "agent")
    assert sorted(genus_chain("student")) == ["agent", "person"]


def test_rulings_are_inherited_and_say_where_from(vocab):
    """This is what makes the genus worth having: it is not decoration on a
    diagram, it changes what the gate knows. An inherited ruling that is
    invisible is a trap."""
    from montology_ontology import genus_add, inherited

    vocab.rule("human", "person", "one word for it")
    genus_add("student", "person")
    got = inherited("student")
    assert len(got) == 1
    assert got[0]["from"] == "person" and got[0]["kind"] == "overload"
    assert "human" in got[0]["detail"]
    assert inherited("person") == []          # a word does not inherit its own


def test_a_database_written_before_the_genus_simply_has_none(tmp_path, monkeypatch):
    """A read-only connection cannot migrate, and crashing a reader over a
    table the writer will create is a worse answer than an empty list."""
    import sqlite3

    from montology_ontology import db as odb

    old = tmp_path / "old.db"
    sqlite3.connect(old).executescript(
        "CREATE TABLE word (name TEXT PRIMARY KEY, kind TEXT, definition TEXT);")
    monkeypatch.setattr(odb, "DB_PATH", old)
    assert odb.genera() == [] and odb.genus_chain("anything") == []
