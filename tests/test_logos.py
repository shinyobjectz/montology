"""The logo chain: sources probe in quality order, misses answer with the
browse fallback, theSVG's JS module yields its SVG, provenance rides along."""

from __future__ import annotations

import json

import httpx

from montology_crawl import logos


class _Resp:
    def __init__(self, status=200, text="", json_data=None, ctype="image/svg+xml"):
        self.status_code = status
        self.text = text
        self.content = text.encode()
        self._json = json_data
        self.headers = {"content-type": ctype}

    def json(self):
        return self._json


def _fake_get(responses):
    def get(url, **kwargs):
        for frag, resp in responses.items():
            if frag in url:
                return resp
        return _Resp(status=404, ctype="text/plain")
    return get


def test_search_walks_the_chain_and_misses_answer_with_browse(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({}))
    out = logos.logo_search("nonexistentbrand")
    assert "svgrepo.com" in out  # a miss is a repair, never an empty hand

    monkeypatch.setattr(httpx, "get", _fake_get({
        "api.svgl.app": _Resp(json_data=[{
            "title": "Stripe", "route": "https://svgl.app/library/stripe.svg",
            "wordmark": {"light": "https://svgl.app/library/stripe-w-l.svg",
                         "dark": "https://svgl.app/library/stripe-w-d.svg"},
            "brandUrl": "https://stripe.com/brand",
        }]),
        "cdn.jsdelivr.net": _Resp(
            text='export const title = "Stripe";\nexport const hex = "635BFF";\n'
                 'export const svg = `<svg>thesvg</svg>`;\nexport const svg2 = 1;'
                 '\n// export const svg present',
            ctype="text/javascript"),
    }))
    hits = json.loads(logos.logo_search("stripe"))
    assert [h["source"] for h in hits] == ["svgl", "thesvg"]
    assert hits[0]["variants"]["wordmark-dark"].endswith("stripe-w-d.svg")
    assert "635BFF" in hits[1]["note"]  # the brand hex rides along


def test_fetch_extracts_thesvg_module_and_writes_provenance(tmp_path, monkeypatch):
    from montology_crawl import brand as b

    monkeypatch.setattr(b, "BRANDS_DIR", tmp_path / "projects")
    monkeypatch.setattr(httpx, "get", _fake_get({
        "cdn.jsdelivr.net": _Resp(
            text='export const title = "Stripe";\n'
                 'export const svg = `<svg fill="#635BFF">mark</svg>`;\n'
                 'export const svg_extra = "x";\n// export const svg here too',
            ctype="text/javascript"),
    }))
    out = logos.logo_fetch("acme", "stripe")
    assert "thesvg" in out
    written = tmp_path / "projects" / "acme" / "design" / "logos" / "stripe-thesvg-logo.svg"
    assert written.read_text() == '<svg fill="#635BFF">mark</svg>'
    prov = json.loads((written.parent / "provenance.json").read_text())
    assert prov[0]["source"] == "thesvg" and prov[0]["file"] == written.name


def test_unknown_variant_answers_with_what_exists(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({
        "api.svgl.app": _Resp(json_data=[{
            "title": "Notion", "route": "https://svgl.app/library/notion.svg"}]),
    }))
    out = logos.logo_fetch("acme", "notion", variant="wordmark")
    assert "Available: route" in out  # the repair names the real options
