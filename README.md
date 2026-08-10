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
# as an agent plugin (any supporting client)
# → point your client at this folder or install it as a plugin

# as a workspace (developing)
uv sync            # every package, one lock
just               # list what you can do
uvx montology      # the CLI: install data, run the server, manage keys
```

## The map

| package | import | what it is |
|---|---|---|
| `cli/` | `montology` | The `montology` command: setup, data pulls, doctor, serve. |
| `ontology/` | `montology_ontology` | The SQLite vocabulary + IAB taxonomy ingest. Authored in `seed.py`, checked by `montology onto`. |
| `zoo/` | `montology_zoo` | Embedding models from HuggingFace, run locally (ONNX/GGUF). A registry, a downloader, one `embed()` call. |
| `server/` | `montology_server` | FastMCP server (stateless HTTP-ready) returning MCP Apps artifacts via `mcp-ui-server`. |
| `tools/dataforseo/` | `montology_dataforseo` | DataForSEO wrapped as Mellea tools. |
| `tools/scrapecreators/` | `montology_scrapecreators` | ScrapeCreators wrapped as Mellea tools. |
| `warehouse/` | `montology_warehouse` | DuckDB — the analytical engine over your data, with the SQLite registries attached. |
| `tools/crawl/` | `montology_crawl` | Local AI crawling (crawl4ai): pages as markdown, measured brand kits, component-ready sections. |
| `skills/` | — | Agent Skills: how to use all of the above, in the agent's language. |

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
  taxonomies for use with attribution; `montology data pull` fetches the
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

Scaffold. The structure and contracts are real; most implementations are
stubs with their intent documented. See `CLAUDE.md` for how the agent of
record works on this repo.
