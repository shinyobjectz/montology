"""The harvested tier: 177 ontologies nobody here read, and the seam that
keeps them out of the shortlist.

Tier 2 is useful only while it is obviously NOT tier 1. Every failure worth
guarding is a way that seam quietly closes: a harvested row printed without
its unvetted heading, a registry licence label read as a checked verdict, an
OBO ontology appearing twice under one id with a ruling on one copy and
nothing on the other. The rest of these cases are the arithmetic — a filter
that shrinks 267 records to 177 has to say where the other 90 went, and a
filter whose tally disappears when it catches nothing is indistinguishable
from a filter somebody deleted.

Nothing here touches the network. The registry is a fixture written to the
cache path, which is also the offline path the command takes in real use.
"""

import json

import pytest

# Two active, one inactive, one unlicensed, and one that is already `sources`
# tier 1 — every filter with something to catch, in one small document.
REGISTRY = {
    "ontologies": [
        {
            "id": "pato", "title": "Phenotype And Trait Ontology",
            "description": "Qualities of anatomical structures and organisms.",
            "domain": "phenotype", "activity_status": "active",
            "license": {"label": "CC BY 3.0"},
            "homepage": "https://github.com/pato-ontology/pato",
            "ontology_purl": "http://purl.obolibrary.org/obo/pato.owl",
        },
        {
            "id": "obi", "title": "Ontology for Biomedical Investigations",
            "description": "Describes an assay, its protocol and its instruments.",
            "domain": "investigations", "activity_status": "active",
            "license": {"label": "CC BY 4.0"},
            "homepage": "http://obi-ontology.org",
            "ontology_purl": "http://purl.obolibrary.org/obo/obi.owl",
        },
        {
            "id": "gaz", "title": "Gazetteer",
            "description": "Places, retired.", "domain": "environment",
            "activity_status": "inactive", "license": {"label": "CC BY 3.0"},
            "homepage": "http://example.org/gaz",
            "ontology_purl": "http://purl.obolibrary.org/obo/gaz.owl",
        },
        {
            "id": "nowhere", "title": "Unlicensed Ontology",
            "description": "Publishes nothing about rights.", "domain": "health",
            "activity_status": "active",
            "homepage": "http://example.org/nowhere",
            "ontology_purl": "http://purl.obolibrary.org/obo/nowhere.owl",
        },
        {
            "id": "go", "title": "Gene Ontology",
            "description": "Molecular function, biological process.",
            "domain": "biological systems", "activity_status": "active",
            "license": {"label": "CC BY 4.0"},
            "homepage": "http://geneontology.org",
            "ontology_purl": "http://purl.obolibrary.org/obo/go.owl",
        },
    ]
}


@pytest.fixture()
def ws(tmp_path):
    """A workspace whose registry cache is already warm — the state every
    run after the first one is in."""
    from montology_ontology import index as idx

    path = idx.cache_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(REGISTRY))
    return tmp_path


@pytest.fixture()
def no_network(monkeypatch):
    """Proof by construction: any test using this fails loudly rather than
    silently reaching obofoundry.org and passing for the wrong reason."""
    import urllib.request

    def refuse(*a, **k):
        raise OSError("the tests do not have a network")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)


def test_the_index_answers_offline_from_its_cache(ws, no_network):
    """The whole reason the JSON is written to disk. A `--search` that needs
    obofoundry.org every time is a command that fails on a plane, in CI, and
    behind every corporate proxy."""
    from montology_ontology import harvest_index

    got = harvest_index(root=ws)
    assert {e.id for e in got.entries} == {"pato", "obi"}
    assert got.origin == "cache"


def test_an_unmaintained_ontology_is_dropped_and_the_drop_is_counted(ws, no_network):
    """OBO marks 76 of its 267 records inactive or orphaned. Indexing them
    hands somebody a dead ontology with nothing saying it is dead; dropping
    them without a tally makes the harvest a claim instead of a count."""
    from montology_ontology import harvest_index
    from montology_ontology.index import FILTERS

    got = harvest_index(root=ws)
    assert "gaz" not in {e.id for e in got.entries}
    assert got.skipped[FILTERS[0]] == 1


def test_a_missing_licence_is_a_blank_not_a_verdict(ws, no_network):
    """`sources` may say `unlicensed`, because somebody opened the repo and
    checked. A registry record with no licence field is an unchecked blank,
    and this tier turning one into the other would launder a guess into a
    verdict that reads exactly like a checked one."""
    from montology_ontology import harvest_index
    from montology_ontology.index import FILTERS

    got = harvest_index(root=ws)
    assert "nowhere" not in {e.id for e in got.entries}
    assert got.skipped[FILTERS[1]] == 1


def test_a_shortlisted_ontology_is_not_harvested_a_second_time(ws, no_network):
    """Fourteen OBO ontologies are tier 1 entries. Listed in both tiers, `go`
    would appear once with a relevance ruling and a commercial verdict and
    once with neither — the exact ambiguity the split exists to remove."""
    from montology_ontology import harvest_index
    from montology_ontology.index import FILTERS

    got = harvest_index(root=ws)
    assert "go" not in {e.id for e in got.entries}
    assert got.skipped[FILTERS[2]] == 1


def test_a_filter_that_caught_nothing_still_reports_a_zero(tmp_path, no_network):
    """A reason that appears only when it fires cannot be told apart from a
    filter that was removed. The zero is the evidence the check ran."""
    from montology_ontology import harvest_index, render_harvest
    from montology_ontology.index import FILTERS, cache_path

    clean = {"ontologies": [REGISTRY["ontologies"][0]]}
    path = cache_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(clean))

    got = harvest_index(root=tmp_path)
    assert set(got.skipped) == set(FILTERS)
    assert sum(got.skipped.values()) == 0
    assert all(f"skipped    0  {r}" in "\n".join(render_harvest(root=tmp_path))
               for r in FILTERS)


def test_the_kept_and_the_dropped_add_up_to_what_was_fetched(ws, no_network):
    """The one assertion that catches a filter added later without a tally:
    the arithmetic stops closing before anybody notices the report is short."""
    from montology_ontology import harvest_index

    got = harvest_index(root=ws)
    assert len(got.entries) + sum(got.skipped.values()) == got.fetched == 5


def test_search_reads_the_id_the_title_the_domain_and_the_blurb(ws, no_network):
    """Four fields because a searcher knows one of four things: the prefix
    they were handed, the name they half-remember, the field they work in, or
    only the concept. A search over titles alone answers the second."""
    from montology_ontology import search_index

    assert [e.id for e in search_index("pato", root=ws)] == ["pato"]
    assert [e.id for e in search_index("biomedical", root=ws)] == ["obi"]
    assert [e.id for e in search_index("phenotype", root=ws)] == ["pato"]
    assert [e.id for e in search_index("protocol", root=ws)] == ["obi"]


def test_an_id_that_is_the_query_outranks_a_word_buried_in_a_blurb(ws, no_network):
    """Descriptions run to 650 characters, so ranking by how OFTEN a query
    appears would put a long abstract above the ontology actually named."""
    from montology_ontology import search_index

    hit = dict(REGISTRY["ontologies"][1],
               description="Mentions pato and pato and pato again.")
    from montology_ontology.index import cache_path
    cache_path(ws).write_text(json.dumps({"ontologies": [hit, REGISTRY["ontologies"][0]]}))
    assert [e.id for e in search_index("pato", root=ws)] == ["pato", "obi"]


def test_the_shortlist_is_searched_by_its_ruling_as_well_as_its_name():
    """`why` is the one place a tier-1 entry says what it is FOR. Without it
    'sbom' finds nothing, even though the shortlist carries two answers."""
    from montology_ontology.index import search_sources

    assert {s.id for s in search_sources("sbom")} == {"spdx"}
    assert "cyclonedx" in {s.id for s in search_sources("bill of materials")}


def test_a_query_never_mixes_the_two_tiers_into_one_list(ws, no_network):
    """The failure this whole module is shaped against: a harvested row read
    as a recommendation. The tiers get separate headings, the second says it
    was not read, and the shortlist is printed first."""
    from montology_ontology import render_search
    from montology_ontology.index import UNVETTED

    lines = render_search("phenotype", root=ws)
    text = "\n".join(lines)
    shortlist = next(i for i, l in enumerate(lines) if "shortlist" in l)
    index = next(i for i, l in enumerate(lines) if "harvested index" in l)
    assert shortlist < index, "the vouched-for list comes first"
    assert UNVETTED in text
    assert "UNVETTED" in lines[index]


def test_a_harvested_licence_is_labelled_as_the_publisher_s_own_claim(ws, no_network):
    """Tier 1 prints `yes-attribution · CC BY 4.0` — a verdict somebody
    reached. Tier 2 has the string and not the verdict, and printing the
    string in the same shape would silently promote it."""
    from montology_ontology import render_search
    from montology_ontology.index import IndexEntry

    text = "\n".join(render_search("phenotype", root=ws))
    assert "licence AS DECLARED BY ITS PUBLISHER: CC BY 3.0" in text
    assert not hasattr(IndexEntry("i", "n", "d", "b", "l", "u", "h"), "commercial")


def test_with_neither_cache_nor_network_the_refusal_carries_the_repair(
        tmp_path, no_network):
    """An empty result would read as 'no such ontology exists', which is a
    different and much worse answer than 'I could not look'."""
    from montology_ontology import harvest_index, render_search

    with pytest.raises(ValueError) as e:
        harvest_index(root=tmp_path)
    assert "run this once with a network" in str(e.value)
    # and the renderer turns it into a line rather than a traceback
    assert any("REFUSED" in l for l in render_search("phenotype", root=tmp_path))


def test_a_refresh_that_cannot_reach_the_network_says_the_answer_is_stale(
        ws, no_network):
    """Failing a question the disk can already answer is worse than answering
    it late — but an answer that does not admit it is old is worse than both."""
    from montology_ontology import harvest_index

    got = harvest_index(refresh=True, root=ws)
    assert {e.id for e in got.entries} == {"pato", "obi"}
    assert "STALE" in got.origin


def test_an_error_page_never_replaces_a_good_cache(ws, monkeypatch):
    """A captive portal, a 503 and a proxy interstitial all arrive as HTTP
    200 with HTML in the body. Written to the cache that is a workspace whose
    index is broken until somebody deletes a file they do not know exists."""
    import contextlib
    import urllib.request

    from montology_ontology import harvest_index
    from montology_ontology.index import cache_path

    @contextlib.contextmanager
    def portal(*a, **k):
        class Body:
            def read(self):
                return b"<html>sign in to continue</html>"
        yield Body()

    monkeypatch.setattr(urllib.request, "urlopen", portal)
    got = harvest_index(refresh=True, root=ws)
    assert "STALE" in got.origin
    assert {e.id for e in got.entries} == {"pato", "obi"}
    assert json.loads(cache_path(ws).read_text())["ontologies"], "cache survived"


def test_the_cache_lives_where_gitignore_already_excludes(tmp_path):
    """`.monty/cache/` is the workspace's refetchable-things directory and is
    gitignored. A cache anywhere else puts 600KB of somebody else's registry
    into every clone, or worse, into the diff of an unrelated commit."""
    from montology_ontology.index import cache_path

    assert cache_path(tmp_path).parent == tmp_path / ".monty" / "cache"
