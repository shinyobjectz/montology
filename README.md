# montology

**The ontology context layer for any monorepo.** A repo's vocabulary lives
in a database — words with one meaning each, dotted codes, doctrine, and
rulings — rendered to prose for agents, and **enforced against the code**:
a tree-sitter scan of every declaration, a lint that fails CI when code
and vocabulary disagree, and errors that carry their repair.

Born from a private system that ran this discipline for real: the last
vocabulary was prose kept in sync by remembering to, which is how a
correctly written permission check came to exist and never be called.
A vocabulary with a gate cannot drift silently.

## Quick start

```sh
npm install -g montology     # a thin launcher: ensures uv, runs the engine via uvx
cd your-repo
monty init                   # .monty/ (the db + config), agent wiring, the words skill
```

`monty init` is deliberately minimal inside YOUR repo: it creates
`.monty/` (an empty ontology — yours to author), appends a marked section
to CLAUDE.md / AGENTS.md (never overwrites), merges one key into
`.mcp.json` (Claude Code) and `.cursor/mcp.json` (Cursor), and renders the
generated `words` skill. Codex users get the exact `~/.codex/config.toml`
snippet printed — montology never edits files outside your repo.

## The loop

```sh
monty onto check thread          # FREE / TAKEN / RULED — before naming ANYTHING
monty scan --candidates          # what the codebase is asking for: recurring
                                 # declared names with no word
monty onto add thread "a stateful user↔agent session" --code atl.thread
monty grep 'class $C' --lang python    # structural search (ast-grep)
monty lint                       # the gate: collisions, code resolution, drift
```

- **Collision**: a `class Atlas` when `atlas` is a core word meaning
  something else → FAIL with the repair (rename, or record the exception
  in `.monty/montology.toml [scan] allow` — a decision, not a silence).
- **Codes are a tree**: `har.cell` cannot exist without a word owning `har`.
- **Prose is rendered, never authored**: the `words` skill regenerates from
  the db (`monty sync`); lint fails when it goes stale.

## The multiast layer

tree-sitter (via `tree-sitter-language-pack` — 100+ maintained grammars)
measures declarations across python, typescript/tsx, javascript, go, rust,
elixir, ruby, java, c, c++ out of the box; unsupported languages are
skipped *and said to be skipped*. ast-grep (invoked, never linked — one
static binary) powers structural search: patterns that parse, not regexes.

## For agents

`.plugin/` is an Agent Plugins 1.0.0 folder (plugin.json · mcp.json ·
skills/). The MCP server exposes `ontology_check`, `ontology_add`,
`ontology_words`, `scan_surface`, `scan_candidates`, `ontology_lint`,
`structural_search`. The generated `words` skill puts the whole
vocabulary in the agent's context, and the doctrine — the *why* behind
each decision — travels with it.

## The shape

```
.monty/          the engine (uv workspace: core · onto · scan · gen · cli)
.plugin/         the Agent Plugins face
npm/             the npm launcher (package `montology`, bin `monty`)
```

In YOUR repo, montology's whole footprint is `.monty/` (db + config), the
generated skill, and the marked sections it appended. `rm -rf .monty
.claude/skills/words` and the sections is a full uninstall.

## Contributors

```sh
git clone https://github.com/socialite-ml/montology && cd montology
uv sync && just              # the action surface
just check                   # the gate (montology lints itself)
```

The marketing-era codebase (brand crawling, embedding zoo, creative
production) lives at the `marketing-era` tag.
