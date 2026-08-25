"""The graph: every edge montology holds, drawn once, measured not guessed."""

from collections import Counter

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def kinds(items):
    return Counter(i["kind"] for i in items)


def test_the_vocabulary_alone_is_nodes_and_edges(ws, onto_db):
    from montology_canvas import graph

    onto_db.add("scan", "the tree-sitter sweep of a codebase", kind="core",
                code="scan", pos="noun")
    onto_db.add("candidate", "a recurring declared name with no word", kind="core",
                owner="scan", code="scan.candidate", pos="noun")

    g = graph(with_scan=False)
    assert kinds(g["nodes"])["word"] == 2
    assert kinds(g["edges"])["contains"] == 1
    assert g["stats"]["words"] == 2
    assert len(g["fingerprint"]) == 16


def test_a_retired_name_becomes_a_term_pointing_at_the_word(ws, onto_db):
    """The history of a vocabulary IS the names it stopped using — a graph that
    draws only live words cannot draw a decision."""
    from montology_canvas import graph

    onto_db.add("errand", "one unit of work", kind="core", pos="noun")
    onto_db.rename_word("errand", "task", "one word for the unit of work")
    onto_db.rule("user", "person", "they are people")

    g = graph(with_scan=False)
    by_id = {n["id"]: n for n in g["nodes"]}
    assert by_id["term:errand"]["kind"] == "term"
    assert by_id["term:user"]["kind"] == "term"
    assert "word:task" in by_id and "term:task" not in by_id   # live words stay words

    e = {x["kind"]: x for x in g["edges"]}
    assert e["renamed"]["source"] == "term:errand" and e["renamed"]["target"] == "word:task"
    assert e["overloaded"]["source"] == "term:user"
    assert e["renamed"]["data"]["gates"] is True     # the guard always blocks a retired name


def test_a_route_that_cannot_gate_says_so(ws, onto_db):
    """qubie had one: `intelligence -> brain` at register 'all' with no scope.
    A ruling that cannot be scoped can never gate, and a canvas that draws it
    the same as an enforced one is lying about which decisions have teeth."""
    from montology_canvas import graph
    from montology_ontology import route_add

    onto_db.add("brain", "the model that answers", kind="core", pos="noun")
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    route_add("intelligence", "brain", register="all")
    route_add("sandbox", "cell", register="code", scope="src/**")

    routes = {e["source"]: e for e in graph(with_scan=False)["edges"]
              if e["kind"] == "routes"}
    assert routes["term:intelligence"]["data"]["gates"] is False
    assert routes["term:sandbox"]["data"]["gates"] is True
    assert routes["term:sandbox"]["label"] == "code"       # the register IS the label


def test_a_ruling_is_a_node_because_it_carries_a_why(ws, onto_db):
    from montology_canvas import graph

    onto_db.add("artifact", "what a run produces", kind="core", pos="noun")
    onto_db.collide("artifact", "mellea", "a file out of the sandbox",
                    "WE MOVED — ours became dossier")

    g = graph(with_scan=False)
    ruling = next(n for n in g["nodes"] if n["kind"] == "ruling")
    assert ruling["data"]["ruling_kind"] == "collision"
    assert "WE MOVED" in ruling["data"]["ruling"]
    assert ruling["data"]["their_meaning"]                  # an edge label holds neither
    assert any(e["kind"] == "rules" and e["target"] == "word:artifact" for e in g["edges"])


def test_the_code_counts_are_collisions_not_resolutions(ws, onto_db):
    """The obvious reading is backwards: a declaration named after an enforced
    word is a COLLISION. Code answers to a word through a bearing, never by
    wearing its name."""
    from montology_canvas import graph

    (ws / "src").mkdir()
    (ws / "src" / "thing.py").write_text("class Cell:\n    pass\n\ndef helper():\n    pass\n")
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")

    word = next(n for n in graph()["nodes"] if n["id"] == "word:cell")
    assert word["data"]["collides"] == 1
    assert word["data"]["excepted"] == 0
    assert word["data"]["at"] == ["src/thing.py:1"]         # the PLACE, not just a count


def test_an_exception_moves_a_collision_into_excepted(ws, onto_db):
    from montology_canvas import graph
    from montology_ontology import except_add

    (ws / "src").mkdir()
    (ws / "src" / "thing.py").write_text("class Cell:\n    pass\n")
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    except_add("cell", "the class IS the cell — the surface being literal", scope="src/**")

    word = next(n for n in graph()["nodes"] if n["id"] == "word:cell")
    assert (word["data"]["collides"], word["data"]["excepted"]) == (0, 1)


def test_a_candidate_is_marked_as_the_suggestion_it_is(ws, onto_db):
    """An instrument that hands back a guess dressed as a fact is worse than
    one that says nothing."""
    from montology_canvas import graph

    (ws / "src").mkdir()
    body = "\n\n".join(f"def compressor_{i}():\n    pass" for i in range(3))
    (ws / "src" / "a.py").write_text("class Compressor:\n    pass\n\n" + body)
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")

    cands = [n for n in graph()["nodes"] if n["kind"] == "candidate"]
    assert cands and all(c["data"]["suggested"] is True for c in cands)


def test_the_fingerprint_moves_only_when_the_graph_does(ws, onto_db):
    from montology_canvas import graph

    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    first = graph(with_scan=False)["fingerprint"]
    assert graph(with_scan=False)["fingerprint"] == first     # deterministic
    onto_db.add("run", "one execution of a task", kind="core", pos="noun")
    assert graph(with_scan=False)["fingerprint"] != first


# ── the bundle is generated material, and gets the gate that requires ───────

def test_a_workspace_without_sources_is_not_failed_for_lacking_them(ws, onto_db):
    """Every install that is not this repo ships the bundle without canvas/.
    Failing those would be failing them for not being us."""
    from montology_canvas import lint

    assert lint() == []


def test_a_bundle_built_from_older_sources_is_stale(tmp_path, monkeypatch):
    from montology_canvas import bundle

    canvas = tmp_path / "canvas"
    (canvas / "src").mkdir(parents=True)
    (canvas / "package.json").write_text('{"name":"probe"}')
    (canvas / "src" / "App.svelte").write_text("<p>one</p>")
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()

    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<html></html>")
    monkeypatch.setattr(bundle, "STATIC", static)
    monkeypatch.setattr(bundle, "STAMP", static / "BUILD.json")

    assert any("no provenance" in line for line in bundle.lint())   # never built
    bundle.stamp()
    assert bundle.lint()[0].startswith("canvas: bundle current")

    (canvas / "src" / "App.svelte").write_text("<p>two</p>")        # source moves…
    stale = bundle.lint()
    assert stale and stale[0].startswith("FAIL canvas") and "STALE" in stale[0]
    assert "just canvas" in stale[0]                                # the repair, attached


def test_the_fingerprint_ignores_what_carries_no_meaning(tmp_path, monkeypatch):
    """A dependency bump that changes no source changes no meaning. A hash that
    moves for reasons nobody can see is a hash people learn to ignore."""
    from montology_canvas import bundle

    canvas = tmp_path / "canvas"
    (canvas / "src").mkdir(parents=True)
    (canvas / "package.json").write_text('{"name":"probe"}')
    (canvas / "src" / "App.svelte").write_text("<p>one</p>")
    before = bundle.source_fingerprint(canvas)

    (canvas / "package-lock.json").write_text('{"lockfileVersion": 3}')
    (canvas / "node_modules").mkdir()
    (canvas / "node_modules" / "junk.js").write_text("// vendored")
    assert bundle.source_fingerprint(canvas) == before


# ── served on localhost, and only what belongs to it ────────────────────────

def _get(url):
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(url) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_the_canvas_serves_its_bundle_and_its_graph(ws, onto_db, monkeypatch):
    import json
    import threading

    import importlib

    from montology_canvas import serve

    # the package re-exports serve() over the module of the same name, so the
    # module has to be asked for by import rather than by attribute
    serve_mod = importlib.import_module("montology_canvas.serve")

    static = ws / "static"
    static.mkdir()
    (static / "index.html").write_text("<html>the canvas</html>")
    monkeypatch.setattr(serve_mod, "STATIC", static)

    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    url = {}
    ready = threading.Event()

    def note(u):
        url["at"] = u
        ready.set()

    t = threading.Thread(target=lambda: serve(open_browser=False, with_scan=False, _ready=note),
                         daemon=True)
    t.start()
    assert ready.wait(10)
    base = url["at"]

    assert _get(base) == (200, "<html>the canvas</html>")
    code, body = _get(base + "api/graph")
    assert code == 200 and json.loads(body)["stats"]["words"] == 1

    # the bundle is the ONLY thing this server may hand out
    code, body = _get(base + "../../../etc/passwd")
    assert code == 404 and "bundle" in body


def test_serving_without_a_bundle_says_how_to_get_one(ws, onto_db, monkeypatch):
    import importlib

    from montology_canvas import serve

    # the package re-exports serve() over the module of the same name, so the
    # module has to be asked for by import rather than by attribute
    serve_mod = importlib.import_module("montology_canvas.serve")

    monkeypatch.setattr(serve_mod, "STATIC", ws / "nothing-here")
    got = serve(open_browser=False)
    assert "not in this install" in got and "just canvas" in got


# ── writing: a face on the engine, never a second writer ───────────────────

def test_every_intent_names_a_function_the_cli_already_calls(ws, onto_db):
    """THE CANVAS HAS NO SQL. If an intent could do something no CLI command
    can, there would be two gates, and the second would drift from the first."""
    from montology_ontology.intents import _intents, catalogue

    for name, (fn, required, _) in _intents().items():
        assert callable(fn), name
        assert required, f"{name} takes nothing — nothing to author"
    assert {c["intent"] for c in catalogue()} == set(_intents())


def test_a_refusal_comes_back_in_the_engine_s_own_words(ws, onto_db):
    """Errors are data with the repair attached — that already works, and
    re-wording it in the browser would be a second gate."""
    from montology_ontology.intents import apply

    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")
    got = apply("word.add", {"name": "cell", "definition": "something else entirely"})
    assert got["ok"] is False
    assert got["line"].startswith("REFUSED") and "spoken for" in got["line"]
    assert "one word means one thing" in got["line"]


def test_the_laws_apply_identically_whichever_face_was_used(ws, onto_db):
    """A word authored on the canvas must be indistinguishable in the database
    from the same word authored at the CLI."""
    from montology_ontology.intents import apply
    from montology_ontology import words

    apply("word.add", {"name": "dossier", "definition": "what a run hands back",
                       "kind": "core", "pos": "noun", "test": "what came out"})
    onto_db.add("parcel", "what a run hands back", kind="core", pos="noun",
                test="what came out")

    rows = {w["name"]: w for w in words()}
    a, b = rows["dossier"], rows["parcel"]
    assert {k: a[k] for k in ("kind", "pos", "test")} == {k: b[k] for k in ("kind", "pos", "test")}


def test_an_unknown_intent_is_refused_with_the_known_ones(ws, onto_db):
    from montology_ontology.intents import apply

    got = apply("word.delete", {"name": "cell"})
    assert got["ok"] is False and "not an intent" in got["line"]
    assert "word.add" in got["line"]


def test_a_missing_required_field_never_reaches_the_engine(ws, onto_db):
    from montology_ontology.intents import apply

    got = apply("route.add", {"from_term": "output"})
    assert got["ok"] is False and "to_word" in got["line"]


def test_writes_need_the_token_the_page_alone_can_read(ws, onto_db, monkeypatch):
    """A cross-origin page can POST to loopback; it cannot READ the response
    that carries the token, because no CORS headers are sent. That is the whole
    CSRF story and it needs no cookie."""
    import json
    import threading
    import urllib.request

    import importlib

    from montology_canvas import serve

    serve_mod = importlib.import_module("montology_canvas.serve")

    static = ws / "static"
    static.mkdir()
    (static / "index.html").write_text("<html></html>")
    monkeypatch.setattr(serve_mod, "STATIC", static)
    onto_db.add("cell", "the box a run executes in", kind="core", pos="noun")

    url, ready = {}, threading.Event()
    threading.Thread(target=lambda: serve(open_browser=False, with_scan=False,
                                          _ready=lambda u: (url.setdefault("at", u), ready.set())),
                     daemon=True).start()
    assert ready.wait(10)
    base = url["at"]

    token = json.loads(urllib.request.urlopen(base + "api/graph").read())["token"]
    assert token

    def post(payload, headers):
        req = urllib.request.Request(base + "api/intent", data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        try:
            return urllib.request.urlopen(req).status, ""
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    body = {"intent": "word.add", "fields": {"name": "run", "definition": "one execution"}}
    assert post(body, {"Content-Type": "application/json"})[0] == 403
    # a form POST needs no preflight, so the content type is checked too
    assert post(body, {"Content-Type": "application/x-www-form-urlencoded",
                       "X-Monty-Token": token})[0] == 415
    assert post(body, {"Content-Type": "application/json", "X-Monty-Token": token})[0] == 200

    findings = json.loads(urllib.request.urlopen(base + "api/check?name=cell").read())
    assert findings["findings"] and "TAKEN" in findings["findings"][0]
