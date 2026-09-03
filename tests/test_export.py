"""Standard RDF export: SKOS + OWL Turtle, RDF/XML, and WebVOWL JSON."""

import json

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def test_turtle_emits_skos_concepts(ws, onto_db):
    from montology_canvas.export import turtle

    onto_db.add("scan", "the tree-sitter sweep", kind="core", code="scan", pos="noun")
    onto_db.add("candidate", "a recurring name with no word", kind="core",
                owner="scan", code="scan.candidate", pos="noun")

    ttl = turtle()
    assert "@prefix skos:" in ttl
    assert "monty:scan a skos:Concept, owl:Class" in ttl
    assert "skos:broader monty:scan" in ttl
    assert "Montology" in ttl


def test_turtle_records_a_rename_as_deprecated(ws, onto_db):
    from montology_canvas.export import turtle

    onto_db.add("errand", "one unit of work", kind="core", pos="noun")
    onto_db.rename_word("errand", "task", "one word for the unit")

    ttl = turtle()
    assert "monty:errand a owl:Class" in ttl
    assert "owl:deprecated true" in ttl
    assert "monty:supersededBy monty:task" in ttl


def test_turtle_records_relations_as_object_properties(ws, onto_db):
    from montology_canvas.export import turtle
    from montology_ontology import relate

    onto_db.add("tour", "a guided path", kind="core", pos="noun")
    onto_db.add("pointer", "where the user is", kind="core", pos="noun")
    relate("tour", "flies", "pointer", why="the tour moves the pointer")

    ttl = turtle()
    assert "monty:rel-flies a owl:ObjectProperty" in ttl
    assert "monty:tour monty:rel-flies monty:pointer" in ttl


def test_vowl_json_is_webvowl_shape(ws, onto_db):
    from montology_canvas.export import vowl

    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")

    doc = vowl()
    assert doc["header"]["author"] == ["Montology"]
    assert "Montology" in doc["header"]["title"]["undefined"]
    assert doc["class"]
    assert doc["classAttribute"]
    assert any(a["label"]["undefined"] == "cell" for a in doc["classAttribute"])


def test_export_command_formats(ws, onto_db, monkeypatch):
    from montology_canvas.export import export

    onto_db.add("word", "one term with one meaning", kind="core", pos="noun")
    assert export("ttl").startswith("@prefix")
    assert export("xml").startswith("<?xml")
    payload = json.loads(export("vowl"))
    assert payload["namespace"][0]["name"] == "monty"


def test_serve_exposes_standard_ontology_routes(ws, onto_db, monkeypatch):
    import importlib
    import threading

    from montology_canvas import serve

    serve_mod = importlib.import_module("montology_canvas.serve")
    static = ws / "static"
    static.mkdir()
    (static / "index.html").write_text("<html></html>")
    monkeypatch.setattr(serve_mod, "STATIC", static)
    onto_db.add("cell", "the box", kind="core", pos="noun")

    url, ready = {}, threading.Event()
    threading.Thread(target=lambda: serve(open_browser=False, with_scan=False,
                                          _ready=lambda u: (url.setdefault("at", u), ready.set())),
                     daemon=True).start()
    assert ready.wait(10)
    base = url["at"]

    import urllib.request

    ttl = urllib.request.urlopen(base + "api/ontology.ttl").read().decode()
    assert "monty:cell" in ttl
    vowl = json.loads(urllib.request.urlopen(base + "api/ontology.vowl.json").read())
    assert vowl["header"]["author"] == ["Montology"]
