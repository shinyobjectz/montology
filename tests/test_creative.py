"""Formats, briefs, the frame law, and asset extraction — offline."""
import json

import pytest

from montology_crawl import brand as b
from montology_crawl import creative as c
from montology_crawl.audit import _images


@pytest.fixture()
def brands(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "BRANDS_DIR", tmp_path / "brands")
    monkeypatch.setattr(c, "BRANDS_DIR", tmp_path / "brands")
    return b


KIT = json.dumps({"url": "https://x.test", "colors": [{"hex": "#123456", "count": 5}],
                  "fonts": [{"family": "Inter", "count": 3}]})


def test_formats_registry_sane():
    assert ("medium-rectangle", 300, 250) == c.FORMATS["banner"][0][:3]
    names = {n for fam in c.FORMATS.values() for n, *_ in fam}
    assert len(names) == sum(len(f) for f in c.FORMATS.values()), "duplicate format names"
    assert set(c.DELIVERABLE_TYPES) == set(c.FORMATS)
    assert all(t in b.COMPONENT_TYPES for t in c.DELIVERABLE_TYPES.values())


def test_brief_is_grounded_or_carries_repair(brands):
    assert "run the pipeline first" in c.brief("ghost", "banner", "sell")
    brands.scaffold("acme", KIT)
    got = c.brief("acme", "banner", "drive trials")
    assert got.startswith("GROUNDED")
    spec = json.loads(got[got.find("{"):])
    assert spec["formats"][0]["width"] == 300
    assert "BRANDED INSTANTIATION" in spec["doctrine"]
    assert "#123456" in spec["brand_tokens"]
    assert "brand lint acme" in spec["then"]
    assert "must be one of" in c.brief("acme", "podcast", "x")


def test_frame_law(brands, tmp_path):
    brands.scaffold("acme", KIT)
    root = brands.BRANDS_DIR / "acme"
    (root / "deliverables").mkdir()
    good = root / "deliverables/Promo-300x250.tsx"
    good.write_text('import { palette } from "../tokens";\n'
                    'const W = 300; const H = 250;\n'
                    'export const Promo = () => <div style={{width: W, height: H, background: palette.c0}}/>;')
    brands.register("acme", "Promo", "ad-banner", "deliverables/Promo-300x250.tsx")
    assert brands.lint("acme")[-1].startswith("ok")
    bad = root / "deliverables/NoFrame.tsx"
    bad.write_text('import { palette } from "../tokens";\nexport const X = () => <div/>;')
    brands.register("acme", "NoFrame", "ad-banner", "deliverables/NoFrame.tsx")
    report = "\n".join(brands.lint("acme"))
    assert "named <name>-<w>x<h>.tsx" in report


def test_image_extraction_skips_junk():
    html = ('<img src="/hero.jpg"><img src="data:image/png;base64,x">'
            '<img src="/sprite-icons.png"><img src="/hero.jpg"><img src="/product.webp">')
    assert _images({"u": html}) == ["/hero.jpg", "/product.webp"]
