"""The full pull: discovery reads the site's own links; the index degrades
with repairs when keys or weights are absent."""

import json

import httpx

from montology_crawl import socials


class _Resp:
    def __init__(self, text="", status=200):
        self.text, self.status_code, self.content = text, status, text.encode()
        self.headers = {"content-type": "text/html"}


def test_discover_reads_the_footer(monkeypatch):
    html = ('<a href="https://www.instagram.com/tecovas/">ig</a>'
            '<a href="https://www.tiktok.com/@tecovas">tt</a>'
            '<a href="https://twitter.com/intent/tweet">share-noise</a>'
            '<a href="https://x.com/tecovas">x</a>'
            '<a href="https://www.youtube.com/@tecovashq">yt</a>')
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp(html))
    got = socials.discover_socials("tecovas.com")
    assert got["instagram"] == "tecovas"
    assert got["tiktok"] == "tecovas"
    assert got["youtube"] == "tecovashq"
    assert got["x"] == "tecovas"  # the intent/ noise never wins


def test_walk_strings_finds_captions_anywhere():
    data = {"items": [{"node": {"caption": "boots!", "id": 1},
                       "video": {"title": "Spring drop"}}]}
    got = socials._walk_strings(data, socials._TEXT_KEYS)
    assert "boots!" in got and "Spring drop" in got


def test_index_without_book_carries_repair(tmp_path, monkeypatch):
    from montology_crawl import brand as b

    monkeypatch.setattr(b, "BRANDS_DIR", tmp_path / "brands")
    assert "monty brand scaffold" in socials.brand_index("ghost")


def test_index_without_key_reports_not_crashes(tmp_path, monkeypatch):
    from montology_crawl import brand as b

    monkeypatch.setattr(b, "BRANDS_DIR", tmp_path / "brands")
    monkeypatch.delenv("SCRAPECREATORS_API_KEY", raising=False)
    root = tmp_path / "brands" / "acme"
    (root / "data").mkdir(parents=True)
    (root / "manifest.json").write_text(json.dumps({"source": "https://x.test"}))
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp(
        '<a href="https://www.instagram.com/acme/">ig</a>'))
    report = socials.brand_index("acme")
    assert "discover: instagram:@acme" in report
    assert "SCRAPECREATORS_API_KEY" in report  # the repair, not a traceback
    assert (root / "data" / "socials.json").exists()
