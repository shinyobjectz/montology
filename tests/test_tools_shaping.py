"""Vendor output shaping and crawl extraction — fixture-driven, offline."""
import json

from montology_dataforseo.tools import _result_items, _table
from montology_scrapecreators.tools import _first_list_of_dicts, sc_api


def test_serp_envelope_and_table():
    data = {"tasks": [{"result": [{"items": [
        {"type": "organic", "rank_absolute": 1, "title": "Best pans", "url": "https://a.com/p", "domain": "a.com"},
        {"type": "paid", "rank_absolute": 0},
    ]}]}]}
    items = _result_items(data)
    organic = [i for i in items if i.get("type") == "organic"]
    out = _table(organic, [("rank", "rank_absolute"), ("title", "title"), ("url", "url")])
    lines = out.splitlines()
    assert lines[0].split() == ["rank", "title", "url"]
    assert "Best pans" in lines[1]
    assert isinstance(_result_items({"weird": 1}), str)  # surprise shape -> raw excerpt


def test_sc_helpers_and_passthrough_guards():
    nested = {"data": {"posts": [{"id": 1, "likes": 5}]}}
    assert _first_list_of_dicts(nested) == [{"id": 1, "likes": 5}]
    assert _first_list_of_dicts({"a": 1}) is None
    assert "routing table" in sc_api("tiktok/profile")          # missing /v prefix
    assert "JSON object" in sc_api("/v1/tiktok/profile", "{bad")


def test_brand_kit_hex_and_css_link_extraction(monkeypatch):
    from montology_crawl import tools as ct

    html = '<link rel="stylesheet" href="/a.css"><style>.x{color:#ff0000}</style>'

    class R:
        status_code = 200
        text = "body { color: #00ff00; font-family: BrandSans, sans-serif }"

    monkeypatch.setattr(ct, "_crawl", lambda url: ("md", html))
    import httpx
    monkeypatch.setattr(httpx, "get", lambda *a, **k: R())
    kit = json.loads(ct.brand_kit("https://x.test"))
    hexes = {c["hex"] for c in kit["colors"]}
    assert "#ff0000" in hexes and "#00ff00" in hexes      # inline AND linked
    assert all(not h.startswith("##") for h in hexes)      # the ## bug stays dead
    assert any(f["family"] == "BrandSans" for f in kit["fonts"])
