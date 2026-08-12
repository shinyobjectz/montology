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


# ── amend: the record corrected in place ──────────────────────────────────
# The case this exists for: a word is authored, a later ruling narrows it,
# and the recorded definition is now WRONG. `add` refuses (the name is
# taken) and `rename` is the wrong verb (the name is right). Before amend
# the only path was an UPDATE against the database, behind the authoring
# door the gate is supposed to guard.


def test_amend_corrects_the_record_and_ledgers_the_old_text(onto_db):
    onto_db.add("vectoring", "steering anything by embedding", test="how it aims")
    got = onto_db.amend("vectoring", definition="steering RETRIEVAL by embedding",
                        test="how retrieval aims", why="the 2026-08-12 ruling narrowed it")
    assert got.startswith("amended")
    word = next(w for w in onto_db.words() if w["name"] == "vectoring")
    assert word["definition"] == "steering RETRIEVAL by embedding"
    assert word["test"] == "how retrieval aims"

    ledger = onto_db.amendments("vectoring")
    assert {r["field"] for r in ledger} == {"definition", "test"}
    was = {r["field"]: r["was"] for r in ledger}
    assert was["definition"] == "steering anything by embedding"
    assert was["test"] == "how it aims"
    assert all(r["why"] == "the 2026-08-12 ruling narrowed it" for r in ledger)


def test_amend_touches_only_the_fields_it_is_given(onto_db):
    onto_db.add("cell", "the sandbox", test="where code runs", note="network-blocked")
    onto_db.amend("cell", definition="the network-blocked sandbox")
    word = next(w for w in onto_db.words() if w["name"] == "cell")
    assert word["test"] == "where code runs"
    assert [r["field"] for r in onto_db.amendments("cell")] == ["definition"]


def test_amend_refuses_a_name_that_is_no_word(onto_db):
    onto_db.add("harness", "the loop")
    got = onto_db.amend("harnes", definition="a typo's word")
    assert got.startswith("REFUSED") and "is not a word" in got
    assert "did you mean: harness?" in got        # the repair, not just the no
    assert "monty onto add" in got
    assert onto_db.amendments() == []             # a refusal writes nothing


def test_amend_refuses_a_no_op(onto_db):
    onto_db.add("thread", "a stateful session", test="one conversation")
    same = onto_db.amend("thread", definition="a stateful session")
    assert same.startswith("REFUSED") and "already says exactly that" in same
    nothing = onto_db.amend("thread")
    assert nothing.startswith("REFUSED") and "--definition" in nothing
    assert onto_db.amendments() == []


def test_amend_clears_a_note_but_never_the_definition(onto_db):
    onto_db.add("dossier", "what a task produces", note="was called artifact")
    assert onto_db.amend("dossier", note="").startswith("amended")
    assert onto_db.amendments("dossier")[0]["was"] == "was called artifact"
    empty = onto_db.amend("dossier", definition="   ")
    assert empty.startswith("REFUSED") and "squatting on meaning" in empty


def test_amend_keeps_the_code_tree_and_the_owner_tree_intact(onto_db):
    onto_db.add("harness", "the loop", code="har")
    onto_db.add("cell", "the sandbox", owner="harness", code="har.cell")
    stranded = onto_db.amend("harness", code="hns")
    assert stranded.startswith("REFUSED") and "cell" in stranded and "strands" in stranded
    assert onto_db.amend("cell", code="har.box").startswith("amended")
    assert onto_db.amend("cell", owner="cell").startswith("REFUSED")
    loop = onto_db.amend("harness", owner="cell")
    assert loop.startswith("REFUSED") and "close the loop" in loop


def test_amend_says_when_the_correction_is_temporary(onto_db):
    conn = onto_db.connect()
    conn.execute("INSERT INTO word (name, kind, definition, origin) VALUES (?,?,?,?)",
                 ("thread", "core", "a session", "acme/ontology"))
    conn.commit()
    got = onto_db.amend("thread", definition="a stateful session")
    assert got.startswith("amended")
    assert "inherited from acme/ontology" in got and "monty onto pull" in got


def test_amendment_history_surfaces_in_check(onto_db):
    onto_db.add("vectoring", "steering anything by embedding")
    onto_db.amend("vectoring", definition="steering retrieval by embedding",
                  why="a ruling narrowed it")
    findings = onto_db.check("Vectoring")
    assert any(f.startswith("AMENDED") and "steering anything by embedding" in f
               and "a ruling narrowed it" in f for f in findings)
