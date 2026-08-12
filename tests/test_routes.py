"""Routing: say this, not that, HERE — and the queries that ride on it.

The register is the whole feature. `workspace` is a correct word in code and
a wrong one on the surface; a ruling that cannot say where it applies is
advisory forever, and these tests pin that it stays that way.
"""

import pytest


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text(
        'name = "app"\n\n[registers]\nsurface = ["ui/*"]\ncode = ["server/*"]\n')
    (tmp_path / "ui").mkdir()
    (tmp_path / "server").mkdir()
    (tmp_path / "ui" / "page.tsx").write_text("const label = 'workspace settings';\n")
    (tmp_path / "server" / "app.py").write_text(
        "workspace = 1  # the uv workspace\n"
        "def go(workspace):\n"
        "    return workspace, workspace\n")
    return tmp_path


@pytest.fixture()
def vocab(onto_db):
    conn = onto_db.connect()
    for name, code in (("workspace", "har.workspace"), ("Studio", "app.studio"),
                       ("org", "org"), ("Dossier", "dos")):
        conn.execute("INSERT INTO word (name, kind, definition, code) VALUES (?,?,?,?)",
                     (name, "inner", f"the {name}", code))
    conn.commit()
    return onto_db


def test_a_register_must_be_one_of_the_four(vocab):
    from montology_ontology import route_add

    got = route_add("workspace", "Studio", register="everywhere")
    assert got.startswith("REFUSED") and "code, surface, prose, all" in got


def test_scoping_a_route_moves_it_rather_than_duplicating(vocab):
    """`all` already covers `code`; keeping both would double every finding."""
    from montology_ontology import route_add, routes

    route_add("artifact", "Dossier", register="all")
    assert len(routes()) == 1
    got = route_add("artifact", "Dossier", register="code")
    assert "narrowed from 'all'" in got
    assert [(r["from_term"], r["register"]) for r in routes()] == [("artifact", "code")]


def test_a_route_may_point_at_a_word_that_does_not_exist_yet(vocab):
    """`Artifact` was retired in code and reinstated on the surface. A ledger
    that could not hold that could not describe the decision."""
    from montology_ontology import route_add

    got = route_add("Dossier", "Artifact", register="surface")
    assert got.startswith("routed")
    assert "not a word yet" in got


def test_drafts_lift_the_scope_out_of_the_parenthetical(vocab):
    from montology_ontology import route_drafts, rule

    rule("workspace (for the tenant surface)", "Studio", "the App's word")
    rule("output", "Dossier", "unscoped on purpose")
    drafts = {d["from_term"]: d for d in route_drafts()}

    assert drafts["workspace"]["register"] == "surface"   # read from the hint
    assert drafts["workspace"]["to_word"] == "Studio"
    assert drafts["output"]["register"] == "all"          # no hint: not guessed
    assert drafts["output"]["known_target"] is True


def test_drafts_do_not_duplicate_a_term_written_two_ways(vocab):
    from montology_ontology import route_drafts, rule

    rule("artifact (for a deliverable)", "Dossier", "w")
    conn = vocab.connect()
    conn.execute("INSERT INTO renamed (was, now, renamed_on, why) VALUES (?,?,?,?)",
                 ("Artifact", "Dossier", "2026-08-09", "w"))
    conn.commit()
    terms = [d["from_term"].lower() for d in route_drafts()]
    assert terms.count("artifact") == 1


def test_a_route_only_finds_its_own_register(repo, vocab):
    from montology_scan.stale import stale

    from montology_ontology import route_add

    route_add("workspace", "Studio", register="surface")
    r = stale(repo)

    assert len(r["findings"]) == 1
    hit = r["findings"][0]
    assert hit["to_word"] == "Studio"
    assert [f.split(" ")[0] for f in hit["files"]] == ["ui/page.tsx"]  # NOT server/


def test_a_route_that_cannot_be_scoped_can_never_gate(repo, vocab):
    """The non-negotiable rule: unscoped findings drown the report, and a
    report you stop reading enforces nothing."""
    from montology_scan.stale import stale

    from montology_ontology import route_add

    route_add("workspace", "org", register="all")
    r = stale(repo)

    assert r["findings"] == []
    assert [x["from_term"] for x in r["unscopable"]] == ["workspace"]
    assert "--in code|surface|prose" in "\n".join(
        __import__("montology_scan.stale", fromlist=["render"]).render(r))


def test_surface_is_never_assumed_when_the_repo_has_not_said(tmp_path, vocab):
    """`code` and `prose` follow from a file's kind; `surface` is a claim
    only the repo can make, so an unconfigured surface matches nothing."""
    from montology_scan.stale import stale

    from montology_ontology import route_add

    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "x"\n')
    (tmp_path / "a.tsx").write_text("workspace\n")
    route_add("workspace", "Studio", register="surface")

    r = stale(tmp_path)
    assert r["findings"] == []
    assert len(r["unscopable"]) == 1


def test_an_orphan_route_and_a_real_cycle_both_fail(vocab):
    from montology_ontology import render_routes, route_add, route_analyse

    route_add("graph", "Events", register="code")          # Events is no word
    route_add("Dossier", "Artifact", register="all")       # overlaps everything
    route_add("Artifact", "Dossier", register="all")
    lines = render_routes(route_analyse())

    assert any("points at a word that does not exist" in x and "Events" in x for x in lines)
    assert any(x.startswith("FAIL route cycle") for x in lines)


def test_two_registers_are_a_bridge_not_a_cycle(vocab):
    """The Artifact/Dossier case: code says one word, the surface says the
    other. Disjoint registers do not contradict."""
    from montology_ontology import render_routes, route_add, route_analyse

    conn = vocab.connect()
    conn.execute("INSERT INTO word (name, kind, definition) VALUES ('Artifact','inner','d')")
    conn.commit()
    route_add("Artifact", "Dossier", register="code")
    route_add("Dossier", "Artifact", register="surface")
    lines = render_routes(route_analyse())

    assert not any(x.startswith("FAIL") for x in lines)
    assert any("a bridge, not a cycle" in x for x in lines)


def test_a_term_sent_two_ways_in_one_register_is_a_contradiction(vocab):
    from montology_ontology import render_routes, route_add, route_analyse

    route_add("task", "Thread", register="code")
    route_add("task", "org", register="code")
    lines = render_routes(route_analyse())
    assert any("disagreement, not scope" in x for x in lines)


def test_health_separates_dead_from_merely_unnamed(repo, vocab):
    from montology_scan.health import health

    conn = vocab.connect()
    conn.execute("INSERT INTO word (name, kind, definition, code) VALUES (?,?,?,?)",
                 ("subspace", "inner", "never built", "mad.space"))
    conn.commit()

    states = {w["name"]: w["state"] for w in health(repo)["words"]}
    assert states["subspace"] == "dead"          # nowhere at all
    assert states["workspace"] == "unnamed"      # in code, no symbol holds it


def test_health_matches_the_last_dotted_segment(tmp_path, onto_db):
    """Elixir declares `Nexus.Events.Event`; matching whole names reported
    65 live words as unimplemented."""
    from montology_scan.health import health

    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "x"\n')
    (tmp_path / "a.ex").write_text("defmodule Nexus.Events.Event do\nend\n")
    conn = onto_db.connect()
    conn.execute("INSERT INTO word (name, kind, definition) VALUES ('Event','inner','d')")
    conn.commit()

    states = {w["name"]: w["state"] for w in health(tmp_path)["words"]}
    assert states["Event"] == "carried"
