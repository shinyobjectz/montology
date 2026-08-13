"""Vitals, validated in full: every verdict, the precedence, every section
under absence, the machine shape, and the CI contract."""

import json

import numpy as np
import pytest

from montology_scan.vitals import build_vitals, render_vitals, vitals


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def _polyglot(ws, n=6):
    for i in range(n):
        (ws / f"m{i}.py").write_text(
            "class LedgerEntry:\n    pass\n\ndef post_invoice():\n    pass\n"
            "def invoice_total():\n    pass\n")


# ── the three verdicts ─────────────────────────────────────────────────

def test_untended_when_the_code_asks_and_nobody_answers(ws):
    _polyglot(ws)
    (ws / "app.css").write_text(".a { color: #061a1c; } .b { color: #06191b; }")
    r = build_vitals(ws)
    assert r["state"] == "untended"
    assert any("zero tokens" in x for x in r["reasons"])
    assert any("monty design ingest" in x for x in r["reasons"])


def test_drifting_names_every_leak(ws, onto_db):
    onto_db.token_add("brand", "color", "#061a1c")
    (ws / "app.css").write_text(
        ".a { color: #061a1c; } .b { color: #06191b; } .c { color: #123456; }")
    (ws / "App.tsx").write_text('export function A() { return <div className="p-[13px] flex gap-2 mt-1" />; }')
    r = build_vitals(ws)
    assert r["state"] == "drifting"
    assert any("2 unnamed color(s)" in x for x in r["reasons"])
    assert any("escape" in x for x in r["reasons"])


def test_tended_when_nothing_leaks(ws, onto_db):
    onto_db.add("ledger", "the append-only record", kind="core", pos="noun")
    onto_db.token_add("brand", "color", "#061a1c")
    (ws / "app.css").write_text(".a { color: #061a1c; }")
    r = build_vitals(ws)
    assert r["state"] == "tended"
    assert "nothing is leaking" in r["verdict"]


# ── precedence and composition ─────────────────────────────────────────

def test_untended_outranks_drifting(ws, onto_db):
    """A repo that has not started is a different fact from one losing."""
    _polyglot(ws)
    (ws / "app.css").write_text(".a { color: #061a1c; } .b { color: #06191b; }")
    (ws / "x.css").write_text(".x { color: #8a8a8a; }")
    r = build_vitals(ws)
    assert r["state"] == "untended"          # zero tokens + code asking
    assert r["design"]["unnamed"] >= 2        # the drifting facts still measured


def test_enforce_culture_failures_count_as_drifting(ws, onto_db):
    onto_db.add("ledger", "the record", kind="core", pos="noun")
    (ws / "a.py").write_text("class Ledger:\n    pass\n")
    (ws / ".monty" / "montology.toml").write_text('[scan]\ncollisions = "enforce"\n')
    r = build_vitals(ws)
    assert r["state"] == "drifting" and any("lint failure" in x for x in r["reasons"])


def test_advisory_collisions_count_without_failing_the_gate(ws, onto_db):
    onto_db.add("ledger", "the record", kind="core", pos="noun")
    (ws / "a.py").write_text("class Ledger:\n    pass\n")
    r = build_vitals(ws)
    assert r["gate"]["ok"] is True            # advisory culture: gate green…
    assert r["state"] == "drifting"           # …but the pulse says leaking
    assert any("advisory collision" in x for x in r["reasons"])


def test_duplicate_meanings_reach_the_verdict(ws, onto_db, monkeypatch):
    from montology_ontology import semantics

    def embed(texts):
        out = np.zeros((len(texts), 4))
        for i, t in enumerate(texts):
            out[i, 0 if "session" in t.lower() else 1 + (hash(t) % 3)] = 1.0
        return out

    monkeypatch.setattr(semantics, "EMBEDDER", embed)
    onto_db.add("thread", "a stateful session", kind="core", pos="noun")
    onto_db.add("convo", "the user's session", kind="core", pos="noun")
    r = build_vitals(ws)
    assert r["semantics"]["colliding_meanings"] == 1
    assert any("duplicate meaning" in x for x in r["reasons"])


# ── sections under absence ─────────────────────────────────────────────

def test_empty_repo_is_tended_and_every_section_degrades(ws):
    r = build_vitals(ws)
    assert r["state"] == "tended"             # nothing claimed, nothing leaking
    assert r["design"]["colors"] == 0
    assert r["guard"]["wired"] is False
    assert r["upstream"] is None
    lines = render_vitals(r)
    assert any("not wired" in line for line in lines)


def test_firewall_and_org_lines_appear_when_present(ws, onto_db):
    (ws / ".claude").mkdir()
    (ws / ".claude" / "settings.json").write_text(
        '{"hooks": {"PreToolUse": [{"hooks": [{"command": "monty guard"}]}]}}')
    (ws / ".monty" / "montology.toml").write_text(
        'name = "x"\n\n[ontology]\nupstream = "/some/org"\n')
    r = build_vitals(ws)
    assert r["guard"]["wired"] is True and r["upstream"] == "/some/org"
    out = "\n".join(render_vitals(r))
    assert "agents cannot write drift" in out and "/some/org" in out


def test_guard_compliance_line_rides_along(ws, onto_db):
    import montology_scan.guard as g

    g._log(ws, str(ws / "a.css"), "deny", ["rogue"])
    g._log(ws, str(ws / "a.css"), "allow", [])
    out = "\n".join(vitals(ws))
    assert "repair-following: 1/1" in out


# ── the machine shape and the CI contract ──────────────────────────────

def test_json_shape_is_the_dashboard_contract(ws, onto_db):
    from montology_scan import vitals_json

    r = json.loads(vitals_json(ws))
    for key in ("name", "state", "verdict", "reasons", "gate", "vocabulary",
                "design", "guard", "upstream"):
        assert key in r, key
    assert r["state"] in ("tended", "drifting", "untended")


def test_strict_exit_contract(ws, onto_db, monkeypatch):
    """--strict: exit 0 iff TENDED — the CI hook-up."""
    from typer.testing import CliRunner

    from montology_cli.main import app

    monkeypatch.chdir(ws)
    runner = CliRunner()
    assert runner.invoke(app, ["vitals", "--strict"]).exit_code == 0   # tended
    onto_db.token_add("brand", "color", "#061a1c")
    (ws / "app.css").write_text(".b { color: #06191b; }")
    assert runner.invoke(app, ["vitals", "--strict"]).exit_code == 1   # drifting
    assert runner.invoke(app, ["vitals"]).exit_code == 0               # report never fails
