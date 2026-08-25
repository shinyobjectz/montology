"""The graph: every edge montology holds, drawn once, measured not guessed."""

from collections import Counter

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def kinds(items):
    return Counter(i["kind"] for i in items)


def test_the_vocabulary_alone_is_nodes_and_edges(ws, onto_db):
    from montology_canvas import graph

    onto_db.add("scan", "the tree-sitter sweep of a codebase", kind="core",
                code="scan", pos="noun")
    onto_db.add("candidate", "a recurring declared name with no word", kind="core",
                owner="scan", code="scan.candidate", pos="noun")

    g = graph(with_scan=False)
    assert kinds(g["nodes"])["word"] == 2
    assert kinds(g["edges"])["contains"] == 1
    assert g["stats"]["words"] == 2
    assert len(g["fingerprint"]) == 16


def test_a_retired_name_becomes_a_term_pointing_at_the_word(ws, onto_db):
    """The history of a vocabulary IS the names it stopped using — a graph that
    draws only live words cannot draw a decision."""
    from montology_canvas import graph

    onto_db.add("errand", "one unit of work", kind="core", pos="noun")
    onto_db.rename_word("errand", "task", "one word for the unit of work")
    onto_db.rule("user", "person", "they are people")

    g = graph(with_scan=False)
    by_id = {n["id"]: n for n in g["nodes"]}
    assert by_id["term:errand"]["kind"] == "term"
    assert by_id["term:user"]["kind"] == "term"
    assert "word:task" in by_id and "term:task" not in by_id   # live words stay words

    e = {x["kind"]: x for x in g["edges"]}
    assert e["renamed"]["source"] == "term:errand" and e["renamed"]["target"] == "word:task"
    assert e["overloaded"]["source"] == "term:user"
    assert e["renamed"]["data"]["gates"] is True     # the guard always blocks a retired name


def test_a_route_that_cannot_gate_says_so(ws, onto_db):
    """qubie had one: `intelligence -> brain` at register 'all' with no scope.
    A ruling that cannot be scoped can never gate, and a canvas that draws it
    the same as an enforced one is lying about which decisions have teeth."""
    from montology_canvas import graph
    from montology_ontology import route_add

    onto_db.add("brain", "the model that answers", kind="core", pos="noun")
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    route_add("intelligence", "brain", register="all")
    route_add("sandbox", "cell", register="code", scope="src/**")

    routes = {e["source"]: e for e in graph(with_scan=False)["edges"]
              if e["kind"] == "routes"}
    assert routes["term:intelligence"]["data"]["gates"] is False
    assert routes["term:sandbox"]["data"]["gates"] is True
    assert routes["term:sandbox"]["label"] == "code"       # the register IS the label


def test_a_ruling_is_a_node_because_it_carries_a_why(ws, onto_db):
    from montology_canvas import graph

    onto_db.add("artifact", "what a run produces", kind="core", pos="noun")
    onto_db.collide("artifact", "mellea", "a file out of the sandbox",
                    "WE MOVED — ours became dossier")

    g = graph(with_scan=False)
    ruling = next(n for n in g["nodes"] if n["kind"] == "ruling")
    assert ruling["data"]["ruling_kind"] == "collision"
    assert "WE MOVED" in ruling["data"]["ruling"]
    assert ruling["data"]["their_meaning"]                  # an edge label holds neither
    assert any(e["kind"] == "rules" and e["target"] == "word:artifact" for e in g["edges"])


def test_the_code_counts_are_collisions_not_resolutions(ws, onto_db):
    """The obvious reading is backwards: a declaration named after an enforced
    word is a COLLISION. Code answers to a word through a bearing, never by
    wearing its name."""
    from montology_canvas import graph

    (ws / "src").mkdir()
    (ws / "src" / "thing.py").write_text("class Cell:\n    pass\n\ndef helper():\n    pass\n")
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")

    word = next(n for n in graph()["nodes"] if n["id"] == "word:cell")
    assert word["data"]["collides"] == 1
    assert word["data"]["excepted"] == 0
    assert word["data"]["at"] == ["src/thing.py:1"]         # the PLACE, not just a count


def test_an_exception_moves_a_collision_into_excepted(ws, onto_db):
    from montology_canvas import graph
    from montology_ontology import except_add

    (ws / "src").mkdir()
    (ws / "src" / "thing.py").write_text("class Cell:\n    pass\n")
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    except_add("cell", "the class IS the cell — the surface being literal", scope="src/**")

    word = next(n for n in graph()["nodes"] if n["id"] == "word:cell")
    assert (word["data"]["collides"], word["data"]["excepted"]) == (0, 1)


def test_a_candidate_is_marked_as_the_suggestion_it_is(ws, onto_db):
    """An instrument that hands back a guess dressed as a fact is worse than
    one that says nothing."""
    from montology_canvas import graph

    (ws / "src").mkdir()
    body = "\n\n".join(f"def compressor_{i}():\n    pass" for i in range(3))
    (ws / "src" / "a.py").write_text("class Compressor:\n    pass\n\n" + body)
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")

    cands = [n for n in graph()["nodes"] if n["kind"] == "candidate"]
    assert cands and all(c["data"]["suggested"] is True for c in cands)


def test_the_fingerprint_moves_only_when_the_graph_does(ws, onto_db):
    from montology_canvas import graph

    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    first = graph(with_scan=False)["fingerprint"]
    assert graph(with_scan=False)["fingerprint"] == first     # deterministic
    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    assert graph(with_scan=False)["fingerprint"] != first
