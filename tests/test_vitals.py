"""The pulse: one verdict, reasons attached, repairs included."""

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def test_untended_when_the_code_asks_and_nobody_answers(ws):
    from montology_scan import vitals

    for i in range(6):
        (ws / f"m{i}.py").write_text(
            "class LedgerEntry:\n    pass\n\ndef post_invoice():\n    pass\n"
            "def invoice_total():\n    pass\n")
    (ws / "app.css").write_text(".a { color: #061a1c; } .b { color: #06191b; }")
    out = "\n".join(vitals(ws))
    assert "UNTENDED" in out
    assert "zero tokens" in out and "monty design ingest" in out


def test_drifting_names_every_leak(ws, onto_db):
    from montology_scan import vitals

    onto_db.token_add("brand", "color", "#061a1c")
    (ws / "app.css").write_text(".a { color: #061a1c; } .b { color: #06191b; }")
    out = "\n".join(vitals(ws))
    assert "DRIFTING" in out and "unnamed color" in out


def test_tended_when_nothing_leaks(ws, onto_db):
    from montology_scan import vitals

    onto_db.add("ledger", "the append-only record", kind="core")
    (ws / "app.css").write_text(".a { color: #061a1c; }")
    onto_db.token_add("brand", "color", "#061a1c")
    out = "\n".join(vitals(ws))
    assert "TENDED" in out and "nothing is leaking" in out
