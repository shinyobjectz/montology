"""Semantic hearing, tested deterministically: the audit logic runs against
a FAKE embedder (meaning encoded by hand), so no download and no flake."""

import numpy as np
import pytest

from montology_ontology import semantics


@pytest.fixture()
def fake_embedder(monkeypatch):
    """Texts mentioning the same concept-key embed identically; every text
    gets a distinct orthogonal-ish base otherwise."""
    CONCEPTS = {"session": 0, "holding": 1, "sandbox": 2, "record": 3}

    def embed(texts):
        out = np.zeros((len(texts), 8))
        for i, t in enumerate(texts):
            low = t.lower()
            hit = next((v for k, v in CONCEPTS.items() if k in low), None)
            if hit is not None:
                out[i, hit] = 1.0
            else:
                out[i, 4 + (hash(low) % 4)] = 1.0
        return out

    monkeypatch.setattr(semantics, "EMBEDDER", embed)
    return embed


def test_two_words_one_meaning_is_heard(onto_db, fake_embedder):
    onto_db.add("thread", "a stateful session between user and agent", kind="core", pos="noun")
    onto_db.add("conversation", "the ongoing session a user holds", kind="core", pos="noun")
    onto_db.add("cell", "the network-blocked sandbox", kind="core", pos="noun")
    report = semantics.audit()
    assert "'conversation' ~ 'thread'" in report or "'thread' ~ 'conversation'" in report
    assert "two words, one meaning?" in report
    assert "cell" not in report.split("semantics:")[-1] or "misfiled" not in report


def test_local_double_of_inherited_word_is_flagged(onto_db, fake_embedder):
    conn = onto_db.connect()
    conn.execute("INSERT INTO word (name, kind, definition, origin) "
                 "VALUES ('thread','core','a stateful session','git@org')")
    conn.commit()
    onto_db.add("convo", "the user's session with the agent")
    report = semantics.audit()
    assert "doubles an inherited one" in report


def test_candidate_that_already_exists_is_mapped_not_minted(onto_db, fake_embedder):
    onto_db.add("holding", "one thing this org acquired as a holding", kind="core", pos="noun")
    report = semantics.audit(candidates=[{"name": "holdings", "count": 7}])
    assert "candidate 'holdings'" in report and "semantically 'holding'" in report


def test_similar_ranks_by_meaning(onto_db, fake_embedder):
    onto_db.add("thread", "a stateful session between user and agent", kind="core", pos="noun")
    onto_db.add("cell", "the network-blocked sandbox", kind="core", pos="noun")
    got = semantics.similar("the session a user keeps open")
    assert got.splitlines()[0].split()[1] == "thread"


def test_missing_extra_carries_repair(onto_db, monkeypatch):
    onto_db.add("thread", "a stateful session", kind="core", pos="noun")
    onto_db.add("cell", "the sandbox", kind="core", pos="noun")
    monkeypatch.setattr(semantics, "EMBEDDER", None)
    import builtins
    real_import = builtins.__import__

    def no_model2vec(name, *a, **k):
        if name == "model2vec":
            raise ImportError(name)
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_model2vec)
    assert "[semantics]" in semantics.audit()


@pytest.mark.integration
def test_potion_hears_real_meaning(onto_db):
    semantics.EMBEDDER = None
    onto_db.add("thread", "a stateful conversation session between a user and an agent", kind="core", pos="noun")
    onto_db.add("dialogue", "an ongoing conversational session a user holds with the agent", kind="core", pos="noun")
    onto_db.add("cell", "a network-blocked sandbox that executes untrusted code", kind="core", pos="noun")
    report = semantics.audit(dup_threshold=0.70)
    assert "dialogue" in report and "thread" in report
