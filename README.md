# montology

**M**arketing + m**on**orepo + on**tology**. One repo that gives a marketing
team — and the agent working for them — a shared vocabulary, real taxonomies,
local embeddings, and tools that answer with data instead of vibes.

Montology is three things at once:

1. **An ontology.** A relational vocabulary for marketing, stored in SQLite,
   authored in one place, and enforced by tooling — plus the industry
   taxonomies everyone already speaks (IAB Content Taxonomy 3.x, Audience
   Taxonomy, Ad Product Taxonomy), ingested into the same database so a
   category is a row you can join against, not a PDF you squint at.
2. **A Python monorepo on uv workspaces.** Packages for the ontology, an
   embedding zoo (HuggingFace models run locally via ONNX/GGUF), Mellea-wrapped
   marketing tools (DataForSEO, ScrapeCreators), and an MCP server that ships
   interactive artifacts via [MCP Apps / mcp-ui](https://github.com/MCP-UI-Org/mcp-ui).
3. **An [Agent Plugin](https://agent-plugins.org).** The repo root is a valid
   Agent Plugins 1.0.0 folder — `plugin.json`, `skills/`, `mcp.json` — so it
   installs into ChatGPT, Codex, Cursor, GitHub Copilot, and VS Code, and
   Claude Code reads the same `skills/` natively.

## Who this is for

Marketers, not engineers. You know your brand, your competitors, and your
channels; your agent (Claude Code or any Agent Plugins client) knows montology.
You ask marketing questions; the agent uses the vocabulary, the taxonomies,
the embeddings and the tools on your behalf.

## Quick start

```sh
# TODAY (works now):
git clone https://github.com/socialite-ml/montology && cd montology
uv sync                     # every package, one lock
uv run monty doctor     # what is set up, what is missing, how to fix it
just                        # list everything else

# as an agent plugin: point any Agent Plugins client (or Claude Code) at
# this folder — plugin.json + skills/ + mcp.json are the standard layout.

# AFTER the first PyPI release (publish.yml, trusted publishing):
uvx montology               # the CLI anywhere, no clone
```

## The shape

```
.justfile      the ACTION SURFACE — `just` answers: what is live, what exists, what to do
.plugin/       the Agent Plugins face (plugin.json · mcp.json · skills/) — install THIS folder
.monty/        the engine: python packages (onto, zoo, warehouse, gen, media, cli, tools/)
               and .monty/cache/ — weights, browsers, embeddings; refetchable, never tracked
data/          the TRACKED central store: ontology.db, zoo.db (the registries ship with the repo)
design/        the node workspace — brand-AGNOSTIC mediums (components · email · image ·
               presentation · video · web) + the one shared render harness; imports `@brand/*`,
               bound to a project at render time
projects/      ENGAGEMENTS — each carries a brand instantiation (tokens, manifest, assets,
               sources) and its deliverables; user data, gitignored
```

Two workspaces, one orchestrator: uv owns `.monty/*`, npm owns `design/`,
`just` sees both. Projects are neither — each is the user's own uv/react
ground, consuming montology.

## Alignment decisions (why it is shaped this way)

- **uv workspaces ARE the monorepo framework.** One `uv.lock` at the root,
  every package a member, `tool.uv.sources` wiring them together. No second
  build system on top — anything else would fight uv.
- **Agent Plugins is the packaging layer, not the product.** Skills and MCP
  configs compiled here publish as one folder that any conforming client
  installs. New skills and servers accrete over time; the plugin is how they
  ship.
- **FastMCP for the server, mcp-ui for the artifacts.** FastMCP is the Python
  MCP framework with first-class stateless HTTP; `mcp-ui-server` returns
  MCP Apps UI resources from tools. Artifacts can be authored with any
  frontend framework — they travel as sandboxed HTML resources.
- **Taxonomies are fetched, not vendored.** IAB Tech Lab licenses its
  taxonomies for use with attribution; `monty data pull` fetches the
  current TSVs from the official repo into the local database.
- **SQLite is the record, DuckDB is the engine.** Registries stay SQLite
  (tiny, transactional); analysis runs in DuckDB, which attaches them
  read-only — one SQL surface over taxonomies, the model shelf, and the
  user's campaign files.
- **The agent writes the React.** Brand component libraries come from
  crawled sections + a measured brand kit, converted by the agent — not by
  a mechanical HTML-to-JSX tool (ruled on in montology-crawl).
- **API keys stay in the environment.** `DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD`
  and `SCRAPECREATORS_API_KEY`, read at call time, never stored in the repo.

## Status

Working. The runtime is real and live-tested: embed/transcribe/topics run
locally, eleven taxonomies ingest (30k+ rows), the crawler measures real
sites, the MCP server answers real clients, and the gen system's laws are
enforced in CI (`just check` = lint + the committed test suite). PyPI
publish is one trusted-publisher registration away (see
`.github/workflows/publish.yml`). `CLAUDE.md` says how the agent of record
works on this repo.
