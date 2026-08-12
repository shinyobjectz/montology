"""The montology CLI — an ontology context layer for any monorepo.

Every message assumes the reader is naming things in a codebase and wants
to be told, quickly, whether a name is safe and what to do when it is not.
Errors carry their repair.
"""

from __future__ import annotations

import json
import os

import typer


def run() -> None:
    """The console entry: load the workspace .env, run the app, and turn a
    missing workspace into its repair instead of a traceback."""
    from montology_core import WorkspaceError, load_env

    load_env()
    try:
        app()
    except WorkspaceError as e:
        typer.echo(str(e), err=True)
        raise SystemExit(2) from None


app = typer.Typer(
    name="montology",
    help="The ontology layer: a vocabulary as a database, enforced against the code.",
    no_args_is_help=True,
)

onto_app = typer.Typer(help="The vocabulary: check, add, amend, rule, list.", no_args_is_help=True)
design_app = typer.Typer(help="Design values as vocabulary: tokens, drift, candidates.", no_args_is_help=True)
app.add_typer(onto_app, name="onto")
app.add_typer(design_app, name="design")


@app.command()
def init(path: str = typer.Argument(".", help="The repo to initialize (default: here)."),
         name: str = typer.Option("", "--name", help="Workspace name (default: the repo's)."),
         yes: bool = typer.Option(False, "--yes", help="Non-interactive: no prompts."),
         json_out: bool = typer.Option(False, "--json", help="Machine summary (implies --yes)."),
         agents: str = typer.Option("", "--agents", help="Harnesses to wire: claude,cursor,codex (default: detected)."),
         from_: str = typer.Option("", "--from", help="Inherit an org ontology (git URL / path / .db URL).")) -> None:
    """Initialize the ontology layer into this repo: .monty/, agent wiring, the words skill."""
    from .init import init_command

    init_command(path, name, yes or json_out, json_out, agents, from_)


@app.command()
def doctor() -> None:
    """Is everything set up? Says what is missing and how to fix it."""
    import shutil as _shutil

    from montology_core import find_root
    from montology_ontology import db_path, words

    root = find_root()
    checks = [
        (root is not None, "workspace",
         "run `monty init` in your repo — every command needs a root (.monty/)"),
        (root is not None and db_path().exists(), "ontology database",
         "run `monty init` (or `monty onto add` your first word)"),
        (root is not None and (root / ".claude" / "skills" / "words" / "SKILL.md").exists(),
         "words skill", "run `monty sync` — the agent reads the vocabulary from it"),
        (_shutil.which("ast-grep") is not None or _shutil.which("sg") is not None,
         "ast-grep (structural search)", "brew install ast-grep"),
        (_gen_backend_ok(), "gen backend (optional — definitions draft locally when present)",
         "install Ollama and `ollama pull gemma3:270m`, or set MONTOLOGY_MODEL_URL"),
    ]
    if root is not None:
        checks.insert(2, (bool(words()), "vocabulary",
                          "empty — `monty scan --candidates` lists what the code is asking for"))
    from ._ui import emit

    for ok, label, repair in checks:
        mark = "ok " if ok else "MISSING"
        emit(f"[{mark}] {label}" + ("" if ok else f" — {repair}"))


def _gen_backend_ok() -> bool:
    import urllib.request

    if os.environ.get("MONTOLOGY_MODEL_URL"):
        return True
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


@onto_app.command("check")
def onto_check(name: str) -> None:
    """Is this name free, ours, or ruled on? Run BEFORE naming anything."""
    from montology_ontology import check

    from ._ui import emit, emit_all

    findings = check(name)
    if not findings:
        emit(f"FREE  '{name}' is not spoken for.")
        raise typer.Exit(0)
    emit_all(findings)
    raise typer.Exit(1)


@onto_app.command("add")
def onto_add(
    name: str,
    definition: str,
    test: str = typer.Option("", help="The one-line 'what is it' test."),
    note: str = typer.Option("", help="Context worth keeping with the word."),
    kind: str = typer.Option("custom", help="core | inner | adopted | custom."),
    owner: str = typer.Option("", help="The word this one lives inside (must exist)."),
    code: str = typer.Option("", help="A dotted code (prefix must resolve)."),
) -> None:
    """Author a word — check-first; a taken name is refused with findings."""
    from montology_ontology import add

    from ._ui import emit

    got = add(name, definition, test=test or None, note=note or None, kind=kind,
              owner=owner or None, code=code or None)
    emit(got)
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    from montology_gen import sync as _sync

    emit(_sync())


@onto_app.command("amend")
def onto_amend(
    name: str,
    definition: str | None = typer.Option(None, "--definition", help="What the word means, corrected."),
    test: str | None = typer.Option(None, "--test", help="The one-line 'what is it' test, corrected."),
    note: str | None = typer.Option(None, "--note", help="The kept context (pass \"\" to clear it)."),
    code: str | None = typer.Option(None, "--code", help="Re-file under a dotted code (prefix must resolve)."),
    owner: str | None = typer.Option(None, "--owner", help="Move it inside another word (must exist)."),
    why: str = typer.Option("", "--why", help="Why the record changed — the ledger keeps it."),
) -> None:
    """Correct a word's recorded text — the name stays, the old text is ledgered."""
    from montology_ontology import amend

    from ._ui import emit, emit_all

    got = amend(name, definition=definition, test=test, note=note, code=code,
                owner=owner, why=why or None)
    emit_all(got.splitlines())
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    from montology_gen import sync as _sync

    emit(_sync())


@onto_app.command("rule")
def onto_rule(dont_say: str, say: str,
              why: str = typer.Option("", help="Why the ruling holds.")) -> None:
    """Record an overload ruling: do not say X, say Y."""
    from montology_gen import sync as _sync
    from montology_ontology import rule

    from ._ui import emit

    emit(rule(dont_say, say, why or None))
    emit(_sync())


@onto_app.command("collide")
def onto_collide(term: str, theirs: str = typer.Argument(..., help="Whose word collides (the framework/system)."),
                 meaning: str = typer.Argument(..., help="What the term means in THEIR system."),
                 ruling: str = typer.Argument(..., help="Which side moved, and what to say now.")) -> None:
    """Record a boundary collision ruling: whose word, what theirs means, who moved."""
    from montology_gen import sync as _sync
    from montology_ontology import collide

    from ._ui import emit

    emit(collide(term, theirs, meaning, ruling))
    emit(_sync())


@onto_app.command("rename")
def onto_rename(was: str, now: str,
                why: str = typer.Argument(..., help="Required — a rename without a reason is churn.")) -> None:
    """Rename a word and ledger it — the old name retires, old material stays readable."""
    from montology_gen import sync as _sync
    from montology_ontology import rename_word

    from ._ui import emit

    got = rename_word(was, now, why)
    emit(got)
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    emit(_sync())
    from montology_scan import migrate as _migrate

    typer.echo("where the code still says the old name:")
    typer.echo(_migrate(was, now))


@onto_app.command("pull")
def onto_pull(source: str = typer.Argument("", help="Git URL, workspace path, or http(s) .db URL — remembered once given.")) -> None:
    """Inherit the ORG vocabulary: one ontology, every repo. Local words survive."""
    from montology_gen import sync as _sync
    from montology_ontology import pull

    from ._ui import emit, emit_all

    got = pull(source or None)
    emit_all(got.splitlines())
    if got.startswith(("REFUSED", "no upstream")):
        raise typer.Exit(1)
    emit(_sync())


@onto_app.command("similar")
def onto_similar(query: str,
                 top: int = typer.Option(8, "--top", help="How many neighbors.")) -> None:
    """The words nearest a name or definition — the meaning may already have a word."""
    from rich.text import Text

    from ._ui import console
    from montology_ontology import semantic_similar

    for line in semantic_similar(query, top).splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3 and parts[0].replace(".", "").isdigit():
            score = float(parts[0])
            hot = score >= 0.5
            row = Text(f"{parts[0]:>6}  ", style="bold yellow" if hot else "dim")
            row.append(f"{parts[1]:<22}", style="bold" if hot else "")
            row.append(parts[2], style="dim")
            console.print(row)
            if hot:
                console.print(Text("        ↑ this meaning may already have its word",
                                   style="dim yellow"))
        else:
            console.print(line)


@onto_app.command("audit")
def onto_audit(threshold: float = typer.Option(0.70, "--threshold", help="Cosine above which meanings collide.")) -> None:
    """The semantic audit (advisory, always): two-words-one-meaning, org/local
    doubles, misfiled owners, candidates that already exist."""
    from ._ui import emit_all
    from montology_ontology import semantic_audit
    from montology_scan import candidates as scan_candidates

    try:
        cands = scan_candidates(top=10)
    except Exception:  # noqa: BLE001 — the audit stands without the scan
        cands = []
    emit_all(semantic_audit(threshold, cands).splitlines())


@onto_app.command("list")
def onto_list(kind: str = typer.Argument("", help="Filter: core | inner | adopted | custom.")) -> None:
    """The vocabulary as rows."""
    from montology_ontology import words

    from ._ui import console

    rows = words(kind or None)
    if not rows:
        typer.echo("(no words yet — monty onto add NAME \"definition\", or monty scan --candidates)")
        return
    from rich.table import Table

    table = Table(box=None, header_style="bold cyan", pad_edge=False)
    for col in ("kind", "word", "code", "is"):
        table.add_column(col)
    for w in rows:
        table.add_row(w["kind"], f"[bold]{w['name']}[/bold]", w["code"] or "—", w["definition"])
    console.print(table)


@app.command()
def scan(candidates: int = typer.Option(0, "--candidates", help="List the top N words the code is asking for.")) -> None:
    """The multiast sweep: what the code declares, measured."""
    from montology_core import workspace_root
    from montology_scan import candidates as scan_candidates
    from montology_scan import declarations

    if candidates:
        rows = scan_candidates(top=candidates)
        if not rows:
            typer.echo("no candidates — every recurring declared name has a word (or is noise)")
        for c in rows:
            typer.echo(f"{c['count']:>4}x  {c['name']:<28} ({c['kind']})  — free: monty onto check {c['name']}")
        return
    got = declarations(workspace_root())
    by_lang: dict[str, int] = {}
    for d in got["decls"]:
        by_lang[d["lang"]] = by_lang.get(d["lang"], 0) + 1
    typer.echo(f"{len(got['decls'])} declarations in {got['files']} files"
               + (f" ({got['errors']} unparsable)" if got["errors"] else ""))
    for lang, n in sorted(by_lang.items(), key=lambda kv: -kv[1]):
        typer.echo(f"  {lang:<12} {n}")
    for lang, n in got["skipped_langs"].items():
        typer.echo(f"  {lang:<12} {n} file(s) SKIPPED — no declaration query yet")


@app.command()
def lint() -> None:
    """The gate: collisions, code resolution, design drift, prose drift. Exit 1 on FAIL."""
    from montology_gen import lint as gen_lint
    from montology_scan import design_lint, lint as scan_lint

    from ._ui import emit_all

    lines = scan_lint() + design_lint() + gen_lint()
    emit_all(lines)
    if any(line.startswith("FAIL") or line.endswith("FAILED") for line in lines):
        raise typer.Exit(1)


@onto_app.command("route")
def onto_route(
    term: str = typer.Argument("", help="The term to route AWAY from."),
    to: str = typer.Option("", "--to", help="The word to say instead."),
    register: str = typer.Option("all", "--in", help="code | surface | prose | all."),
    scope: str = typer.Option("", "--scope", help="Path glob, overriding the register."),
    why: str = typer.Option("", "--why", help="Why the ruling exists."),
    drafts: bool = typer.Option(False, "--drafts", help="What existing rulings imply, unwritten."),
    adopt_all: bool = typer.Option(False, "--adopt-all", help="Write every draft, unconfirmed."),
    drop: bool = typer.Option(False, "--drop", help="Remove the route."),
) -> None:
    """Say this, not that — HERE. The register is what makes a ruling enforceable."""
    from montology_ontology import route_add, route_drafts, route_drop, routes

    from ._ui import emit_all

    if drafts or adopt_all:
        ds = route_drafts()
        if not ds:
            typer.echo("no drafts — every ruling is already routed.")
            raise typer.Exit(0)
        if adopt_all:
            for d in ds:
                typer.echo(route_add(d["from_term"], d["to_word"],
                                     register=d["register"], why=d.get("why"),
                                     ruled_on=d.get("ruled_on"), origin=d["source"]))
            typer.echo(f"\nadopted {len(ds)} draft(s). The ones left at register "
                       "'all' cannot gate until you scope them — `monty onto stale` "
                       "lists them.")
            raise typer.Exit(0)
        lines = [f"{len(ds)} draft route(s) from your existing rulings — "
                 "confirm the ones that are right:", ""]
        for d in ds:
            mark = "" if d["known_target"] else "  [target is not a word yet]"
            hint = f"  (from: {d['hint']})" if d["hint"] else ""
            lines.append(f"  {d['from_term']!r} → {d['to_word']!r} in {d['register']}{hint}{mark}")
            lines.append(f"      monty onto route {d['from_term']!r} --to {d['to_word']!r} "
                         f"--in {d['register']}")
        lines += ["", "Adopt them all with --adopt-all, then scope the ones "
                  "that landed on 'all'."]
        emit_all(lines)
        raise typer.Exit(0)

    if not term:
        rs = routes()
        if not rs:
            typer.echo("no routes yet — `monty onto route --drafts` reads what your "
                       "existing rulings already imply.")
            raise typer.Exit(0)
        emit_all([f"  {r['from_term']!r} → {r['to_word']!r}  in {r['register']}"
                  + (f" ({r['scope']})" if r["scope"] else "") for r in rs])
        raise typer.Exit(0)

    if not to:
        typer.echo("REFUSED — say where it goes: --to WORD")
        raise typer.Exit(1)
    if drop:
        typer.echo(route_drop(term, to, register))
        raise typer.Exit(0)
    line = route_add(term, to, register=register, scope=scope or None, why=why or None)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("routes")
def onto_routes() -> None:
    """Where terms land: chains, orphans, and rulings that contradict."""
    from montology_ontology import render_routes, route_analyse

    from ._ui import emit_all

    lines = render_routes(route_analyse())
    emit_all(lines)
    if any(line.startswith("FAIL") for line in lines):
        raise typer.Exit(1)


@onto_app.command("stale")
def onto_stale(
    strict: bool = typer.Option(False, "--strict", help="Exit 1 on any live stale term."),
) -> None:
    """Deprecated terms still in use, searched only where the ruling applies."""
    from montology_scan import render_stale, stale_terms

    from ._ui import emit_all

    r = stale_terms()
    emit_all(render_stale(r))
    if strict and r["findings"]:
        raise typer.Exit(1)


@onto_app.command("health")
def onto_health(
    verbose: bool = typer.Option(False, "--verbose", help="Every unnamed word, not the first few."),
) -> None:
    """Is each word carried by anything — or is it a name alone?"""
    from montology_scan import render_health, word_health

    from ._ui import emit_all

    emit_all(render_health(word_health(), verbose=verbose))


@app.command()
def surface(
    word: str = typer.Argument("", help="Show what bears this word (what implements the term)."),
    record: bool = typer.Option(False, "--record", help="Run the probes and write what they find."),
    phantoms: bool = typer.Option(False, "--phantoms", help="Only what nothing touches."),
    on: str = typer.Option("", "--on", help="A surface id: its seams and the words it bears on."),
    bear: str = typer.Option("", "--bear", help="A surface id: record that WORD is borne by it."),
    note: str = typer.Option("", "--note", help="Why, for the bearing."),
) -> None:
    """What this repo stands on: surfaces, seams, phantoms — and which words they bear."""
    from montology_scan import record_surfaces, surface_report
    from montology_scan.surf import bear as bear_word

    from ._ui import emit_all

    if bear:
        if not word:
            typer.echo("REFUSED — say which word: monty surface WORD --bear SURFACE_ID")
            raise typer.Exit(1)
        line = bear_word(word, bear, note or None)
        typer.echo(line)
        raise typer.Exit(1 if line.startswith("REFUSED") else 0)

    if record:
        r = record_surfaces()
        typer.echo(f"recorded {r['surfaces']} surface(s), {r['seams']} seam(s) "
                   f"via {', '.join(r['probes'])}")
        for s in r["skipped"]:
            typer.echo(f"  skipped {s}")

    emit_all(surface_report(only_phantoms=phantoms, word=word or None, on=on or None))


@app.command()
def sync() -> None:
    """Render the words skill from the database (prose is output, never source)."""
    from montology_gen import sync as gen_sync

    typer.echo(gen_sync())


@app.command()
def grep(pattern: str,
         lang: str = typer.Option("", "--lang", help="Language for the pattern (python, typescript…).")) -> None:
    """Structural search via ast-grep: `monty grep 'def $F($$$)' --lang python`."""
    from montology_scan import sg

    typer.echo(sg(pattern, lang))


@app.command()
def gen(name: str = typer.Argument(..., help="The word to draft a definition for."),
        context: str = typer.Option("", help="Usage context grounding the draft.")) -> None:
    """Draft ONE definition on the atomic tier — law-checked, refused over written wrong."""
    from montology_gen import gen_word

    typer.echo(gen_word(name, context))


@design_app.command("token")
def design_token(name: str, category: str, value: str,
                 note: str = typer.Option("", help="Context worth keeping.")) -> None:
    """Name a design value: monty design token brand-primary color '#061a1c'."""
    from montology_gen import sync as _sync
    from montology_ontology import token_add

    from ._ui import emit

    got = token_add(name, category, value, note or None)
    emit(got)
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    emit(_sync())


@design_app.command("tokens")
def design_tokens(category: str = typer.Argument("", help="color | space | radius | shadow | font | breakpoint.")) -> None:
    """The design vocabulary as rows."""
    from montology_ontology import tokens

    from ._ui import console, _swatched

    rows = tokens(category or None)
    if not rows:
        typer.echo("(no tokens yet — monty design candidates shows what the code uses)")
        return
    from rich.table import Table

    table = Table(box=None, header_style="bold cyan", pad_edge=False)
    for col in ("category", "token", "value"):
        table.add_column(col)
    for t in rows:
        table.add_row(t["category"], f"[bold]{t['name']}[/bold]", _swatched(t["value"]))
    console.print(table)


@design_app.command("candidates")
def design_candidates_cmd() -> None:
    """The design values the code is asking to have named — adoption-ready."""
    from montology_scan import design_candidates

    from ._ui import emit_all

    emit_all(design_candidates().splitlines())


@design_app.command("ingest")
def design_ingest() -> None:
    """Adopt the repo's own Tailwind theme (v4 @theme, v3 config) as tokens."""
    from montology_scan import ingest_theme

    from ._ui import emit

    emit(ingest_theme())


@design_app.command("recipes")
def design_recipes(min_uses: int = typer.Option(3, "--min", help="Occurrences before a combo counts.")) -> None:
    """Recurring utility compositions with no name — components the markup wants."""
    from montology_scan import recipe_candidates

    typer.echo(recipe_candidates(min_uses=min_uses))


@design_app.command("scan")
def design_scan() -> None:
    """The style surface: colors, spacing, classes, escapes — measured."""
    from montology_core import workspace_root
    from montology_scan import style_surface

    s = style_surface(workspace_root())
    typer.echo(f"{s['files']} style-bearing files")
    typer.echo(f"  colors: {len(s['colors'])} distinct, {sum(s['colors'].values())} uses")
    typer.echo(f"  spacing: {len(s['spacing'])} distinct values")
    typer.echo(f"  classes: {len(s['defined_classes'])} defined, {len(s['used_classes'])} used")
    typer.echo(f"  custom properties: {len(s['custom_props'])}")
    typer.echo(f"  tailwind arbitrary escapes: {len(s['arbitrary'])}")


@app.command()
def migrate(was: str, now: str,
            apply: bool = typer.Option(False, "--apply", help="Rewrite in place (clean git tree first).")) -> None:
    """Propagate a rename through the code: sweep every case variant; --apply rewrites."""
    from montology_scan import migrate as scan_migrate

    typer.echo(scan_migrate(was, now, apply))


@app.command()
def explain(no_draft: bool = typer.Option(False, "--no-draft", help="Skip atomic-tier definition drafts.")) -> None:
    """The one-shot conceptual X-ray: surface, vocabulary had and asked-for,
    clusters vs directories, design, contradictions."""
    from ._ui import emit_all
    from montology_scan import explain as scan_explain

    emit_all(scan_explain(draft=not no_draft))


@app.command()
def drift(samples: int = typer.Option(12, "--samples", help="History points to measure."),
          csv: bool = typer.Option(False, "--csv", help="Machine-readable rows (the research lane).")) -> None:
    """The telescope: lexicon, palette and convergence across the git history."""
    from ._ui import emit_all
    from montology_scan import drift_csv, measure_history, render_drift

    rows = measure_history(samples=samples)
    if csv:
        for line in drift_csv(rows):
            typer.echo(line)
        return
    emit_all(render_drift(rows))


@app.command()
def vitals(json_out: bool = typer.Option(False, "--json", help="The dashboard shape."),
           strict: bool = typer.Option(False, "--strict", help="Exit 1 unless TENDED — for CI.")) -> None:
    """The pulse: the state of this repo's meaning, one verdict — track it per repo."""
    from ._ui import emit_all
    from montology_scan import build_vitals
    from montology_scan.vitals import render_vitals

    r = build_vitals()
    if json_out:
        import json as _json

        typer.echo(_json.dumps(r, indent=2))
    else:
        emit_all(render_vitals(r))
    if strict and r["state"] != "tended":
        raise typer.Exit(1)


@app.command()
def guard(stats: bool = typer.Option(False, "--stats", help="Repair-following, measured from the log.")) -> None:
    """The firewall (hook entry): reads a proposed edit as JSON on stdin,
    allows silently or DENIES with the repair — drift cannot enter."""
    import sys as _sys

    from ._ui import emit, emit_all, emit_err
    from montology_scan import guard_hook

    if stats:
        from montology_scan.guard import stats as guard_stats

        emit_all(guard_stats())
        return
    raise typer.Exit(guard_hook(_sys.stdin.read(), err=emit_err, out=emit))


@app.command()
def serve(http: bool = typer.Option(False, help="Streamable HTTP instead of stdio.")) -> None:
    """Run the montology MCP server."""
    import sys

    from montology_cli.mcp_server import main as serve_main

    sys.argv = ["montology-mcp"] + (["--http"] if http else [])
    serve_main()
