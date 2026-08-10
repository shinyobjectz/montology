"""The capture converter: faithful HTML -> JSX, scripts stripped, URLs
absolute — and scaffold fills the registry with it, shadcn-shaped."""

import json

import pytest

from montology_crawl.capture import capture_component, component_name, html_to_jsx


def test_html_becomes_jsx():
    jsx = html_to_jsx(
        '<div class="hero" style="color: red; background-color: #fff">'
        '<img src="/logo.png" srcset="/a.png 1x"><br>'
        '<label for="q">Find</label><script>evil()</script>'
        '<button onclick="track()" disabled>Go</button></div>',
        base_url="https://x.test/page",
    )
    assert 'className="hero"' in jsx
    assert 'style={{color: "red", backgroundColor: "#fff"}}' in jsx
    assert '<img src="https://x.test/logo.png"' in jsx and "/>" in jsx
    assert "srcSet=" in jsx and "<br/>" in jsx
    assert 'htmlFor="q"' in jsx
    assert "evil" not in jsx and "onclick" not in jsx and "track()" not in jsx
    assert "<button disabled>Go</button>" in jsx


def test_jsx_braces_in_text_are_escaped():
    assert "&#123;" in html_to_jsx("<p>a {b} c</p>")


def test_component_names_are_type_canonical():
    assert component_name("hero") == "Hero"
    assert component_name("logo-row") == "LogoRow"
    assert component_name("email-header") == "EmailHeader"


def test_capture_module_shape():
    tsx = capture_component("Hero", "<section>hi</section>", "https://x.test")
    assert "export function Hero()" in tsx
    assert "<section>hi</section>" in tsx
    assert "CAPTURED from https://x.test" in tsx


def test_scaffold_fills_the_registry(tmp_path, monkeypatch):
    from montology_crawl import brand as b

    monkeypatch.setattr(b, "BRANDS_DIR", tmp_path / "brands")
    audit = json.dumps({
        "url": "https://x.test",
        "colors": [{"value": "#061a1c", "count": 38}],
        "fonts": {"families": [{"family": "Inter", "count": 9}]},
        "tailwind": {"detected": False},
        "components": [
            {"candidate": "home-hero", "type": "hero",
             "source_html": '<section class="h">Big</section>', "seen_on": ["https://x.test"]},
            {"candidate": "home-hero-2", "type": "hero", "source_html": "<section>Alt</section>"},
            {"candidate": "site-nav", "type": "nav", "source_html": "<nav>menu</nav>"},
        ],
    })
    got = b.scaffold("acme", audit)
    assert "3 captured component(s)" in got
    root = tmp_path / "brands" / "acme"
    # shadcn-shaped: one canonical file per type slot, extras numbered
    hero = (root / "design/components/captured/Hero.tsx").read_text()
    assert "export function Hero()" in hero and 'className="h"' in hero
    assert (root / "design/components/captured/Hero2.tsx").exists()
    assert (root / "design/components/captured/Nav.tsx").exists()
    manifest = json.loads((root / "manifest.json").read_text())
    assert [c["status"] for c in manifest["components"]] == ["captured"] * 3
    assert manifest["components"][0]["file"] == "design/components/captured/Hero.tsx"
    assert (root / "data/sources/home-hero.html").exists()
    assert (root / "data/audit.json").exists()
    # captured tier passes the gate without tokens imports
    assert b.lint("acme")[-1].startswith("ok")


def test_truncated_capture_still_compiles_shaped():
    # the audit caps source_html — captures end mid-tag in the wild
    jsx = html_to_jsx('<div><p class="a">Denim</p><ul><li>one<')
    assert jsx.endswith("</li></ul></div>")   # the stack closed the cut
    assert "&lt;" in jsx                       # the dangling < became text
    jsx2 = html_to_jsx("</p><div>orphan close before</div>")
    assert jsx2 == "<div>orphan close before</div>"
