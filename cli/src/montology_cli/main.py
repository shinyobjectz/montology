"""The montology CLI — written for marketers, exercised by agents.

Every message assumes the reader knows marketing and not Python: say what
happened, and when something is missing, say exactly what to do about it.
"""

from __future__ import annotations

import os

import typer

app = typer.Typer(
    name="montology",
    help="Marketing + monorepo + ontology. Data pulls, vocabulary checks, models, serving.",
    no_args_is_help=True,
)

data_app = typer.Typer(help="The taxonomy database.", no_args_is_help=True)
onto_app = typer.Typer(help="The vocabulary.", no_args_is_help=True)
zoo_app = typer.Typer(help="Local embedding models.", no_args_is_help=True)
crawl_app = typer.Typer(help="Local crawling (brand sites, pages).", no_args_is_help=True)
gen_app = typer.Typer(help="Generate skills, docs and words from instruments (Mellea).", no_args_is_help=True)
brand_app = typer.Typer(help="Brand component libraries: scaffold, register, lint.", no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(onto_app, name="onto")
app.add_typer(zoo_app, name="zoo")
app.add_typer(crawl_app, name="crawl")
app.add_typer(gen_app, name="gen")
app.add_typer(brand_app, name="brand")


def _gen_backend_ok() -> bool:
    import urllib.request

    if os.environ.get("MONTOLOGY_MODEL_URL"):
        return True
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


@app.command()
def doctor() -> None:
    """Is everything set up? Says what is missing and how to fix it."""
    from montology_ontology import DB_PATH

    checks = [
        (DB_PATH.exists(), "taxonomy database", "run: montology data pull"),
        (bool(os.environ.get("DATAFORSEO_LOGIN")), "DataForSEO login",
         "export DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD (app.dataforseo.com/api-access)"),
        (bool(os.environ.get("SCRAPECREATORS_API_KEY")), "ScrapeCreators key",
         "export SCRAPECREATORS_API_KEY (scrapecreators.com)"),
        (_gen_backend_ok(), "gen backend (optional — without one, gen hands drafts to the host agent)",
         "for autonomous gen: montology gen setup, or set MONTOLOGY_MODEL_URL"),
    ]
    for ok, name, repair in checks:
        mark = "ok " if ok else "MISSING"
        typer.echo(f"[{mark}] {name}" + ("" if ok else f" — {repair}"))


@app.command()
def serve(http: bool = typer.Option(False, help="Streamable HTTP instead of stdio.")) -> None:
    """Run the montology MCP server."""
    from montology_server.app import main as serve_main
    import sys

    sys.argv = ["montology-mcp"] + (["--http"] if http else [])
    serve_main()


@data_app.command("pull")
def data_pull(source: str = typer.Argument("", help="One source id, or empty for every core source.")) -> None:
    """Fetch taxonomies into the local database (seeds the vocabulary too)."""
    from montology_ontology import pull, seed

    typer.echo(seed())
    for line in pull(source or None):
        typer.echo(line)


@data_app.command("sources")
def data_sources() -> None:
    """Every taxonomy montology knows about, and the ruling on each."""
    from montology_ontology import SOURCES

    for s in SOURCES:
        typer.echo(f"{s.status:<8} {s.id:<22} {s.name}")
        typer.echo(f"         {s.why}")


@onto_app.command("check")
def onto_check(name: str) -> None:
    """Is this name free, ours, or an industry category already?"""
    from montology_ontology import check

    findings = check(name)
    if not findings:
        typer.echo(f"FREE  '{name}' is not spoken for.")
        raise typer.Exit(0)
    for f in findings:
        typer.echo(f)
    raise typer.Exit(1)


@onto_app.command("add")
def onto_add(
    name: str,
    definition: str,
    test: str = typer.Option("", help="The one-line 'what is it' test."),
    note: str = typer.Option("", help="Context worth keeping with the word."),
    owner: str = typer.Option("", help="The word this one lives inside (must exist)."),
    code: str = typer.Option("", help="A short dotted code, socialite-style (must be free)."),
) -> None:
    """Author a word of your own — check-first; a taken name is refused with findings."""
    from montology_ontology import add

    got = add(name, definition, test=test or None, note=note or None,
              owner=owner or None, code=code or None)
    typer.echo(got)
    raise typer.Exit(1 if got.startswith("REFUSED") else 0)


@onto_app.command("map")
def onto_map(word: str, target: str,
             note: str = typer.Option("", help="Why this mapping holds.")) -> None:
    """Pin a word to a taxonomy row: montology onto map flight iab-content:634"""
    from montology_ontology import map_word

    if ":" not in target:
        typer.echo("target is source:code, e.g. iab-content:634 or schemaorg:Organization")
        raise typer.Exit(1)
    source, code = target.split(":", 1)
    got = map_word(word, source, code, note or None)
    typer.echo(got)
    raise typer.Exit(1 if got.startswith("REFUSED") else 0)


@onto_app.command("mappings")
def onto_mappings(word: str = typer.Argument("", help="One word, or empty for all.")) -> None:
    """The word↔taxonomy joins on record."""
    from montology_ontology import mappings

    rows = mappings(word or None)
    if not rows:
        typer.echo("(no mappings yet — montology onto map WORD source:code)")
    for m in rows:
        typer.echo(f"{m['word']:<20} -> {m['source']}:{m['code']}  {m['path'] or m['name'] or '(row gone)'}")


@onto_app.command("list")
def onto_list(kind: str = typer.Argument("", help="Filter: core | adopted | custom.")) -> None:
    """The vocabulary — ours and yours (kind=custom is yours)."""
    from montology_ontology import words

    for w in words(kind or None):
        typer.echo(f"{w['kind']:<9} {w['name']:<24} {w['definition']}")


@zoo_app.command("list")
def zoo_list() -> None:
    """The curated models, from the zoo database."""
    from montology_zoo import DB_PATH, connect, seed

    if not DB_PATH.exists():
        seed()
    conn = connect()
    for m in conn.execute("SELECT * FROM model ORDER BY status, task, id"):
        arts = conn.execute(
            "SELECT format, quant, bytes FROM artifact WHERE model_id=?", (m["id"],)
        ).fetchall()
        shapes = ", ".join(
            f"{a['format']}/{a['quant']}"
            + (f" {a['bytes'] / 1e6:.0f}MB" if a["bytes"] else " (unsynced)")
            for a in arts
        ) or "—"
        typer.echo(f"{m['status']:<9} {m['id']:<24} {m['task']:<12} {shapes}")
        typer.echo(f"{'':<9} {m['note']}")


@zoo_app.command("sync")
def zoo_sync() -> None:
    """Measure every artifact against the HuggingFace API (sizes, architecture)."""
    from montology_zoo import seed, sync

    typer.echo(seed())
    for line in sync():
        typer.echo(line)


@zoo_app.command("fit")
def zoo_fit() -> None:
    """What runs on THIS machine — measured sizes, documented estimate math."""
    from montology_zoo import fit_report

    for line in fit_report():
        typer.echo(line)


@zoo_app.command("embed")
def zoo_embed(model_id: str, texts: list[str]) -> None:
    """Embed one or more texts; prints dims and the pairwise similarity matrix."""
    from montology_zoo import ZooError, embed_text

    try:
        v = embed_text(model_id, list(texts))
    except ZooError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    typer.echo(f"{v.shape[0]} texts -> {v.shape[1]} dims")
    if len(texts) > 1:
        sims = v @ v.T
        for i, a in enumerate(texts):
            for j in range(i + 1, len(texts)):
                typer.echo(f"  {sims[i, j]:+.3f}  {a[:36]!r} ~ {texts[j][:36]!r}")


@zoo_app.command("transcribe")
def zoo_transcribe(wav: str, model_id: str = typer.Option("asr-whisper-base", "--model")) -> None:
    """Transcribe an audio file via whisper.cpp on the zoo's model."""
    from montology_zoo import ZooError, transcribe

    try:
        typer.echo(transcribe(model_id, wav))
    except ZooError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@zoo_app.command("topics")
def zoo_topics(file: str, model_id: str = typer.Option("text-minilm", "--model"),
               min_size: int = typer.Option(5, "--min-size")) -> None:
    """Discover topics in a text file (one document per line)."""
    import pathlib as _pl

    from montology_zoo import ZooError
    from montology_zoo.topics import discover_topics

    lines = [l.strip() for l in _pl.Path(file).read_text().splitlines() if l.strip()]
    try:
        for t_ in discover_topics(lines, model_id=model_id, min_topic_size=min_size):
            typer.echo(f"{t_['count']:>4}  {t_['topic']}  {', '.join(t_['terms'])}")
    except ZooError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@zoo_app.command("pull")
def zoo_pull(model_id: str) -> None:
    """Download a model's weights (the smallest synced artifact)."""
    from montology_zoo.pull import pull

    typer.echo(pull(model_id))


@app.command()
def sql(query_text: str = typer.Argument(..., help="SQL over your data + the registries.")) -> None:
    """Query the warehouse (DuckDB): your loaded files, plus ontology.* and zoo.*."""
    from montology_warehouse import query

    typer.echo(query(query_text))


@data_app.command("load")
def data_load(path: str, table: str) -> None:
    """Load a CSV/Parquet/JSON file into a warehouse table for SQL."""
    from montology_warehouse import load_file

    typer.echo(load_file(path, table))


@crawl_app.command("setup")
def crawl_setup() -> None:
    """One-time: install the crawler's browser (Chromium via Playwright)."""
    from montology_crawl.tools import setup

    typer.echo(setup())


@crawl_app.command("page")
def crawl_page(url: str) -> None:
    """One page as LLM-ready markdown."""
    from montology_crawl import fetch_page

    typer.echo(fetch_page(url))


@crawl_app.command("audit")
def crawl_audit(url: str, max_pages: int = typer.Option(4, "--pages")) -> None:
    """The COMPLETE brand surface, multi-page: colors, fonts, tailwind, spacing,
    breakpoints, buttons, and a typed component inventory with source HTML."""
    from montology_crawl import brand_audit

    typer.echo(brand_audit(url, max_pages=max_pages))


@crawl_app.command("brand")
def crawl_brand(url: str) -> None:
    """A brand kit measured from a homepage: colors, fonts, logo, voice."""
    from montology_crawl import brand_kit

    typer.echo(brand_kit(url))


@gen_app.command("skill")
def gen_skill_cmd(
    name: str = typer.Argument(..., help="Skill to (re)generate: " ),
    write: bool = typer.Option(False, "--write", help="Write skills/<name>/SKILL.md (default: print)."),
    try_local: bool = typer.Option(False, "--try-local", help="Re-attempt the local piecewise path even if this model has a refusal on record."),
) -> None:
    """Generate a package's skill from its instruments — AST surface, warehouse shape, house rules."""
    from montology_gen import gen_skill

    typer.echo(gen_skill(name, write=write, try_local=try_local))


@gen_app.command("word")
def gen_word_cmd(name: str, context: str = typer.Option("", help="Usage context grounding the definition.")) -> None:
    """Propose an ontology word, law-checked (free, one meaning, no vendors)."""
    from montology_gen import gen_word

    typer.echo(gen_word(name, context))


@gen_app.command("setup")
def gen_setup_cmd() -> None:
    """One-time: pull the atomic-tier model (gemma3:270m, 292 MB). Bodies need no model — the host agent drafts them."""
    import shutil
    import subprocess

    if not shutil.which("ollama"):
        typer.echo("Ollama is not installed. Repair: install it from ollama.com, then rerun "
                   "`montology gen setup`. (Or set MONTOLOGY_MODEL_URL to any "
                   "OpenAI-compatible endpoint instead — no Ollama needed.)")
        raise typer.Exit(1)
    r = subprocess.run(["ollama", "pull", "gemma3:270m"], capture_output=True, text=True)
    typer.echo("atomic tier ready (gemma3:270m, 292 MB); bodies use the host agent" if r.returncode == 0
               else f"pull failed: {r.stderr[-300:]}")
    raise typer.Exit(r.returncode)


@gen_app.command("docs")
def gen_docs_cmd(write: bool = typer.Option(False, "--write"),
                 prose: bool = typer.Option(False, "--prose",
                                            help="Also generate per-package paragraphs (needs a model).")) -> None:
    """Regenerate the README's package map (deterministic); --prose adds paragraphs."""
    from montology_gen.engine import gen_docs

    typer.echo(gen_docs(write=write, prose=prose))


@gen_app.command("lint")
def gen_lint_cmd() -> None:
    """Deterministic, model-free: every skill against its laws; the no-prompt ban."""
    from montology_gen import lint

    lines = lint()
    for line in lines:
        typer.echo(line)
    raise typer.Exit(1 if any(l.startswith("FAIL") for l in lines) else 0)


@brand_app.command("scaffold")
def brand_scaffold_cmd(brand: str, kit: str = typer.Argument(..., help="brand_kit JSON output, or a path to it.")) -> None:
    """brands/<brand>/ from a measured kit: tokens.ts + manifest + README."""
    from montology_crawl import brand_scaffold

    got = brand_scaffold(brand, kit)
    typer.echo(got)
    raise typer.Exit(0 if got.startswith("scaffolded") else 1)


@brand_app.command("register")
def brand_register_cmd(brand: str, name: str, ctype: str, file: str,
                       source: str = typer.Option("", help="The URL the component derives from.")) -> None:
    """Add a component to the brand's manifest (type from the component taxonomy)."""
    from montology_crawl import brand_register

    got = brand_register(brand, name, ctype, file, source)
    typer.echo(got)
    raise typer.Exit(0 if got.startswith("registered") else 1)


@brand_app.command("assets")
def brand_assets_cmd(brand: str, audit: str = typer.Argument(..., help="brand_audit JSON or a path to it.")) -> None:
    """Download the brand's images into brands/<brand>/assets/ (bounded, with ledger)."""
    from montology_crawl import brand_assets

    typer.echo(brand_assets(brand, audit))


@brand_app.command("brief")
def brand_brief_cmd(brand: str, deliverable: str,
                    goal: str = typer.Option(..., "--goal", help="What the creative must achieve.")) -> None:
    """The grounded creative brief: banner | social | video | email | landing."""
    from montology_crawl import brand_brief

    got = brand_brief(brand, deliverable, goal)
    typer.echo(got)
    raise typer.Exit(1 if not got.startswith("GROUNDED") else 0)


@brand_app.command("lint")
def brand_lint_cmd(brand: str) -> None:
    """The deterministic gate: manifest, files, types, tokens-not-hex."""
    from montology_crawl import brand_lint

    lines = brand_lint(brand)
    for line in lines:
        typer.echo(line)
    raise typer.Exit(1 if any(l.startswith("FAIL") for l in lines) else 0)
