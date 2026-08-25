"""Acts: what the code DOES, as against what it declares.

The scan measured only declarations, which is the noun side — and it is why a
montology vocabulary comes out about ninety percent nouns. montology's own is
30 nouns to 1 verb; qubie's is 100 to 9.
"""

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "src").mkdir()
    return tmp_path


def test_an_act_is_a_subject_a_verb_and_an_object(ws, onto_db):
    from montology_scan.acts import acts

    (ws / "src" / "run.py").write_text(
        "class Tour:\n"
        "    def walk(self):\n"
        "        pointer.fly(3)\n"
        "        pointer.hide()\n"
    )
    got = acts()["acts"]
    assert {(a["subject"], a["verb"], a["object"]) for a in got} == {
        ("walk", "fly", "pointer"), ("walk", "hide", "pointer")}
    assert all(a["file"] == "src/run.py" for a in got)      # a place, always


def test_only_acts_on_what_the_vocabulary_names_count(ws, onto_db):
    """The discriminator is montology's own thesis: an act is domain vocabulary
    when the thing it acts ON is something we name. Without this the list came
    back `time`, `sleep`, `monotonic`, `expanduser` — the standard library,
    which says nothing about what the system is."""
    from montology_scan.acts import domain_acts

    (ws / "src" / "run.py").write_text(
        "def walk():\n"
        "    pointer.fly(3)\n"
        "    time.sleep(1)\n"
        "    os.path.expanduser('~')\n"
    )
    onto_db.add("pointer", "the thing on screen the person is looking at",
                kind="core", pos="noun")
    got = domain_acts()
    assert [(a["verb"], a["object"]) for a in got] == [("fly", "pointer")]


def test_a_word_made_to_do_things_nobody_named(ws, onto_db):
    """qubie's `pointer`: flown, hidden, attached, hardened and destroyed, and
    the vocabulary names none of it."""
    from montology_scan.acts import unnamed_verbs

    (ws / "src" / "run.py").write_text(
        "def walk():\n"
        "    pointer.fly(1)\n    pointer.hide()\n    pointer.harden()\n"
        "    pointer.dwell()\n"
    )
    onto_db.add("pointer", "what the person is looking at", kind="core", pos="noun")
    onto_db.add("dwell", "to rest on a thing long enough to mean it",
                kind="core", pos="verb")

    rows = unnamed_verbs()
    assert len(rows) == 1
    row = rows[0]
    assert row["word"] == "pointer"
    assert row["unnamed"] == ["fly", "harden", "hide"]
    assert row["named"] == ["dwell"]              # what IS named is shown too
    assert row["at"]["fly"][0].endswith("src/run.py:2")


def test_plumbing_is_not_vocabulary(ws, onto_db):
    """A codebase performs `append` and `get` constantly and none of it is
    domain vocabulary."""
    from montology_scan.acts import unnamed_verbs

    (ws / "src" / "run.py").write_text(
        "def walk():\n    trail.append(1)\n    trail.get(2)\n    trail.strip()\n")
    onto_db.add("trail", "the record of where the person has been",
                kind="core", pos="noun")
    assert unnamed_verbs() == []


def test_a_language_with_no_query_is_skipped_and_said_to_be(ws, onto_db):
    from montology_scan.acts import acts

    (ws / "src" / "m.swift").write_text("class Thing { }")
    got = acts()
    assert "swift" in got["skipped"]               # silence would read as covered


def test_the_graph_carries_what_a_word_is_made_to_do(ws, onto_db):
    from montology_canvas import graph

    (ws / "src" / "run.py").write_text(
        "class Tour:\n    def walk(self):\n        pointer.fly(1)\n        pointer.hide()\n")
    onto_db.add("pointer", "what the person is looking at", kind="core", pos="noun")
    onto_db.add("tour", "a walk through the system", kind="core", pos="noun")

    g = graph()
    node = next(n for n in g["nodes"] if n["id"] == "word:pointer")
    assert node["data"]["verbs_unnamed"] == ["fly", "hide"]
    assert g["stats"]["unnamed_verbs"] == 2


def test_an_act_between_two_words_is_an_edge(ws, onto_db):
    """qubie has seven, and they read as a sentence about the system:
    a tour flies, hides, hardens, destroys and dwells a pointer."""
    from montology_canvas import graph

    (ws / "src" / "run.py").write_text(
        "class tour:\n    def go(self):\n        pass\n\ndef tour_step():\n    pointer.fly(1)\n")
    (ws / "src" / "b.py").write_text("def tour():\n    pointer.hide()\n")
    onto_db.add("pointer", "what the person is looking at", kind="core", pos="noun")
    onto_db.add("tour", "a walk through the system", kind="core", pos="noun")

    acts_ = [e for e in graph()["edges"] if e["kind"] == "act"]
    assert acts_ and all(e["source"] == "word:tour" for e in acts_)
    assert {e["data"]["verb"] for e in acts_} == {"hide"}
    assert acts_[0]["data"]["defined"] is False
