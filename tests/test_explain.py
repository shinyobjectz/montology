"""The X-ray: composition tested deterministically — fake embedder, no drafts."""

import numpy as np
import pytest

from montology_ontology import semantics


@pytest.fixture()
def repo(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "billing").mkdir()
    (tmp_path / "web").mkdir()
    (tmp_path / "billing" / "ledger.py").write_text(
        "class LedgerEntry:\n    pass\n\ndef post_invoice():\n    pass\n")
    (tmp_path / "web" / "invoice.ts").write_text(
        "interface InvoiceRow { id: string }\nfunction renderInvoice(): void {}\n")
    (tmp_path / "web" / "app.css").write_text(
        ".x { color: #061a1c; } .y { color: #06191b; }")
    onto_db.add("invoice", "a bill issued to a client", kind="core", pos="noun")
    onto_db.token_add("brand", "color", "#061a1c")

    def embed(texts):
        out = np.zeros((len(texts), 6))
        for i, t in enumerate(texts):
            low = t.lower()
            if "invoice" in low or "bill" in low:
                out[i, 0] = 1.0
            elif "ledger" in low:
                out[i, 1] = 1.0
            else:
                out[i, 2 + (hash(low) % 4)] = 1.0
        return out

    monkeypatch.setattr(semantics, "EMBEDDER", embed)
    return tmp_path


def test_explain_composes_the_anatomy(repo):
    from montology_scan.explain import build, render_terminal

    r = build(repo, draft=False)
    assert r["surface"]["decls"] >= 4
    assert any(c["name"] == "invoicerow" or "invoice" in c["name"]
               for c in r["candidates"])
    # the invoice cluster gathers word + candidates, and spans both dirs
    inv = next(c for c in r["clusters"]
               if any(m["name"] == "invoice" for m in c["members"]))
    assert {m["kind"] for m in inv["members"]} == {"word", "candidate"}
    # candidate secretly the existing word -> contradiction carried in
    assert any("invoice" in line for line in r["contradictions"])

    lines = render_terminal(r)
    assert any("declarations" in line for line in lines)
    assert any(line.startswith("cluster:") for line in lines)


def test_explain_is_terminal_only(repo):
    from montology_scan import explain

    lines = explain(repo, draft=False)
    assert any("declarations" in line for line in lines)
    assert not (repo / ".monty" / "explain.html").exists()   # no decoration
