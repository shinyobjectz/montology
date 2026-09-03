"""The montology CLI — an ontology context layer for any monorepo.

Every message assumes the reader is naming things in a codebase and wants
to be told, quickly, whether a name is safe and what to do when it is not.
Errors carry their repair.
"""

from __future__ import annotations

import json
import os

import typer
from typer.core import TyperGroup


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

onto_app = typer.Typer(help="The vocabulary: check, add, amend, rule, except, list.", no_args_is_help=True)
intake_app = typer.Typer(help="The questions a workspace starts with: phased forms, answers on disk, the glossary.", no_args_is_help=True)
canvas_app = typer.Typer(help="The ontology as a graph: build, write and review it on a local canvas.", invoke_without_command=True)
design_app = typer.Typer(help="Design values as vocabulary: tokens, drift, candidates.", no_args_is_help=True)
app.add_typer(onto_app, name="onto")
app.add_typer(design_app, name="design")
app.add_typer(intake_app, name="intake")
app.add_typer(canvas_app, name="canvas")


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
        checks += _harness_checks(root)
    from ._ui import emit

    for ok, label, repair in checks:
        mark = "ok " if ok else "MISSING"
        emit(f"[{mark}] {label}" + ("" if ok else f" — {repair}"))


def _harness_checks(root) -> list[tuple[bool, str, str]]:
    """Is the firewall actually wired, per harness?

    The post-hoc half of montology is harness-agnostic; the pre-write half
    is a hook, and a hook has a dialect. A repo can be enforced under one
    agent and merely advisory under another with nothing saying so — which
    is the worst shape for a gate, because the team believes it is closed.
    Only harnesses this repo has ASKED for are reported: an absent
    .cursor/ is a choice, not a defect.
    """
    out: list[tuple[bool, str, str]] = []
    wired = [
        ("claude", root / ".claude" / "settings.json", ("hooks", "PreToolUse"),
         "monty init --agents claude"),
        ("cursor", root / ".cursor" / "hooks.json", ("hooks", "preToolUse"),
         "monty init --agents cursor"),
    ]
    for name, path, (top, event), repair in wired:
        marker = root / (".claude" if name == "claude" else ".cursor")
        if not marker.is_dir():
            continue                       # this harness was never wired here
        found = False
        if path.is_file():
            try:
                data = json.loads(path.read_text())
                found = "monty guard" in json.dumps(
                    data.get(top, {}).get(event, []))
            except json.JSONDecodeError:
                out.append((False, f"{name} guard hook",
                            f"{path.name} does not parse — fix it, then {repair}"))
                continue
        out.append((found, f"{name} guard hook (drift cannot enter)", repair))
    return out


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
    pos: str = typer.Option("", "--pos", help="What it NAMES: verb | noun | value — how a collision is judged."),
) -> None:
    """Author a word — check-first; a taken name is refused with findings."""
    from montology_ontology import add

    from ._ui import emit

    got = add(name, definition, test=test or None, note=note or None, kind=kind,
              owner=owner or None, code=code or None, pos=pos or None)
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
    pos: str | None = typer.Option(None, "--pos", help="What it NAMES: verb | noun | value."),
    why: str = typer.Option("", "--why", help="Why the record changed — the ledger keeps it."),
) -> None:
    """Correct a word's recorded text — the name stays, the old text is ledgered."""
    from montology_ontology import amend

    from ._ui import emit, emit_all

    got = amend(name, definition=definition, test=test, note=note, code=code,
                owner=owner, pos=pos, why=why or None)
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


@onto_app.command("except")
def onto_except(
    word: str = typer.Argument("", help="The word a symbol may share the name of."),
    where: str = typer.Option("", "--where", help="Path glob it holds in (default: tree-wide, and said so)."),
    why: str = typer.Option("", "--why", help="Required — a reasonless exception is a shrug."),
    drafts: bool = typer.Option(False, "--drafts", help="What montology.toml [scan] allow would become."),
    drop: bool = typer.Option(False, "--drop", help="Remove the exception."),
) -> None:
    """A symbol may share this word's name, HERE, for this reason — ledgered.

    Judged on what the word NAMES: a verb doing ordinary work below the
    surface is not a second meaning; a noun answering for a second thing is
    the defect; a value type declared as two values is refused outright.
    """
    from montology_ontology import except_add, except_drop, exceptions

    from ._ui import emit_all

    if drafts:
        from montology_scan import except_drafts

        ds = except_drafts()
        if not ds:
            typer.echo("no drafts — montology.toml [scan] allow is empty or already ledgered.")
            raise typer.Exit(0)
        lines = [f"{len(ds)} entry(ies) in montology.toml [scan] allow, unledgered. "
                 "Each needs the one thing the list never carried — its reason:", ""]
        for d in ds:
            mark = "" if d["is_word"] else "   [not a word — nothing collides with it]"
            mark += "" if d["pos"] else "   [no part of speech yet]"
            lines.append(f"  {d['word']}{mark}")
            lines.append(f'      monty onto except {d["word"]} --where "…" --why "…"')
        lines += ["", "Then empty the list: [scan] allow = []. Nothing is adopted "
                  "automatically — the reason is the feature, and montology will not "
                  "invent one."]
        emit_all(lines)
        raise typer.Exit(0)

    if not word:
        rows = exceptions()
        if not rows:
            typer.echo("no exceptions — `monty lint` reports collisions with the four "
                       "cases; record the ones you keep with `monty onto except`.")
            raise typer.Exit(0)
        emit_all([f"  {r['word']!r} in {'tree-wide' if r['scope'] == '**' else r['scope']}"
                  f"  ({r['judged'] or 'unjudged'}, {r['checked'] or '—'})  {r['why']}"
                  for r in rows])
        raise typer.Exit(0)

    if drop:
        typer.echo(except_drop(word, where or None))
        raise typer.Exit(0)

    from montology_core import workspace_root
    from montology_scan import type_declarations

    try:
        types = [t for t in type_declarations(workspace_root())
                 if t["name"].lower() == word.strip().lower()]
    except Exception:  # noqa: BLE001 — an unmeasurable tree is `unchecked`, not a crash
        types = []
    got = except_add(word, why, scope=where or None, types=types)
    emit_all(got.splitlines())
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    from montology_gen import sync as _sync

    typer.echo(_sync())


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


class SourcesGroup(TyperGroup):
    """`monty onto sources [group]` predates `sources ingest`.

    A surface that works does not get to break because a subcommand arrived
    under it, so a first token that names no subcommand is the group filter it
    has always been and is routed to `list`. README, the plugin skill and the
    MCP tool all document the old form; a rename with no ledger behind it is
    exactly what this repo refuses everywhere else."""

    def parse_args(self, ctx, args):
        if not args or (args[0] not in self.commands and not args[0].startswith("-")):
            args = ["list", *args]
        return super().parse_args(ctx, args)


sources_app = typer.Typer(
    help="Public taxonomies: what exists, whether you may ship against it, and — for the "
         "two that have an ingester — their terms in the vocabulary.",
    cls=SourcesGroup)
onto_app.add_typer(sources_app, name="sources")


@sources_app.command("list")
def onto_sources(
    group: str = typer.Argument("", help="core, or a domain group. Omit for all."),
    search: str = typer.Option("", "--search", help="Search BOTH tiers: the shortlist and the harvested index."),
    refresh: bool = typer.Option(False, "--refresh", help="Re-fetch the OBO Foundry registry into the cache."),
) -> None:
    """The public taxonomies montology knows about, with their licences.

    Grouped by who it is for: `core` is any business in any industry,
    everything else names its domain. Mostly a catalogue — each entry carries
    where the data lives, whether it is worth reaching for, the licence AS
    PUBLISHED and the practical commercial verdict, because the question that
    decides whether you may ship against a vocabulary is the licence, and it is
    the one every automated scan gets wrong on the IAB set. Two entries go
    further and can be loaded into the vocabulary: `monty onto sources ingest`.

    `--search` also reaches the SECOND tier: the harvested OBO Foundry index,
    which is 177 ontologies nobody here read, printed under its own heading and
    never mixed into the shortlist. It answers "does one already exist for
    this?" — not "should I use it?".
    """
    from montology_ontology import render_harvest, render_search, render_sources

    from ._ui import emit_all

    if refresh:
        emit_all(render_harvest(refresh=True))
    if search:
        emit_all(render_search(search))
    elif not refresh:
        emit_all(render_sources(group))


@sources_app.command("ingest")
def onto_sources_ingest(
    source: str = typer.Argument(..., help="A registry id that has an ingester: prov-o, schemaorg."),
    refresh: bool = typer.Option(False, "--refresh", help="Re-fetch the payload instead of reading the cache."),
) -> None:
    """Load one public taxonomy's terms into the vocabulary as adopted words.

    So that `monty onto check <name>` can answer "that is Schema.org's word,
    not yours" — which a catalogue cannot answer and a reuse check needs. The
    payload is cached under `.monty/cache/`, so every run after the first is
    offline; the words carry the source they came from, this repo's own words
    are never overwritten, and the licence travels with every answer about
    them. An id with no ingester is refused with the ones that have one.
    """
    from montology_ontology import ingest_source

    from ._ui import emit_all

    line = ingest_source(source, refresh=refresh)
    emit_all(line.splitlines())
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


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
    from montology_canvas import lint as canvas_lint
    from montology_gen import lint as gen_lint
    from montology_scan import design_lint, lint as scan_lint

    from ._ui import emit_all

    lines = scan_lint() + design_lint() + gen_lint() + canvas_lint()
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


@onto_app.command("ask")
def onto_ask(
    text: str = typer.Argument(..., help="Something the vocabulary must be able to answer."),
    answered_by: str = typer.Option("", "--by", help="Comma-separated words that answer it."),
    phase: str = typer.Option("", "--from", help="The intake phase it came from."),
) -> None:
    """Record a competency question — the requirement the vocabulary answers to."""
    from montology_ontology import ask

    line = ask(text, asked_in=phase,
               answered_by=[w.strip() for w in answered_by.split(",") if w.strip()])
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("answers")
def onto_answers(qid: str, word: str = typer.Option(..., "--word", help="A word that answers it.")) -> None:
    """Say that a word is part of how a question gets answered."""
    from montology_ontology import answer

    line = answer(qid, word)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("questions")
def onto_questions(drafts: bool = typer.Option(False, "--drafts", help="Draft questions from the intake answers.")) -> None:
    """The questions this vocabulary is answerable to, and what answers them."""
    from montology_ontology import coverage, harvest, questions

    from ._ui import emit_all

    if drafts:
        try:
            from montology_intake import merged_answers

            got = harvest(merged_answers())
        except Exception as e:  # noqa: BLE001
            typer.echo(f"no intake answers to draft from ({type(e).__name__}). "
                       "Run `just intake` first.")
            raise typer.Exit(0) from None
        if not got:
            typer.echo("nothing to draft — the intake answers name no things yet.")
            raise typer.Exit(0)
        lines = [f"{len(got)} draft question(s) from the intake — "
                 "confirm the ones that are the question you meant:", ""]
        for d in got:
            lines += [f"  {d['text']}   (from {d['from']})",
                      f"      monty onto ask \"{d['text']}\" --from intake"]
        emit_all(lines)
        raise typer.Exit(0)

    qs = questions()
    cov = coverage()
    if not qs:
        typer.echo(cov["note"])
        raise typer.Exit(0)
    lines = []
    for q in qs:
        mark = "·" if not q["answered_by"] else "✓"
        lines.append(f"  {mark} {q['id']}  {q['text']}")
        if q["answered_by"]:
            lines.append(f"        answered by: {', '.join(q['answered_by'])}")
    lines += ["", f"  {len(cov['unanswered'])} question(s) no word answers",
              f"  {len(cov['unmotivated'])} word(s) no question motivates"]
    if cov["unmotivated"]:
        lines.append(f"        {', '.join(cov['unmotivated'][:12])}"
                     + (" …" if len(cov["unmotivated"]) > 12 else ""))
    emit_all(lines)


@onto_app.command("propose")
def onto_propose(
    title: str = typer.Argument(..., help="What this proposal is for."),
    change: list[str] = typer.Option([], "--change", help="intent=JSON, e.g. word.add={\"name\":\"cell\",\"definition\":\"…\"}"),
    why: str = typer.Option("", "--why", help="The case for the change."),
    author: str = typer.Option("", "--author"),
) -> None:
    """Open a proposal: a set of changes to be reviewed before it lands."""
    import json as _json

    from montology_ontology import propose

    parsed = []
    for spec in change:
        intent, _, blob = spec.partition("=")
        try:
            parsed.append({"intent": intent.strip(), "fields": _json.loads(blob or "{}")})
        except ValueError as e:
            typer.echo(f"REFUSED — {intent!r}: the fields are JSON ({e})")
            raise typer.Exit(1) from None
    line = propose(title, parsed, why=why, author=author)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("proposals")
def onto_proposals(status: str = typer.Argument("", help="open | merged | closed")) -> None:
    """Every proposal, newest first."""
    from montology_ontology import changes, proposals

    from ._ui import emit_all

    rows = proposals(status or None)
    if not rows:
        typer.echo("no proposals — `monty onto propose \"title\" --change intent=JSON`.")
        raise typer.Exit(0)
    lines = []
    for r in rows:
        cs = changes(r["id"])
        undecided = sum(1 for c in cs if not c["verdict"])
        lines.append(f"  {r['id']}  [{r['status']}]  {r['title']}  "
                     f"({len(cs)} change(s)"
                     + (f", {undecided} undecided" if undecided else "") + ")")
    emit_all(lines)


@onto_app.command("show")
def onto_show(pid: str) -> None:
    """One proposal: its changes, their verdicts, and what it would break."""
    import json as _json

    from montology_ontology import changes, preview, proposals

    from ._ui import emit_all

    row = next((p for p in proposals() if p["id"] == pid), None)
    if not row:
        typer.echo(f"REFUSED — no proposal {pid!r}.")
        raise typer.Exit(1)

    lines = [f"{row['id']}  [{row['status']}]  {row['title']}"]
    if row["why"]:
        lines += ["", f"  {row['why']}"]
    lines.append("")
    for c in changes(pid):
        mark = {"approved": "✓", "rejected": "✗"}.get(c["verdict"], "·")
        lines.append(f"  {mark} #{c['ord']}  {c['intent']}")
        for k, v in sorted(c["fields"].items()):
            lines.append(f"        {k}: {v}")
    seen = preview(pid)
    lines.append("")
    if seen["new"]:
        lines.append("  NEWLY RAISED by this merge:")
        lines += [f"    {line}" for line in seen["new"]]
    for r in seen.get("refused", []):
        lines.append(f"    {r['line']}")
    lines.append("  the gate holds after this merge" if seen["ok"]
                 else "  THE GATE WOULD FAIL — this cannot merge as it stands")
    emit_all(lines)


@onto_app.command("decide")
def onto_decide(pid: str, ord_: int = typer.Argument(..., metavar="N"),
                verdict: str = typer.Argument(..., help="approved | rejected"),
                note: str = typer.Option("", "--note")) -> None:
    """Approve or reject ONE change — a good rename should not sink with a bad definition."""
    from montology_ontology import decide

    line = decide(pid, ord_, verdict, note)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("merge")
def onto_merge(pid: str) -> None:
    """Replay the approved changes — refused while the gate would fail."""
    from montology_ontology import merge

    line = merge(pid)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("close")
def onto_close(pid: str) -> None:
    """Close a proposal without merging it."""
    from montology_ontology import close_proposal

    line = close_proposal(pid)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("relate")
def onto_relate(subject: str, verb: str, object: str,
                why: str = typer.Option("", "--why"),
                drop: bool = typer.Option(False, "--drop")) -> None:
    """Say that one word DOES something to another — the ontology's own graph.

    This is the one thing montology does not mine. Palantir's link types are
    declared by a person and DTDL's relationships are written into the model;
    nobody finds them in code, because code holds an implementation and not an
    ontology. `monty onto relations --drafts` shows what the scan suggests.
    """
    from montology_ontology import relate, unrelate

    line = unrelate(subject, verb, object) if drop else relate(subject, verb, object, why=why or None)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("relations")
def onto_relations(
    drafts: bool = typer.Option(False, "--drafts", help="What the code suggests, unconfirmed."),
    word: str = typer.Argument("", help="Only relations touching this word."),
) -> None:
    """The noun-verb-noun graph: what acts on what."""
    from montology_ontology import relations, render_drafts

    from ._ui import emit_all

    if drafts:
        emit_all(render_drafts())
        raise typer.Exit(0)
    rows = relations(word or None)
    if not rows:
        typer.echo("no relations yet — `monty onto relations --drafts` reads what "
                   "the code suggests, and `monty onto relate A verb B` records one.")
        raise typer.Exit(0)
    emit_all([f"  {r['subject']} --{r['verb']}--> {r['object']}"
              + (f"   ({r['why']})" if r["why"] else "") for r in rows])


@onto_app.command("verbs")
def onto_verbs(top: int = typer.Option(15, "--top", help="How many words to report.")) -> None:
    """What the code DOES to the things this vocabulary names — and does not name.

    The scan measures declarations, which is the noun side, and it is why a
    montology vocabulary comes out about ninety percent nouns. This is the
    other half, read off the same tree.
    """
    from montology_scan import render_acts

    from ._ui import emit_all

    emit_all(render_acts(top=top))


@onto_app.command("review")
def onto_review(
    threshold: float = typer.Option(0.70, "--threshold", help="Cosine above which two meanings count as one."),
    spread: int = typer.Option(3, "--spread", help="Unrelated areas before a word looks like a God Object."),
) -> None:
    """The anti-patterns this vocabulary instantiates — named, evidenced, advisory.

    Never fails a build. The gate is `monty lint`; this is a judgement, and a
    judgement that fails a build is one people learn to route around.
    """
    from montology_scan import render_review, review

    from ._ui import emit_all

    emit_all(render_review(review(threshold=threshold, spread=spread)))


@onto_app.command("genus")
def onto_genus(
    word: str = typer.Argument("", help="The word that is a kind of something."),
    is_a: str = typer.Option("", "--is", help="The more general word it is a kind of."),
    why: str = typer.Option("", "--why", help="Why the subsumption holds."),
    drop: bool = typer.Option(False, "--drop", help="Remove the subsumption."),
) -> None:
    """What a word IS a kind of — the one relation that changes what the gate knows."""
    from montology_ontology import genera, genus_add, genus_chain, genus_drop, inherited

    from ._ui import emit_all

    if not word:
        rows = genera()
        if not rows:
            typer.echo("no genus recorded yet — `monty onto genus WORD --is WORD`.")
            raise typer.Exit(0)
        emit_all([f"  {r['word_name']} is a kind of {r['genus_name']}"
                  + (f"  ({r['why']})" if r["why"] else "") for r in rows])
        raise typer.Exit(0)

    if not is_a:
        chain = genus_chain(word)
        lines = [f"{word} is a kind of: " + (" → ".join(chain) if chain else "(nothing recorded)")]
        got = inherited(word)
        if got:
            lines += ["", "inherited rulings:"]
            lines += [f"  from {i['from']}  [{i['kind']}] {i['detail']}" for i in got]
        emit_all(lines)
        raise typer.Exit(0)

    line = genus_drop(word, is_a) if drop else genus_add(word, is_a, why=why or None)
    typer.echo(line)
    raise typer.Exit(1 if line.startswith("REFUSED") else 0)


@onto_app.command("rigidity")
def onto_rigidity(word: str, value: str = typer.Argument(..., help="rigid | anti-rigid")) -> None:
    """Judge what KIND of thing a word names, so its subsumptions can be checked.

    Rigid is what a thing IS and cannot stop being; anti-rigid is a role it
    plays for a while. The one OntoClean metaproperty montology keeps.
    """
    from montology_ontology import rigidity_set

    line = rigidity_set(word, value)
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
def config(
    key: str = typer.Argument("", help="A setting, e.g. scan.collisions. Omit to list every one."),
    value: str = typer.Argument("", help="The new value. Omit to read the current one."),
) -> None:
    """Read or change what this workspace is tuned to.

    No arguments lists every setting with its value, where that value came
    from, and what it does. One argument reads one. Two set it — refused
    with the allowed set rather than coerced into something meaningless.
    """
    from montology_core import settings as cfg
    from montology_core import workspace_root

    from ._ui import emit, next_steps

    root = workspace_root()

    if key and value:
        try:
            emit("set  " + cfg.write(root, key, value))
        except (KeyError, ValueError, FileNotFoundError) as e:
            # KeyError stringifies to its repr — the quotes would read as
            # part of the repair, and a repair you cannot paste is not one.
            emit(f"REFUSED — {e.args[0]}")
            raise typer.Exit(2) from None
        return

    rows = cfg.effective(root)
    if key:
        rows = [r for r in rows if r["name"] == key]
        if not rows:
            emit(f"REFUSED — no such setting {key!r}. "
                 f"Known: {', '.join(sorted(cfg.SETTINGS))}.")
            raise typer.Exit(2)
    width = max(len(r["name"]) for r in rows)
    for r in rows:
        allowed = r["allowed"]
        emit(f"  {r['name']:<{width}}  {r['value']!r:<22} "
             f"({r['source']}; {allowed if isinstance(allowed, str) else ' | '.join(allowed)})")
        emit(f"  {'':<{width}}  {r['effect']}")
    if not key:
        next_steps([
            ("monty config <key> <value>", "change one — refused if the value is not allowed"),
            ("monty vitals", "what the current settings are letting through"),
        ])


@app.command()
def serve(http: bool = typer.Option(False, help="Streamable HTTP instead of stdio.")) -> None:
    """Run the montology MCP server."""
    import sys

    from montology_cli.mcp_server import main as serve_main

    sys.argv = ["montology-mcp"] + (["--http"] if http else [])
    serve_main()


@canvas_app.callback(invoke_without_command=True)
def canvas_root(ctx: typer.Context,
                no_open: bool = typer.Option(False, "--no-open", help="Print the URL only; do not open a browser."),
                no_scan: bool = typer.Option(False, "--no-scan", help="The vocabulary only — skip the tree-sitter sweep."),
                port: int = typer.Option(0, "--port", help="Bind a fixed port (0 = ephemeral).")) -> None:
    """Serve the ontology as a graph on localhost, until you interrupt it."""
    if ctx.invoked_subcommand:
        return
    from montology_canvas import serve

    typer.echo(serve(open_browser=not no_open, port=port, with_scan=not no_scan,
                     _ready=lambda url: typer.echo(f"canvas  {url}   (ctrl-c to close)")))


@canvas_app.command("stamp")
def canvas_stamp_cmd() -> None:
    """Record which sources produced the built bundle — run after a build."""
    from montology_canvas import stamp

    typer.echo(stamp())


@canvas_app.command("export")
def canvas_export_cmd(
    fmt: str = typer.Argument("ttl", help="Format: ttl, xml, or vowl."),
) -> None:
    """The vocabulary as standard RDF (Turtle, RDF/XML) or WebVOWL JSON."""
    from montology_canvas import export

    typer.echo(export(fmt))


@canvas_app.command("graph")
def canvas_graph_cmd(
    no_scan: bool = typer.Option(False, "--no-scan", help="The vocabulary only — skip the tree-sitter sweep."),
    candidates: int = typer.Option(20, "--candidates", help="How many candidate nodes to include."),
) -> None:
    """The vocabulary and the code it governs, as one node/edge document."""
    import json as _json

    from montology_canvas import graph

    typer.echo(_json.dumps(graph(with_scan=not no_scan, candidate_top=candidates),
                           indent=2, ensure_ascii=False))


@intake_app.command("ask")
def intake_ask_cmd(spec: str = typer.Argument(..., help="Phase spec: a JSON file path, JSON text, or - for stdin."),
                   no_open: bool = typer.Option(False, "--no-open", help="Print the URL only; do not open a browser."),
                   timeout: float = typer.Option(0, "--timeout", help="Seconds to wait for the submit (0 = forever).")) -> None:
    """Serve one phase as a form, wait for the submit, write .monty/answers/<phase>.answers.json, exit."""
    from montology_intake import ask

    got = ask(spec, open_browser=not no_open, timeout=timeout)
    typer.echo(got)
    raise typer.Exit(0 if got.startswith("answered") else 1)


@intake_app.command("answers")
def intake_answers_cmd() -> None:
    """Every answered phase, merged, as JSON — what the next phase is written from."""
    import json as _json

    from montology_intake import merged_answers

    typer.echo(_json.dumps(merged_answers(), indent=2, ensure_ascii=False))


@intake_app.command("status")
def intake_status_cmd() -> None:
    """Phases open and answered; whether the glossary is rendered."""
    from montology_intake import status

    for line in status():
        typer.echo(line)


@intake_app.command("glossary")
def intake_glossary_cmd(open_: bool = typer.Option(False, "--open", help="Open the page when rendered.")) -> None:
    """The closing page: the whole ontology as a glossary, rendered from the database."""
    from montology_intake import glossary

    got = glossary()
    typer.echo(got)
    if got.startswith("glossary") and open_:
        import webbrowser

        webbrowser.open("file://" + got.split()[1])
    raise typer.Exit(0 if got.startswith("glossary") else 1)
