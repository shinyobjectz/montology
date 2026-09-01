# Changelog

What changed, and why it mattered. Entries follow
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are the
ones published to npm and PyPI.

The `Unreleased` section is what is on `main` and not yet cut into a
version — montology has shipped continuously from `main` since 0.2.0, so
that section is long on purpose. The marketing-era codebase montology grew
out of is preserved at the [`marketing-era`](https://github.com/shinyobjectz/montology/tree/marketing-era)
tag and shares no code with this one.

## Unreleased

### Added

- **Swift is read.** `.swift` was recognised by extension and parsed to
  nothing — a Swift tree scanned clean because nothing looked at it.
  Declarations (struct, class, enum, actor, protocol, typealias,
  associatedtype, function, method), type declarations, name→type bindings
  and call acts now all cover Swift, which lights up `scan`, `lint`, the
  guard, `explain` and `migrate` for it. An `extension Harness` correctly
  does **not** count as declaring `Harness`.
- **`monty config`** — read and change what a workspace is tuned to
  (`guard.names`, `guard.design`, `scan.collisions`, `scan.enforced_kinds`,
  `scan.exclude`, `scan.include`, `design.enforce`). Every key reports its
  value, where that value came from, and what it does. Writes edit
  `montology.toml` in place so its comments survive; an unknown key or a
  disallowed value is refused with the allowed set.
- **The plugin ships the firewall it advertises.** `.plugin/hooks/hooks.json`
  plus a `scripts/guard.sh` that bails in pure shell before any interpreter
  starts — a plugin install has no `monty init` to run, and a hook on the
  write path must cost nothing in repos that never asked for montology.
- **Cursor gets the pre-write guard**, not only the MCP server:
  `monty init` writes `.cursor/hooks.json`, and the guard speaks Cursor's
  `preToolUse` dialect (top-level edit payloads, and the JSON verdict
  Cursor reads alongside exit 2).
- **`monty doctor` verifies the hooks are actually wired**, per harness.
- Four MCP tools that had no equivalent: `repo_explain`, `ontology_similar`,
  `ontology_rule`, `workspace_config`.
- `acts` — what the code *does*, the half the declaration scan never
  measured: a subject, a verb and an object read off the tree, with names
  bound to types so an edge survives renaming the variable.
- `canvas` — the ontology as a document with the graph as a figure;
  authoring from it goes through the engine's own front door.
- `intake` — the phased questions a workspace starts with, served as a
  local form, answered on disk, closing in a rendered glossary.
- `proposals` — a pull request for meaning, with the gate run against the
  merged world; `questions` — what the vocabulary is answerable to, checked
  both ways; `genus` — the one structural relation that gates something;
  `onto review` — the anti-pattern catalogue, calibrated by running it.
- `surfaces` and `seams` — what a repo stands on and where it touches it.

### Changed

- **Montology stopped reading as a CSS tool.** Every routing surface — the
  skill description, `plugin.json`, the MCP instructions, the section
  `monty init` writes into `CLAUDE.md`/`AGENTS.md`, and this README — led
  with Tailwind and design tokens, so agents in other repos concluded
  montology was for styling. Code leads everywhere now; design values are
  stated as one kind of word among many. `monty init`'s next steps lead
  with `explain` and `scan --candidates`, and only mention design when the
  repo actually has a theme.
- The `montology` skill opens with a **routing table** — new repo, empty
  vocabulary, working repo, unfamiliar repo — with the questions to ask
  before running `init`, the staged path from advisory to enforced, and a
  documented settings surface.
- The guard covers `NotebookEdit`. Repos wired before this get their
  matcher widened in place rather than a second hook appended.
- The words skill **tiers** past its budget instead of truncating: the page
  keeps the words and the rulings and hands the rest to reference pages.
- A collision is judged on **what the word names** (verb / noun / value),
  not by one blanket rule — a verb doing ordinary work below the surface is
  not a second meaning.
- Exceptions moved into the database (`monty onto except`), where they
  carry their reason and the paths they hold in. The old reasonless
  `[scan] allow` list is still honoured and still reported.

### Fixed

- **`monty intake ask '<json>'` never worked on Linux.** The spec reader
  told inline JSON from a path by stat-ing it, and a 900-byte "filename"
  answers ENAMETOOLONG on Linux (which `Path.exists()` re-raises) and
  `False` on macOS. Decided by shape now — a JSON object starts with `{`.
- **CI had been red for nineteen consecutive runs.** Three independent
  causes, each hidden behind the one before it: the workflow ran bare
  `pytest` instead of the `-m "not integration"` that `pytest.ini` has
  always documented; the intake bug above; and the weekly stress battery's
  collision drill stopped authoring its victim word when `--pos` became
  required, so it reported `fired=False` on all eight repos — the gate was
  never broken, the probe was. `just check` now runs what CI runs.
- **`monty migrate` reported Swift and Kotlin trees as already clean.**
  `simple_identifier` was missing from the sweep's identifier set, so every
  function, property and enum case was invisible to it — a confident
  "clean" over files it never read.
- **`[scan] exclude` matched nothing.** The globs every workspace had
  written were inert, so scans reported confident counts over files nobody
  meant to include.
- `onto add` no longer accepts a name a rename retired.

## 0.2.0 — 2026-08-10

Meaning over time: the three research tracks became one feature.

### Added

- `monty vitals` — one verdict per repo (TENDED / DRIFTING / UNTENDED),
  every reason carrying its repair; `--json` for dashboards, `--strict`
  for CI.
- `monty drift` — the git history sampled into lexicon, palette and
  convergence curves.
- `monty guard --stats` — repair-following, measured from the hook log.
- **The firewall**: a PreToolUse hook that lints a proposed edit *before*
  it lands, and denies with the repair attached.
- **`monty explain`** — the one-shot conceptual X-ray of any repo, cold.
- **Semantic hearing** (`[semantics]` extra): POTION static embeddings,
  ~30 MB and numpy-only, powering `onto similar` and `onto audit` —
  advisory permanently, because a cosine score proposes and only a ruling
  decides.
- **One ontology, every repo**: `monty init --from`, `monty onto pull`,
  and a rename that crosses the fleet.
- Design values as vocabulary: tokens, the style surface, recipe mining,
  and drift with the nearest token named.
- The stress battery — eight real repos, four provable properties.
- Distribution: `montology@0.2.0` on npm, the skill indexed on skills.sh.

## 0.1.0 — 2026-08-10

**The pivot**: montology became the ontology context layer for any
monorepo. The vocabulary is a database, prose renders from it, and a
tree-sitter scan enforces it against the code.

### Added

- `monty init` — workspace discovery that walks up like git, merge-safe
  agent wiring, and a footprint measured in seconds.
- The vocabulary: `onto check` / `add` / `amend`, one word meaning one
  thing, with the check-first contract.
- Rulings — overloads, framework collisions, and renames — plus
  `monty migrate`, which propagates a rename through the code by token
  with strings and comments structurally untouchable.
- `monty lint` — the gate, with every FAIL carrying its repair.
- The generated `words` skill, rendered from the database and never
  authored by hand.
