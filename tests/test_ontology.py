"""The vocabulary contract: check-first, one meaning, codes resolve."""


def test_check_first_refuses_taken_names(onto_db):
    assert onto_db.add("thread", "a stateful session").startswith("added")
    got = onto_db.add("Thread", "something else entirely")
    assert got.startswith("REFUSED") and "one word means one thing" in got


def test_codes_are_a_tree(onto_db):
    assert "REFUSED" in onto_db.add("cell", "the sandbox", code="har.cell")  # no prefix word
    onto_db.add("harness", "the loop", code="har")
    assert onto_db.add("cell", "the sandbox", code="har.cell").startswith("added")
    assert "already belongs" in onto_db.add("cage", "another sandbox", code="har.cell")
    assert "dotted-lowercase" in onto_db.add("bad", "x", code="Har.Cell")


def test_owner_must_exist(onto_db):
    got = onto_db.add("plan", "a proposal", owner="harness")
    assert got.startswith("REFUSED") and "owner" in got


def test_rulings_surface_in_check(onto_db):
    onto_db.rule("sandbox", "cell", "one word for it")
    findings = onto_db.check("sandbox")
    assert any("RULED" in f and "cell" in f for f in findings)


def test_empty_db_is_all_free(onto_db):
    assert onto_db.check("anything") == []
    assert onto_db.words() == []
