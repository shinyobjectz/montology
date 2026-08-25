"""Competency questions: the requirements a vocabulary is answerable to.

The practice both vendors underplay, and the direction neither ships: a word no
question motivates is how a glossary grows into something nobody reads.
"""

import pytest


@pytest.fixture()
def vocab(onto_db):
    onto_db.add("order", "what a customer asked for", kind="core", pos="noun")
    onto_db.add("carrier", "who moves the goods", kind="core", pos="noun")
    return onto_db


def test_a_question_is_a_question_not_a_topic(vocab):
    from montology_ontology import ask

    assert ask("orders").startswith("REFUSED")
    assert ask("Which carrier shipped this order?").startswith("asked")


def test_asking_the_same_thing_twice_is_asking_it_once(vocab):
    """Running the intake again, or a second round, must not make two
    questions out of one."""
    from montology_ontology import ask, questions

    ask("Which carrier shipped this order?")
    got = ask("  which  Carrier   shipped this order? ")   # same question, typed again
    assert got.startswith("already asked")
    assert len(questions()) == 1


def test_a_question_is_answered_by_words_that_exist(vocab):
    from montology_ontology import answer, ask, questions

    ask("Which carrier shipped this order?", answered_by=["order", "carrier"])
    q = questions()[0]
    assert q["answered_by"] == ["carrier", "order"]
    assert answer(q["id"], "freight").startswith("REFUSED")     # not a word
    assert answer("nope", "order").startswith("REFUSED")        # not a question


def test_coverage_runs_both_ways(vocab):
    from montology_ontology import ask, coverage

    ask("Which carrier shipped this order?", answered_by=["order"])
    ask("What did it cost to ship?")

    cov = coverage()
    assert [q["text"] for q in cov["unanswered"]] == ["What did it cost to ship?"]
    assert cov["unmotivated"] == ["carrier"]   # a word nobody asked for


def test_with_no_questions_it_says_so_rather_than_flagging_every_word(vocab):
    """Every word is unmotivated when nothing has been asked — which is a fact
    about the questions, not about the words."""
    from montology_ontology import coverage

    cov = coverage()
    assert cov["unmotivated"] == [] and cov["unanswered"] == []
    assert "no competency questions recorded" in cov["note"]


def test_harvest_proposes_and_never_writes(vocab):
    """The same rule gen follows: only a person can say whether that was the
    question they meant."""
    from montology_ontology import harvest, questions

    drafts = harvest({"central_things": "Order, Shipment and Carrier",
                      "banned_words": "we say workspace, never project"})
    texts = [d["text"] for d in drafts]
    assert any("order" in t for t in texts) and any("shipment" in t for t in texts)
    assert any("decided not to use" in t for t in texts)
    assert questions() == []                    # proposed, not written


def test_harvest_ignores_what_names_nothing(vocab):
    from montology_ontology import harvest

    drafts = harvest({"central_things": "the, and, a, it"})
    assert drafts == []


def test_the_canvas_shows_an_unanswered_question(vocab, tmp_path, monkeypatch):
    from montology_canvas import graph

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()

    from montology_ontology import ask

    ask("Which carrier shipped this order?", answered_by=["order"])
    ask("What did it cost to ship?")

    g = graph(with_scan=False)
    qs = {n["label"][:20]: n for n in g["nodes"] if n["kind"] == "question"}
    assert len(qs) == 2
    assert any(n["data"]["unanswered"] for n in qs.values())
    assert any(e["kind"] == "answers" and e["target"] == "word:order" for e in g["edges"])
