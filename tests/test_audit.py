"""The audit's extractors — fixture-driven, no network."""
from montology_crawl.audit import (TAILWIND_RE, _buttons, _colors, _fonts,
                                   _inventory, _tailwind)


def test_tailwind_regex_and_density():
    assert TAILWIND_RE.match("flex")
    assert TAILWIND_RE.match("hover:bg-blue-500")
    assert TAILWIND_RE.match("md:grid-cols-3")
    assert not TAILWIND_RE.match("navbar__inner")
    tw = _tailwind(['<div class="flex items-center p-4 hero-custom">'])
    assert tw["utility_density"] == 0.75 and tw["detected"]
    assert not _tailwind(['<div class="header main content">'])["detected"]


def test_colors_all_syntaxes():
    got = {c["value"] for c in _colors("a{color:#FFF;border:rgb(1, 2, 3);x:hsl(210, 40%, 20%)}")}
    assert {"#fff", "rgb(1,2,3)", "hsl(210,40%,20%)"} <= got


def test_fonts_scale_and_faces():
    css = ("@font-face{font-family:'BrandSans';src:url(x)} "
           "h1{font-family:BrandSans,sans-serif;font-size:3rem;font-weight:700}")
    f = _fonts(css, css)
    assert f["families"][0]["family"] == "BrandSans"
    assert f["size_scale"][0]["size"] == "3rem"
    assert "BrandSans" in f["font_faces"]


def test_inventory_types_and_cross_page_dedup():
    hero = '<section class="hero-x"><h1>Big</h1></section>'
    nav = '<nav class="top"><a href="/">x</a></nav>'
    pricing = '<section class="plans">only $9 per month</section>'
    inv = _inventory({"u1": hero + nav + pricing, "u2": hero + nav})
    by_type = {c["type"]: c for c in inv}
    assert by_type["hero"]["seen_on"] == ["u1", "u2"]      # deduped across pages
    assert by_type["nav"]["type"] == "nav"
    assert by_type["pricing"]["type"] == "pricing"
    assert all(c["source_html"] for c in inv)


def test_buttons_signature():
    got = _buttons('<a class="btn bg-ink rounded-full">go</a>' * 3)
    assert got and got[0]["count"] == 3
