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
app.add_typer(data_app, name="data")
app.add_typer(onto_app, name="onto")
app.add_typer(zoo_app, name="zoo")
app.add_typer(crawl_app, name="crawl")


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


@crawl_app.command("brand")
def crawl_brand(url: str) -> None:
    """A brand kit measured from a homepage: colors, fonts, logo, voice."""
    from montology_crawl import brand_kit

    typer.echo(brand_kit(url))
