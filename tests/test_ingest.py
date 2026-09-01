"""Two public taxonomies in the database: parsed, custodied, licensed, cited."""

import json
import urllib.request

import pytest

PROV_RDF = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:prov="http://www.w3.org/ns/prov#"
         xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://www.w3.org/ns/prov#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
         xmlns:owl="http://www.w3.org/2002/07/owl#">
  <owl:Class rdf:about="http://www.w3.org/ns/prov#Activity">
    <rdfs:label>Activity</rdfs:label>
    <definition>An activity is something that occurs over a period of time.</definition>
    <rdfs:isDefinedBy rdf:resource="http://www.w3.org/ns/prov-o#"/>
  </owl:Class>
  <owl:ObjectProperty rdf:about="http://www.w3.org/ns/prov#activity">
    <rdfs:comment xml:lang="en">The activity of an influence.</rdfs:comment>
    <rdfs:isDefinedBy rdf:resource="http://www.w3.org/ns/prov-o#"/>
  </owl:ObjectProperty>
  <owl:ObjectProperty rdf:about="http://www.w3.org/ns/prov#wasGeneratedBy">
    <rdfs:isDefinedBy rdf:resource="http://www.w3.org/ns/prov-o#"/>
    <rdfs:domain rdf:resource="http://www.w3.org/ns/prov#Entity"/>
    <rdfs:range rdf:resource="http://www.w3.org/ns/prov#Activity"/>
  </owl:ObjectProperty>
  <owl:ObjectProperty rdf:about="http://www.w3.org/ns/prov#hadActivity">
    <rdfs:comment>This property has multiple RDFS domains to suit OWL profiles.</rdfs:comment>
    <rdfs:comment xml:lang="en">The optional Activity of an Influence.</rdfs:comment>
    <rdfs:isDefinedBy rdf:resource="http://www.w3.org/ns/prov-o#"/>
  </owl:ObjectProperty>
  <owl:Class rdf:about="http://www.w3.org/ns/prov#ServiceDescription">
    <definition>prov-aq's, not PROV-O's.</definition>
    <rdfs:isDefinedBy rdf:resource="http://www.w3.org/ns/prov-aq#"/>
  </owl:Class>
  <owl:AnnotationProperty rdf:about="http://www.w3.org/ns/prov#definition">
    <rdfs:comment>The vocabulary the file describes itself with.</rdfs:comment>
    <rdfs:isDefinedBy rdf:resource="http://www.w3.org/ns/prov-o#"/>
  </owl:AnnotationProperty>
</rdf:RDF>
"""

SCHEMAORG_JSONLD = json.dumps({"@context": {"schema": "https://schema.org/"}, "@graph": [
    {"@id": "schema:Person", "@type": "rdfs:Class", "rdfs:label": "Person",
     "rdfs:comment": "A person (alive, dead, undead, or fictional)."},
    {"@id": "schema:Action", "@type": "rdfs:Class",
     "rdfs:label": {"@language": "en", "@value": "Action"},
     "rdfs:comment": {"@language": "en", "@value": "An action performed by a direct agent."}},
    {"@id": "schema:author", "@type": "rdf:Property", "rdfs:label": "author",
     "rdfs:comment": "The author of this content. See <a href=\"h\">HTML5</a>&nbsp;for more."},
    {"@id": "schema:Code", "@type": "rdfs:Class", "rdfs:label": "Code",
     "rdfs:comment": "Computer programming source code.",
     "schema:supersededBy": {"@id": "schema:SoftwareSourceCode"}},
    {"@id": "schema:Monday", "@type": "schema:DayOfWeek", "rdfs:label": "Monday",
     "rdfs:comment": "The day between Sunday and Tuesday."},
    {"@id": "schema:distance", "@type": "rdf:Property", "rdfs:label": "distance",
     "rdfs:comment": "The distance travelled."},
    {"@id": "schema:Distance", "@type": "rdfs:Class", "rdfs:label": "Distance",
     "rdfs:comment": "Properties that take Distances as values."},
]})


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """The claim under test everywhere below: once a payload is cached, an
    ingest never reaches the network. A test that quietly downloads 1.5 MB of
    Schema.org is a test that fails on a plane and passes on a desk."""
    def refuse(*_a, **_k):
        raise AssertionError("the ingest went to the network; the cache is the source here")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def cached(ws, name: str, text: str) -> None:
    path = ws / ".monty" / "cache" / "sources" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_prov_o_takes_the_ontologys_own_terms(ws, onto_db):
    from montology_ontology import ingest_source

    cached(ws, "prov-o.rdf", PROV_RDF)
    report = ingest_source("prov-o")
    got = {w["name"]: w for w in onto_db.words()}

    assert set(got) == {"Activity", "wasGeneratedBy", "hadActivity"}
    assert all(w["kind"] == "adopted" and w["origin"] == "taxonomy:prov-o" for w in got.values())
    # prov-aq's term and the file's own annotation vocabulary are not PROV-O
    assert "ServiceDescription" not in got and "definition" not in got
    # a class names a thing; a property's part of speech is not the file's to say
    assert got["Activity"]["pos"] == "noun" and got["wasGeneratedBy"]["pos"] is None
    # the English comment beats the untagged editorial note that precedes it
    assert got["hadActivity"]["definition"] == "The optional Activity of an Influence."
    # ten PROV-O terms publish no prose; none of it gets invented here
    assert "publishes no prose definition" in got["wasGeneratedBy"]["definition"]
    assert "prov:Entity to prov:Activity" in got["wasGeneratedBy"]["definition"]
    assert "www.w3.org/TR/prov-o/#wasGeneratedBy" in got["wasGeneratedBy"]["definition"]
    # `activity` folded into `Activity`, said out loud rather than dropped
    assert "folded   1 name(s)" in report and "activity" in report


def test_schemaorg_skips_what_its_publisher_retired(ws, onto_db):
    from montology_ontology import ingest_source

    cached(ws, "schemaorg.jsonld", SCHEMAORG_JSONLD)
    report = ingest_source("schemaorg")
    got = {w["name"]: w for w in onto_db.words()}

    assert set(got) == {"Person", "Action", "author", "Distance"}
    assert "Code" not in got and "skipped  1 superseded" in report   # supersededBy
    assert "Monday" not in got                                      # an enumeration member
    assert got["Action"]["definition"] == "An action performed by a direct agent."  # @value
    assert got["author"]["definition"] == "The author of this content. See HTML5 for more."


def test_local_words_win_and_a_re_ingest_refreshes_wholesale(ws, onto_db):
    from montology_ontology import ingest_source

    cached(ws, "schemaorg.jsonld", SCHEMAORG_JSONLD)
    onto_db.add("person", "whoever this repo means by it", kind="core", pos="noun")
    report = ingest_source("schemaorg")

    ours = {w["name"]: w for w in onto_db.words()}["person"]
    assert ours["origin"] is None and ours["definition"] == "whoever this repo means by it"
    assert "LOCAL WINS  1 name(s)" in report and "left every one of them alone: Person" in report

    # the standard is the standard's to change: a second run replaces its own
    # rows and leaves ours where they are
    before = len(onto_db.words())
    assert "ingested  3 term(s)" in ingest_source("schemaorg")
    assert len(onto_db.words()) == before


def test_a_second_taxonomy_leaves_a_name_with_the_first(ws, onto_db):
    from montology_ontology import ingest_source

    cached(ws, "prov-o.rdf", PROV_RDF)
    cached(ws, "schemaorg.jsonld", json.dumps(
        {"@graph": [{"@id": "schema:Activity", "@type": "rdfs:Class",
                     "rdfs:label": "Activity", "rdfs:comment": "Schema.org's Activity."},
                    {"@id": "schema:Person", "@type": "rdfs:Class",
                     "rdfs:label": "Person", "rdfs:comment": "A person."}]}))
    ingest_source("prov-o")
    report = ingest_source("schemaorg")

    got = {w["name"]: w for w in onto_db.words()}
    assert got["Activity"]["origin"] == "taxonomy:prov-o"
    assert "ALREADY ADOPTED  1 name(s)" in report and "Activity" in report


def test_a_retired_name_is_not_taken_back(ws, onto_db):
    from montology_ontology import ingest_source

    cached(ws, "schemaorg.jsonld", SCHEMAORG_JSONLD)
    onto_db.add("author", "who wrote it", kind="core", pos="noun")
    onto_db.rename_word("author", "byline", "one word for it")
    report = ingest_source("schemaorg")

    assert "author" not in {w["name"] for w in onto_db.words()}
    assert "RETIRED  1 name(s)" in report


def test_every_answer_about_an_adopted_word_carries_its_licence(ws, onto_db):
    from montology_ontology import ingest_source, render_sources

    cached(ws, "schemaorg.jsonld", SCHEMAORG_JSONLD)
    report = ingest_source("schemaorg")
    assert "CC BY-SA 3.0" in report and "share-alike reaches anything you derive" in report

    found = "\n".join(onto_db.check("Person"))
    assert "ADOPTED" in found and "Schema.org" in found and "CC BY-SA 3.0" in found

    listing = "\n".join(render_sources("core"))
    assert "ingested here — 4 adopted word(s)" in listing
    assert "ingestable — monty onto sources ingest prov-o" in listing


def test_an_id_with_no_ingester_is_refused_with_the_ones_that_have_one(ws):
    from montology_ontology import ingest_source

    both = ingest_source("naics")            # in the registry, no parser
    assert both.startswith("REFUSED") and "prov-o, schemaorg" in both
    assert "no ingester" in both

    neither = ingest_source("not-a-source")  # not in the registry at all
    assert neither.startswith("REFUSED") and "not a registry id" in neither


def test_a_truncated_payload_is_data_with_the_repair(ws):
    from montology_ontology import ingest_source

    cached(ws, "prov-o.rdf", PROV_RDF[:200])
    refused = ingest_source("prov-o")
    assert refused.startswith("REFUSED") and "--refresh" in refused


def test_a_whole_taxonomy_is_cited_not_rendered(ws, onto_db):
    """The disclosure question the ingest forces: 2,300 adopted words must not
    become 2,300 rows in the page every agent loads on every turn."""
    from montology_gen import lint, render_pages, sync
    from montology_gen.laws import BODY_CAP, PAGE_CAP

    onto_db.add("thread", "a stateful session", kind="core", pos="noun")
    conn = onto_db.connect()
    conn.executemany(
        "INSERT INTO word (name, kind, definition, pos, origin) VALUES (?,?,?,?,?)",
        [(f"SchemaTerm{n}", "adopted", "A term Schema.org publishes, in full prose that "
          "costs context nobody spends on reading two thousand of them.", "noun",
          "taxonomy:schemaorg") for n in range(2300)])
    conn.commit()

    text, pages, demoted = render_pages("t")
    assert len(text) <= BODY_CAP                       # the resident page still fits…
    assert "**thread**" in text                        # …with our own words in full
    assert "SchemaTerm1" not in text                   # …and theirs cited instead
    assert "2,300 words" in text and "CC BY-SA 3.0" in text
    assert all(len(p) <= PAGE_CAP for p in pages.values())
    assert any("cited, not listed" in step for step in demoted)

    sync()
    assert lint()[-1].endswith("ok")
