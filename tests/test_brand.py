"""The brand library gate — every failure mode carries its repair."""
import json

import pytest

from montology_crawl import brand as b


@pytest.fixture()
def brands(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "BRANDS_DIR", tmp_path / "brands")
    return b


KIT = json.dumps({"url": "https://x.test", "colors": [{"hex": "#061a1c", "count": 38}],
                  "fonts": [{"family": "Inter", "count": 9}]})


def test_scaffold_register_lint_roundtrip(brands):
    assert brands.scaffold("acme", KIT).startswith("scaffolded")
    root = brands.BRANDS_DIR / "acme"
    assert 'c0: "#061a1c", // seen 38x' in (root / "tokens.ts").read_text()
    (root / "components").mkdir(exist_ok=True)
    (root / "components/Hero.tsx").write_text(
        'import { palette } from "../tokens";\nexport const Hero = () => <div style={{color: palette.c0}}/>;')
    assert brands.register("acme", "Hero", "hero", "components/Hero.tsx").startswith("registered")
    lines = brands.lint("acme")
    assert lines[-1].startswith("ok")


def test_gate_failure_modes(brands):
    brands.scaffold("acme", KIT)
    root = brands.BRANDS_DIR / "acme"
    assert "not in the taxonomy" in brands.register("acme", "X", "sidebar", "components/X.tsx")
    brands.register("acme", "Ghost", "hero", "components/Ghost.tsx")
    (root / "components/Hex.tsx").write_text('export const Hex = () => <div style={{color: "#fff"}}/>;')
    brands.register("acme", "Hex", "banner", "components/Hex.tsx")
    report = "\n".join(brands.lint("acme"))
    assert "missing on disk" in report
    assert "does not import the brand tokens" in report
    assert "literal hex color" in report
    assert report.splitlines()[-1].startswith("FAIL")


def test_bad_inputs_carry_repairs(brands):
    assert "lowercase-kebab" in brands.scaffold("Bad Name", KIT)
    assert "could not read the kit" in brands.scaffold("acme", "not json")
    assert "scaffold" in brands.register("acme", "H", "hero", "f.tsx")
    assert brands.lint("nope")[0].startswith("FAIL")
