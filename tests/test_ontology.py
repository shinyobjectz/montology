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


def test_collision_ruling_surfaces_in_check(onto_db):
    onto_db.collide("Artifact", "mellea",
                    "a file produced by code execution",
                    "WE MOVED — ours became Dossier; Artifact now means theirs only")
    findings = onto_db.check("artifact")
    assert any("COLLISION (mellea)" in f and "WE MOVED" in f for f in findings)


def test_rename_moves_the_row_and_retires_the_old_name(onto_db):
    onto_db.add("artifact", "what a task produces", kind="core")
    got = onto_db.rename_word("artifact", "dossier", "mellea's field name cannot be aliased")
    assert got.startswith("renamed") and "row moved" in got
    assert any(w["name"] == "dossier" for w in onto_db.words())
    # the old name is blocked from re-use, with the ledger as the finding
    refused = onto_db.add("artifact", "something new")
    assert refused.startswith("REFUSED") and "retired" in refused
    # renaming ONTO a taken name is refused
    onto_db.add("plan", "a proposal")
    assert onto_db.rename_word("plan", "dossier", "why").startswith("REFUSED")


def test_rename_requires_its_why(onto_db):
    assert "needs its why" in onto_db.rename_word("a", "b", "  ")
