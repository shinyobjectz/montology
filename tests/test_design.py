"""Design values as vocabulary: the style surface, the drift laws, adoption."""

from pathlib import Path

import pytest


@pytest.fixture()
def styled(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "app.css").write_text(
        ".btn { color: #061a1c; padding: 12px; }\n"
        ".card { background: #06191b; margin: 13px; }\n"   # Δ3 from the token blue
        ".hero { color: rgb(6, 26, 28); font-family: Inter, sans-serif; }\n"
        ":root { --brand: #061a1c; }\n")
    (tmp_path / "App.tsx").write_text(
        'export function App() {\n'
        '  return <div className="btn ghost-panel p-[13px] text-[#ff0001]"\n'
        '              style={{color: "#ff0000", margin: "13px"}}>x</div>;\n'
        '}\n'
        'export function B() { return <div className="ghost-panel">y</div>; }\n')
    return tmp_path


def test_style_surface_measures_everything(styled):
    from montology_scan import style_surface

    s = style_surface(styled)
    assert s["colors"]["#061a1c"] == 3          # css hex + rgb() + custom prop
    assert s["colors"]["#ff0001"] == 1          # the tailwind arbitrary color
    assert s["colors"]["#ff0000"] == 1          # the style-object literal
    assert "btn" in s["defined_classes"] and "ghost-panel" in s["used_classes"]
    assert s["spacing"]["13px"] >= 2
    assert "Inter" in s["fonts"]
    assert any("p-[13px]" in a["class"] for a in s["arbitrary"])
    assert s["where"]["#06191b"].startswith("app.css:")


def test_design_lint_names_the_nearest_token(styled, onto_db):
    from montology_scan import design_lint

    onto_db.token_add("brand-primary", "color", "#061a1c")
    report = "\n".join(design_lint(styled))
    assert "rogue color #06191b" in report and "brand-primary" in report and "Δ" in report
    assert "ghost-panel" in report            # used, defined nowhere
    assert "arbitrary" in report              # the escapes counted
    assert "FAIL" not in report               # advisory by default


def test_enforce_promotes_rogues_to_failures(styled, onto_db):
    from montology_scan import design_lint

    onto_db.token_add("brand-primary", "color", "#061a1c")
    (styled / ".monty" / "montology.toml").write_text("[design]\nenforce = true\n")
    assert any(r.startswith("FAIL design: rogue color") for r in design_lint(styled))


def test_without_tokens_statistics_not_failures(styled):
    from montology_scan import design_lint

    report = design_lint(styled)
    assert not any("rogue" in r for r in report)   # nothing to align to yet
    assert any(r.startswith("design:") for r in report)


def test_candidates_are_adoption_ready(styled):
    from montology_scan import design_candidates

    got = design_candidates(styled)
    assert "#061a1c" in got and "monty design token" in got


def test_token_contract(onto_db):
    assert onto_db.token_add("brand-primary", "color", "#061a1c").startswith("token")
    refused = onto_db.token_add("brand-primary", "color", "#ffffff")
    assert refused.startswith("REFUSED") and "one" in refused.lower()
    assert onto_db.token_add("x", "hue", "#fff").startswith("REFUSED")
    assert onto_db.tokens("color")[0]["value"] == "#061a1c"


def test_tailwind_v4_theme_ingests_as_tokens(tmp_path, onto_db, monkeypatch):
    from montology_scan import ingest_theme

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "theme.css").write_text(
        "@theme { --color-brand: #061a1c; --color-danger: #b91c1c;\n"
        "  --spacing-lg: 2rem; --font-display: Inter; }\n")
    got = ingest_theme(tmp_path)
    assert "ingested 4 token(s)" in got
    toks = {t["name"]: t for t in onto_db.tokens()}
    assert toks["brand"]["value"] == "#061a1c" and toks["brand"]["category"] == "color"
    assert toks["lg"]["category"] == "space"
    assert toks["display"]["category"] == "font"
    # ingest is idempotent — never overwrites
    assert "0 token(s)" in ingest_theme(tmp_path).replace("ingested 0", "0")


def test_tailwind_v3_config_ingests_nested_names(tmp_path, onto_db, monkeypatch):
    from montology_scan import tailwind_theme

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "tailwind.config.js").write_text(
        'module.exports = { theme: { extend: {\n'
        '  colors: { brand: { 500: "#061a1c", light: "#eef2f2" }, danger: "#b91c1c" },\n'
        '  spacing: { 18: "4.5rem" } } } }\n')
    theme = {t["name"]: t for t in tailwind_theme(tmp_path)}
    assert theme["brand-500"]["value"] == "#061a1c"
    assert theme["brand-light"]["category"] == "color"
    assert theme["danger"]["value"] == "#b91c1c"
    assert theme["18"]["category"] == "space"


def test_recipes_mine_recurring_compositions(tmp_path, onto_db, monkeypatch):
    from montology_scan import recipe_candidates

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    card = "rounded-lg border bg-white p-4 shadow-sm"
    (tmp_path / "A.tsx").write_text("".join(
        f'export function C{i}() {{ return <div className="{card}">x</div>; }}\n'
        for i in range(4)))
    got = recipe_candidates(tmp_path, min_uses=3)
    assert "4x" in got and "rounded-lg" in got and "monty design token" in got
    # naming it silences the candidate
    normalized = " ".join(sorted(card.split()))
    onto_db.token_add("card", "recipe", normalized)
    assert "no recurring unnamed recipes" in recipe_candidates(tmp_path, min_uses=3)
