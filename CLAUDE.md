# montology — repo instructions

Public repo, `socialite-ml/montology`. Also mounted as a submodule of the
private `socialite` repo — never assume socialite's code or vocabulary is
reachable from here; this repo stands alone.

## Who uses this

**Non-technical marketers, through an agent** (Claude Code or any Agent
Plugins client). Every surface — CLI output, error messages, skill prose —
is written for someone who knows marketing and does not know Python. Errors
carry their repair: a boundary that only says "no" produces loops, not
compliance.

## The shape

- **uv workspaces monorepo.** Root `pyproject.toml` lists members; one
  `uv.lock`. Run everything through `just` (no recipe = list them).
- **The repo root is an Agent Plugins 1.0.0 folder** — `plugin.json`,
  `skills/`, `mcp.json`. Keep it conforming: those three names are the
  standard's, not ours to rename.
- **The ontology is a database, not a doc.** `ontology/data/ontology.db`,
  authored ONLY in `ontology/src/montology_ontology/seed.py`. IAB taxonomies
  ingest into the same database (`monty data pull`), namespaced so a
  house term and an IAB category can never collide.
- **The zoo downloads, it does not bundle.** Model weights come from
  HuggingFace at pull time onto the user's disk. Never commit weights.
- **Tools are Mellea-wrapped** (`@tool` from mellea) so any Mellea program
  can hand them to a model, and thin enough that the MCP server exposes the
  same functions.
- **Keys live in the environment**, read at call time: `DATAFORSEO_LOGIN`,
  `DATAFORSEO_PASSWORD`, `SCRAPECREATORS_API_KEY`. Never in code, never in
  the plugin.

## Everything prose is generated

Skills, docs and ontology words are produced by `monty gen` (the
montology-gen package): INSTRUMENTS measure the truth (AST surfaces,
warehouse shape, skill inventory), Mellea `@generative` STUBS turn facts
into prose (docstrings are specs — a prompt-shaped string fails `gen
lint`), and LAWS check the result deterministically against the same
instruments. A generation that fails its laws after one repair is REFUSED,
never written. Generated files carry a provenance header; edit the
instruments and regenerate, never the file. `gen lint` runs in `just
check`, so a skill that names a tool the AST does not know is a build
failure, not a doc bug.

THE DEFAULT DRAFTER IS THE HOST AGENT — you. Without a model backend,
`monty gen skill <name>` emits the grounded task (instruments, spec,
laws) for you to fulfill; treat it as work, write the file, run `gen
lint`. A lint FAIL after a surface change means regenerate that skill —
the failing build is the hook that forces it. A served model
(MONTOLOGY_MODEL_URL, any OpenAI-compatible endpoint) is the autonomous
lane, not a prerequisite — and it lives on a server. Locally there is
exactly one model, ever: gemma3:270m (292 MB), the atomic tier. There is
no local body-model lane to configure; that is a design decision, not a
gap.

## Ground rules

- A word means one thing. Before naming anything in the ontology, check it:
  `uv run monty onto check <name>`.
- Vendors are not vocabulary — DataForSEO and ScrapeCreators are tools we
  call, never concepts in the ontology.
- Skills teach METHOD (how to use a tool well for marketing work); the
  ontology defines MEANING (what a word is). Do not put definitions in
  skills or methods in the ontology.
- This repo is public. Nothing tenant-specific, nothing credentialed,
  nothing from socialite's private tree crosses into it.
