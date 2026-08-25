"""A proposal: a pull request for meaning.

The ontology is a SQLite file, so git shows a vocabulary change as a binary
blob. A proposal stores INTENTS instead — readable as a diff of MEANING, and
replayed through the same functions a person at a terminal uses.
"""

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text(
        'name = "t"\n[scan]\ncollisions = "enforce"\n')
    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    return tmp_path


def open_one(ws, *changes, title="a change"):
    from montology_ontology import propose, proposals

    propose(title, list(changes))
    return proposals("open")[0]["id"]


WORD = {"intent": "word.add",
        "fields": {"name": "dossier", "definition": "what a run hands back",
                   "kind": "core", "pos": "noun"}}
CELL = {"intent": "word.add",
        "fields": {"name": "cell", "definition": "the box a run executes in",
                   "kind": "core", "pos": "noun"}}


def test_a_proposal_stores_intents_not_a_second_vocabulary(ws):
    """Replaying them on merge goes through the same functions the CLI uses, so
    an approved proposal can do nothing a CLI user could not."""
    from montology_ontology import changes

    pid = open_one(ws, WORD)
    got = changes(pid)
    assert len(got) == 1
    assert got[0]["intent"] == "word.add"
    assert got[0]["fields"]["name"] == "dossier"     # readable as MEANING
    assert got[0]["verdict"] is None


def test_an_unknown_intent_never_becomes_a_proposal(ws):
    from montology_ontology import propose

    got = propose("bad", [{"intent": "word.delete", "fields": {}}])
    assert got.startswith("REFUSED") and "word.delete" in got


def test_a_proposal_with_no_changes_is_a_note(ws):
    from montology_ontology import propose

    assert "doctrine" in propose("thoughts", [])


def test_merge_is_refused_while_anything_is_undecided(ws):
    from montology_ontology import merge

    pid = open_one(ws, WORD)
    got = merge(pid)
    assert got.startswith("REFUSED") and "undecided" in got and "#0" in got
    assert "monty onto decide" in got


def test_the_preview_runs_the_real_gate_against_the_merged_world(ws):
    """The verdict a reviewer needs is not 'does this parse' but 'what does this
    BREAK'. Nothing here may touch the real database."""
    from montology_ontology import preview, words

    (ws / "src" / "app.py").write_text("class Cell:\n    pass\n")
    pid = open_one(ws, CELL)

    seen = preview(pid)
    assert seen["ok"] is False
    assert any("collides with the word 'cell'" in line for line in seen["blocking"])
    assert {w["name"] for w in words()} == {"run"}    # the real db is untouched


def test_only_a_fail_stops_a_merge_but_everything_new_is_shown(ws):
    """Most workspaces run collisions advisory, and 'this collides with forty
    declarations' is exactly the thing to know before approving even where it
    does not break the build."""
    from montology_ontology import preview

    (ws / ".monty" / "montology.toml").write_text('name = "t"\n[scan]\n')  # advisory
    (ws / "src" / "app.py").write_text("class Cell:\n    pass\n")
    pid = open_one(ws, CELL)

    seen = preview(pid)
    assert seen["ok"] is True                     # advisory: it may merge
    assert seen["blocking"] == []
    assert any("collides" in line for line in seen["new"])   # …but it is SHOWN


def test_merge_is_refused_while_the_gate_would_fail(ws):
    from montology_ontology import decide, merge, words

    (ws / "src" / "app.py").write_text("class Cell:\n    pass\n")
    pid = open_one(ws, CELL)
    decide(pid, 0, "approved")

    got = merge(pid)
    assert got.startswith("REFUSED") and "gate would fail" in got
    assert {w["name"] for w in words()} == {"run"}


def test_one_bad_change_does_not_sink_a_good_one(ws):
    """A proposal that bundles a good rename with a bad definition should not
    have to be rejected whole."""
    from montology_ontology import decide, merge, words

    (ws / "src" / "app.py").write_text("class Cell:\n    pass\n")
    pid = open_one(ws, WORD, CELL)
    decide(pid, 0, "approved")
    decide(pid, 1, "rejected", "except the class or rename it first")

    got = merge(pid)
    assert got.startswith("merged")
    assert {w["name"] for w in words()} == {"run", "dossier"}


def test_a_merged_proposal_cannot_merge_twice(ws):
    from montology_ontology import decide, merge

    pid = open_one(ws, WORD)
    decide(pid, 0, "approved")
    assert merge(pid).startswith("merged")
    assert "already merged" in merge(pid)


def test_rejecting_everything_is_a_close_not_a_merge(ws):
    from montology_ontology import decide, merge

    pid = open_one(ws, WORD)
    decide(pid, 0, "rejected")
    got = merge(pid)
    assert got.startswith("REFUSED") and "monty onto close" in got


def test_a_verdict_is_one_of_two_words(ws):
    from montology_ontology import decide

    pid = open_one(ws, WORD)
    assert decide(pid, 0, "maybe").startswith("REFUSED")
    assert decide(pid, 9, "approved").startswith("REFUSED")   # no such change


def test_the_canvas_draws_a_proposal_as_ghosts(ws):
    """Drawn OVER the live graph, because the question a reviewer is asking is
    'what would this vocabulary look like'."""
    from montology_canvas import graph

    pid = open_one(ws, CELL,
                   {"intent": "ruling.overload",
                    "fields": {"dont_say": "sandbox", "say": "cell", "why": "one word"}})

    g = graph(with_scan=False, proposal=pid)
    ghosts = [n for n in g["nodes"] if n["data"].get("proposed")]
    assert {n["id"] for n in ghosts} == {"word:cell", "term:sandbox"}
    assert all(n["data"]["verdict"] is None for n in ghosts)
    assert any(e["data"].get("proposed") and e["kind"] == "overloaded" for e in g["edges"])
    # nothing proposed may be mistaken for something the database holds
    assert not [n for n in g["nodes"] if n["id"] == "word:run" and n["data"].get("proposed")]
