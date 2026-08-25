"""The anti-pattern catalogue: named, evidenced, and never a build failure.

Every threshold in here was calibrated by running it against two real
vocabularies, not by reasoning about it. The comments say what was measured.
"""

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "src").mkdir()
    return tmp_path


def patterns(r):
    return {f["pattern"] for f in r["findings"]}


def only(r, pattern):
    return [f for f in r["findings"] if f["pattern"] == pattern]


def test_a_vendor_in_a_definition_is_a_kitchen_sink(ws, onto_db):
    """Found in montology's OWN seed the first time this ran: the word `scan`
    was defined as 'the tree-sitter sweep of a codebase'. The word laws only
    ever checked GENERATED definitions, so a seeded one walked past them."""
    from montology_scan import review

    onto_db.add("pipeline", "a run of jobs orchestrated through github actions",
                kind="core", pos="noun")
    got = only(review(), "The Kitchen Sink")
    assert got and got[0]["verdict"] == "proof"
    assert "github" in got[0]["evidence"]


def test_a_vague_name_is_a_misnomer(ws, onto_db):
    from montology_scan import review

    onto_db.add("manager", "the thing that runs the other things", kind="core", pos="noun")
    got = only(review(), "The Misnomer")
    assert got and got[0]["verdict"] == "heuristic"


def test_circularity_counts_only_in_the_genus_position(ws, onto_db):
    """montology's `edge` closes with 'an edge nothing can check is a drawing'
    — the sentence earning its keep, not begging the question. Counting the
    whole definition flagged 46 of qubie's 99 words."""
    from montology_scan import review

    onto_db.add("permission", "permission to take an action that changes something",
                kind="core", pos="noun")
    onto_db.add("edge", "a relation between two things it names — an edge nothing "
                        "can check is a drawing", kind="core", pos="noun")
    got = {f["subject"] for f in only(review(), "The Misnomer")}
    assert "permission" in got and "edge" not in got


def test_a_short_name_is_not_a_finding(ws, onto_db):
    """qubie's `gap`, `leg`, `rig` and `tap` are ordinary words with real
    definitions. Length was a proxy for 'is this an initialism' and a bad one:
    it made a list that was three-quarters noise."""
    from montology_scan import review

    onto_db.add("gap", "the recorded span between dwells when nobody is attending",
                kind="core", pos="noun")
    assert not only(review(), "The Misnomer")


def test_a_version_in_a_name_is_a_time_machine(ws, onto_db):
    from montology_scan import review

    onto_db.add("session-v2", "the second kind of session", kind="core", pos="noun")
    got = only(review(), "The Time Machine")
    assert got and got[0]["verdict"] == "proof"
    assert "rename ledger" in got[0]["repair"]


def test_a_route_that_cannot_gate_is_a_toothless_ruling(ws, onto_db):
    """Not in anyone's catalogue, because no vendor models a register."""
    from montology_ontology import route_add
    from montology_scan import review

    onto_db.add("brain", "the part that is asked and answers", kind="core", pos="noun")
    route_add("intelligence", "brain", register="all")
    got = only(review(), "The Toothless Ruling")
    assert got and got[0]["verdict"] == "proof" and "--scope" in got[0]["repair"]


def test_one_name_across_unrelated_areas_is_a_god_object(ws, onto_db):
    from montology_scan import review

    for area in ("billing", "shipping", "auth"):
        (ws / area).mkdir()
        (ws / area / "m.py").write_text("class Record:\n    pass\n")
    onto_db.add("record", "one durable statement of what happened", kind="core", pos="noun")

    got = only(review(spread=3), "The God Object")
    assert got and got[0]["verdict"] == "heuristic"
    assert "3 unrelated areas" in got[0]["evidence"]


def test_what_is_not_checked_is_said_every_run(ws, onto_db):
    """A catalogue with silent omissions reads as one that looked and found
    nothing."""
    from montology_scan import render_review, review

    r = review()
    names = {n for n, _ in r["skipped"]}
    assert names == {"Department Silos", "Action Sprawl", "The Golden Hammer"}
    assert all(why for _, why in r["skipped"])
    lines = render_review(r)
    assert sum("not checked" in line for line in lines) == 3


def test_the_review_never_fails_a_build(ws, onto_db):
    """The gate is for facts. An anti-pattern is a judgement, and a judgement
    that fails a build is one people learn to route around."""
    from montology_scan import render_review, review

    onto_db.add("manager", "the thing that manages", kind="core", pos="noun")
    lines = render_review(review())
    assert not any(line.startswith("FAIL") for line in lines)
    assert any("advisory" in line for line in lines)


def test_a_path_still_carrying_a_retired_name(ws, onto_db):
    """Ours, and it took a real repo to see. qubie renamed q1 to reactive-layer
    and q2 to edge-layer and left the directories as `q1/` and `q2/` — so the
    vocabulary said one thing and the tree said another, and every act inside
    those folders resolved to a retired term and vanished."""
    from montology_scan import review

    (ws / "q2").mkdir()
    (ws / "q2" / "relay.py").write_text("class Relay:\n    pass\n")
    (ws / "q2" / "brain.py").write_text("class Brain:\n    pass\n")
    onto_db.add("q2", "the middle layer", kind="core", pos="noun")
    onto_db.rename_word("q2", "edge-layer", "layers are named for what they do")

    got = only(review(), "The Old Address")
    assert got and got[0]["verdict"] == "proof"
    assert "q2" in got[0]["subject"] and "edge-layer" in got[0]["subject"]
    assert "2 file(s)" in got[0]["evidence"]
    assert "q2/relay.py" in got[0]["evidence"]


def test_a_path_that_matches_the_new_name_is_not_a_finding(ws, onto_db):
    from montology_scan import review

    (ws / "edge-layer").mkdir()
    (ws / "edge-layer" / "relay.py").write_text("class Relay:\n    pass\n")
    onto_db.add("q2", "the middle layer", kind="core", pos="noun")
    onto_db.rename_word("q2", "edge-layer", "layers are named for what they do")
    assert not only(review(), "The Old Address")
