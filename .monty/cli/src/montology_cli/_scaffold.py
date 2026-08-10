"""Materialize a workspace: the files `monty init` lays down.

Two sources, one relative layout. Installed as a wheel, the assets ride at
``montology_cli/_scaffold`` (see the cli pyproject's force-include); in a
repo checkout, the repo root itself carries the same paths. Either way the
materializer copies `.plugin/`, `data/*.db` and `design/` and renders the
workspace-local files (justfile, CLAUDE.md, .mcp.json, .gitignore).

IDEMPOTENT, and careful about ownership: engine-owned files (skills, the
render harness) refresh on every init; user-owned files (the data dbs once
present, anything the templates would clobber) are written only when
absent. A re-run repairs what is missing and touches nothing else.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ._engine import engine_spec

JUSTFILE = """# {name} — `just` shows the action surface: what is live, what exists, what to do.

set dotenv-load := true

# What is live right now: tools, models, data, projects
default:
    @echo "── {name} ─────────────────────────────────────────────"
    @monty doctor
    @echo ""
    @echo "── brands (the book) ──────────────────────────────────"
    @ls -1 brands 2>/dev/null | grep -v README || echo "  none yet — monty crawl audit <url> && monty brand scaffold <name> audit.json"
    @echo ""
    @echo "── projects (engagements) ─────────────────────────────"
    @ls -1 projects 2>/dev/null | grep -v -e node_modules -e README || echo "  none yet"
    @echo ""
    @echo "── skills the agent carries ───────────────────────────"
    @ls -1 .plugin/skills | grep -v README
    @echo ""
    @echo "── data (the central store) ───────────────────────────"
    @du -h data/* 2>/dev/null | sed 's/^/  /' || true
    @echo ""
    @echo "recipes: just --list   ·   the CLI: monty --help"

# Is everything set up? Says what is missing and how to fix it.
doctor:
    monty doctor

# Crawl a brand site end to end and scaffold its project
brand url:
    monty crawl audit {{{{url}}}} > /tmp/monty-audit.json && monty brand scaffold $(basename {{{{url}}}} | tr -d .) /tmp/monty-audit.json

# The MCP server by hand (agents normally launch it via .mcp.json)
serve:
    monty serve
"""

CLAUDE_MD = """# {name} — a montology workspace

Marketing work happens here through `monty` (the montology CLI) and the
skills under `.plugin/skills/` — they are the method; read them before
improvising. Run `just` alone to see the action surface: what tools are
live, which projects exist, what data is loaded.

- **`brands/`** — the brand book: one folder per brand — measured tokens,
  the component registry (captured + built), media by medium, social pulls.
- **`projects/`** — engagements: the work made for someone, consuming the book.
- **`data/`** — the registries (vocabulary, taxonomies, model shelf) and
  your DuckDB warehouse. Query with `monty sql "..."`.
- Rendering: components import `@brand/*`, bound to `brands/<name>/design`
  at render time; the shared harness lives inside `.monty/`.
- **`.monty/cache/`** — refetchable weights and browsers, never committed.

Ground rules: numbers come from tools, never memory. Categories are looked
up (`monty onto check`, taxonomy search), not guessed. When a tool answers
with a repair, relay it — do not improvise workarounds.
"""

AGENTS_MD = """# {name} — a montology workspace

Marketing work happens here through `monty` (the montology CLI). The
METHOD lives in `.plugin/skills/` — one SKILL.md per capability; read the
relevant one before improvising. Run `just` alone to see the action
surface: what tools are live, which projects exist, what data is loaded.

- **`brands/`** — the brand book: one folder per brand — measured tokens,
  the component registry (captured + built), media by medium, social pulls.
- **`projects/`** — engagements: the work made for someone, consuming the book.
- **`data/`** — the registries (vocabulary, taxonomies, model shelf) and
  the DuckDB warehouse. Query with `monty sql "..."`.
- Rendering: components import `@brand/*`, bound to `brands/<name>/design`
  at render time; the shared harness lives inside `.monty/`.
- **`.monty/cache/`** — refetchable weights and browsers, never committed.

Ground rules: numbers come from tools, never memory. Categories are looked
up (`monty onto check`, taxonomy search), not guessed. When a tool answers
with a repair, relay it — do not improvise workarounds.
"""

ENV_EXAMPLE = """# Copy to .env (gitignored) — or export these in your shell.
# Vendor keys are optional; every montology tool says what it needs.
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
SCRAPECREATORS_API_KEY=
# A served OpenAI-compatible model endpoint (optional — the host agent
# drafts by default, and gemma3:270m via Ollama covers one-line stubs).
MONTOLOGY_MODEL_URL=
"""

GITIGNORE = """__pycache__/
*.pyc
.DS_Store

# keys — never commit
.env
.env.*
!.env.example

# refetchable: weights, browsers, embeddings
.monty/cache/

# the registries (ontology.db, zoo.db) ARE tracked; the warehouse is
# your analytical scratch and stays local
data/warehouse.duckdb

# node (the render harness is engine plumbing)
.monty/design/node_modules/

# pulled media that re-pulls: track images (LFS when heavy), not videos
brands/*/design/video/*.mp4
"""

BRANDS_README = """# brands/ — the brand book

One folder per brand: everything montology knows about them, indexed.

    monty crawl audit https://thebrand.com > audit.json
    monty brand scaffold thebrand audit.json   # tokens + captured component registry
    monty brand logo thebrand thebrand         # quality vector, with provenance
    monty brand index thebrand                 # socials -> media -> embeddings

`<brand>/design/components/` is the registry (shadcn-shaped): `captured/`
holds the site's own sections as React, `built` components are idiomatic
rebuilds on the measured tokens. `<brand>/design/image|video|email|web|
presentation/` is the book by medium; `<brand>/data/` holds the audit,
source HTML and social pulls.
"""

PROJECTS_README = """# projects/

One folder per ENGAGEMENT — the work made for someone: campaigns,
reports, deliverable sets. The knowledge about a brand lives in
`brands/<name>/` (the brand book); an engagement consumes it.
"""


def scaffold_source() -> Path:
    """Where the assets live: the wheel's _scaffold dir, or the repo root."""
    wheel = Path(__file__).resolve().parent / "_scaffold"
    if wheel.is_dir():
        return wheel
    repo = Path(__file__).resolve().parents[4]
    if (repo / ".plugin").is_dir():
        return repo
    raise RuntimeError(
        "scaffold assets not found — neither the wheel's _scaffold nor a "
        "repo checkout. Reinstall montology (`uvx --refresh --from ... monty`)."
    )


def _write_if_absent(path: Path, content: str, made: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    made.append(str(path.name))


def materialize(ws: Path, name: str) -> dict:
    """Lay down the workspace at `ws`. Returns what happened, for the summary."""
    src = scaffold_source()
    made: list[str] = []
    ws.mkdir(parents=True, exist_ok=True)

    # the marker first — everything else resolves through it
    (ws / ".monty" / "cache" / "models").mkdir(parents=True, exist_ok=True)
    meta = ws / ".monty" / "workspace.toml"
    if not meta.exists():
        meta.write_text(
            f'name = "{name}"\ncreated = "{datetime.now(UTC).date()}"\n'
            f'engine = "{engine_spec()}"\n'
        )
        made.append("workspace.toml")

    # engine-owned: refreshes on every init; user additions survive. The
    # render harness is plumbing and lives INSIDE .monty — mediums live in
    # each brand's book (brands/<name>/design), not at the root.
    shutil.copytree(src / ".plugin", ws / ".plugin", dirs_exist_ok=True)
    harness = ws / ".monty" / "design"
    harness.mkdir(parents=True, exist_ok=True)
    for sub in ("package.json", "package-lock.json", "render.mjs"):
        s = src / "design" / sub
        if s.exists():
            shutil.copy2(s, harness / sub)
    made.append(".plugin + render harness refreshed")

    # user-owned once present: the registries are a starting point, and a
    # workspace's ontology grows — never clobber it
    (ws / "data").mkdir(exist_ok=True)
    for db in ("ontology.db", "zoo.db"):
        if not (ws / "data" / db).exists():
            shutil.copy2(src / "data" / db, ws / "data" / db)
            made.append(db)

    (ws / "brands").mkdir(exist_ok=True)
    _write_if_absent(ws / "brands" / "README.md", BRANDS_README, made)
    (ws / "projects").mkdir(exist_ok=True)
    _write_if_absent(ws / "projects" / "README.md", PROJECTS_README, made)
    _write_if_absent(ws / ".justfile", JUSTFILE.format(name=name), made)
    _write_if_absent(ws / ".gitignore", GITIGNORE, made)
    _write_if_absent(ws / ".env.example", ENV_EXAMPLE, made)

    return {"root": str(ws), "made": made}


CODEX_MCP_NOTE = (
    "codex keeps MCP config globally — add this to ~/.codex/config.toml "
    "(init never edits files outside the workspace):\n"
    "  [mcp_servers.montology]\n"
    '  command = "uvx"\n'
    '  args = ["--from", "{spec}", "montology-mcp"]'
)


def wire_agents(ws: Path, name: str, agents: tuple[str, ...]) -> dict:
    """Per-harness discovery files, chosen at onboarding. Project files
    only — a harness's global config is the user's, and stays theirs."""
    made: list[str] = []
    notes: list[str] = []
    mcp_config = json.dumps({
        "mcpServers": {"montology": {
            "command": "uvx",
            "args": ["--from", engine_spec(), "montology-mcp"],
        }}
    }, indent=2) + "\n"

    if "claude" in agents:
        _write_if_absent(ws / ".mcp.json", mcp_config, made)
        _write_if_absent(ws / "CLAUDE.md", CLAUDE_MD.format(name=name), made)
        skills_link = ws / ".claude" / "skills"
        if not skills_link.exists():
            skills_link.parent.mkdir(exist_ok=True)
            skills_link.symlink_to(Path("..") / ".plugin" / "skills")
            made.append(".claude/skills -> .plugin/skills")
    if "cursor" in agents:
        _write_if_absent(ws / ".cursor" / "mcp.json", mcp_config, made)
    if "cursor" in agents or "codex" in agents:
        _write_if_absent(ws / "AGENTS.md", AGENTS_MD.format(name=name), made)
    if "codex" in agents:
        notes.append(CODEX_MCP_NOTE.format(spec=engine_spec()))
    return {"made": made, "notes": notes}
