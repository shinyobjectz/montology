"""The intake: a spec becomes a form, a submit becomes a file, the glossary
renders the ontology and refuses an empty one."""
import json
import threading
import urllib.request

import pytest

from montology_intake import ask, glossary, merged_answers, render_form, status, validate_spec
from montology_intake import spec as ispec

SPEC = {
    "phase": "1-domain", "title": "What this system is", "intro": "Three quick ones.",
    "questions": [
        {"id": "system", "type": "text", "label": "What does it do?"},
        {"id": "docs", "type": "url", "label": "Where are the docs?"},
        {"id": "users", "type": "choice", "label": "Who uses it?", "options": ["Ops", "Devs", "Both"]},
        {"id": "edges", "type": "multi", "label": "Whose words leak in?", "options": ["React", "K8s"], "required": False},
        {"id": "strictness", "type": "scale", "label": "How strict?", "min": 1, "max": 5, "labels": ["warn", "fail"]},
    ],
}


@pytest.fixture()
def intake_folder(tmp_path, monkeypatch):
    ws = tmp_path / "acme"
    (ws / ".monty").mkdir(parents=True)
    monkeypatch.setattr(ispec, "INTAKE_DIR", ws / ".monty" / "answers")
    return ws / ".monty" / "answers"


def test_a_spec_is_told_from_a_path_by_its_shape_not_by_a_stat(tmp_path):
    """The regression that kept CI red for three weeks. Deciding
    inline-JSON-vs-path with `Path(source).exists()` stats a 900-byte
    "filename": Linux raises ENAMETOOLONG and macOS returns False, so the
    bug was invisible on the machine it was written on and fatal on every
    Linux runner. A `{` is the whole test."""
    from montology_intake.spec import load_spec

    inline = json.dumps(SPEC)
    assert len(inline) > 255, "the case only bites past a path component's limit"
    assert load_spec(inline) == SPEC
    assert load_spec("  " + inline + "  ") == SPEC      # whitespace is not a path

    on_disk = tmp_path / "phase.json"
    on_disk.write_text(inline)
    assert load_spec(str(on_disk)) == SPEC

    with pytest.raises(OSError):                        # a path that is not there
        load_spec(str(tmp_path / "nope.json"))


def test_spec_validation_carries_repairs():
    assert validate_spec(SPEC) == []
    bad = {"phase": "Domain!", "questions": [{"id": "x", "type": "choice", "label": "?"},
                                              {"id": "x", "label": "dup"}, {"id": "y", "type": "rating", "label": "?"}]}
    report = "\n".join(validate_spec(bad))
    assert "must be a slug" in report and "title is missing" in report
    assert "needs options" in report and "used twice" in report and "not one of" in report


def test_form_is_self_contained():
    page = render_form(SPEC, "acme")
    assert "<title>What this system is</title>" in page
    assert "http" not in page.split("<script>")[0].split("<style>")[1]  # no remote css
    assert '"post_to": "/answers"' in page and "What does it do?" in page
    with pytest.raises(ValueError):
        render_form({"phase": "x"}, "acme")


def test_ask_roundtrip_writes_answers(intake_folder):
    answers = {"system": "ships anvils", "docs": "https://acme.test", "users": "Both",
               "edges": ["React"], "strictness": 4}

    def submit(url):
        page = urllib.request.urlopen(url).read().decode()
        assert "What this system is" in page
        req = urllib.request.Request(url + "answers", data=json.dumps({"answers": answers}).encode(),
                                     headers={"content-type": "application/json"})
        threading.Thread(target=lambda: urllib.request.urlopen(req).read(), daemon=True).start()

    got = ask(json.dumps(SPEC), open_browser=False, timeout=10, _ready=submit)
    assert got.startswith("answered") and "(5 answers)" in got
    assert (intake_folder / "1-domain.html").exists() and (intake_folder / "1-domain.json").exists()
    rec = json.loads((intake_folder / "1-domain.answers.json").read_text())
    assert rec["answers"] == answers and rec["workspace"] == "acme"
    assert merged_answers()["1-domain"]["answers"]["users"] == "Both"
    assert any(line.startswith("answered  1-domain") for line in status())


def test_ask_refuses_bad_spec_and_times_out(intake_folder):
    assert ask(json.dumps({"phase": "x"}), open_browser=False).startswith("REFUSED")
    got = ask(json.dumps(SPEC), open_browser=False, timeout=0.3, _ready=lambda u: None)
    assert got.startswith("timed out") and "monty intake ask" in got


def test_glossary_renders_the_ontology(intake_folder, onto_db):
    assert glossary().startswith("REFUSED") and "monty onto add" in glossary()
    onto_db.seed_for_test = None
    assert onto_db.add("anvil", "the heavy thing Acme ships", test="does it drop", pos="noun").startswith("added")
    onto_db.rule("project", "workspace", "one word for the thing")
    got = glossary()
    assert got.startswith("glossary") and "(1 words" in got
    page = (intake_folder / "glossary.html").read_text()
    assert "the heavy thing Acme ships" in page and "does it drop" in page
    assert "<s>project</s>" in page and "workspace" in page
    assert "glossary  rendered" in "\n".join(status())
