# montology

**Your design system and your vocabulary, enforced — in any repo, by one
command.** montology reads what your code *already declares* — the
Tailwind theme, the CSS, every class and every named thing in ten
languages — and turns it into an ontology with a gate: drift fails CI
with the file, the line, and the repair.

![monty init + lint: theme adopted, drift receipted](docs/demo.gif)

```sh
uvx --from "git+https://github.com/socialite-ml/montology#subdirectory=.monty/cli" monty init
```

*(that one-liner works today, from nothing but `uv`; `npm install -g
montology` and PyPI are landing)*

## Sixty seconds to a drift report

```sh
cd your-repo
monty init            # .monty/, agent wiring — and your Tailwind theme
                      # auto-adopted as design tokens (the theme is the law)
monty lint
```

```
warn design: rogue color #121212 ×2 (first at css/app.scss:37)
     — nearest token: ink #1b1b1f (Δ31)
note design: #ffffff and #fafafa are Δ15 apart (11× / 4×) — one job,
     two values; pick one and tokenize it
note design: class 'ghost-panel' used 6× but defined in no stylesheet
note design: 3 Tailwind arbitrary value(s) — each left the scale
     (p-[13px], text-[#123456]…)
```

No config, no authoring — the theme you already wrote becomes the law,
and every literal that escaped it gets a receipt. Recurring utility
compositions surface too: `monty design recipes` mines the class strings
your markup repeats (`flex flex-wrap gap-2 items-center` ×102 — on
shadcn/ui's own repo) so they can become *named* things.

## The firewall: your agent cannot write drift

![the guard denies the edit before it lands, with the tokens to use](docs/guard.gif)

Everything above is post-hoc. The guard runs **before the write**:
`monty init` installs a PreToolUse hook (merge-safe, into
`.claude/settings.json`) that lints every proposed Write/Edit against the
ontology in milliseconds — a declaration named after a **retired** word
(renames are rulings; always blocks), a collision with an enforced word,
a rogue hex when tokens exist. Deny is exit 2 with the repair on stderr:
the harness feeds it straight back to the model, which corrects and
retries. The agent *physically cannot* introduce a second gray or resurrect
a renamed concept — it gets the token or the current word handed to it
mid-edit. The guard **fails open** (malformed payload, no workspace, any
internal error → allow silently) so it can never break an editor; humans
in vim never meet it. Config: `[guard] names/design = block | warn | off`.

## `monty explain` — the one-shot conceptual X-ray

![point it at a repo it has never seen](docs/explain.gif)

Point montology at any repo cold: one command composes the declared
surface, the vocabulary it has, the vocabulary it is *asking for* (with
definitions drafted on the atomic tier when one serves — law-checked,
refused over wrong), **where meanings actually gather** (semantic
clusters vs the directory tree's claimed architecture: cross-cutting
concepts, grab-bag directories), the design system as measured, and
every place the repo contradicts itself — straight to the terminal,
because an instrument prints findings, it does not decorate them.

## The part that keeps you: words

A repo's concepts drift exactly like its colors. montology's vocabulary
is a **database, not a doc** — one word, one meaning, a one-line test,
an optional dotted code — rendered into a generated agent skill and
enforced against every declaration tree-sitter can parse (python,
ts/tsx, js, go, rust, elixir, ruby, java, c, c++):

![candidates → check-first → advisory collisions](docs/words.gif)

```sh
monty onto check thread        # FREE / TAKEN / RULED — before naming ANYTHING
monty scan --candidates        # the words your codebase is asking for
monty onto add thread "a stateful user↔agent session" --code atl.thread
monty lint                     # collisions (advisory by default), code-tree
                               # integrity, stale prose — each with its repair
```

Rulings end arguments permanently: **overloads** ("say cell, not
sandbox"), **collisions** with frameworks (whose word it is, who moved),
and **renames** — the old name retires, old material stays readable, and
`monty migrate old new --apply` propagates the rename through the code
by *token* (tree-sitter positions, strings and comments untouched,
losslessly round-trippable — proven on eight real repos).

## Semantic hearing

![similar → the string laws pass → the audit hears the duplicate](docs/semantics.gif)

The string laws enforce *one word, one meaning*. The `[semantics]` extra
hears the dual — *one meaning, one word* — with POTION static embeddings
(~30 MB, numpy-only; no torch, no runtime): `monty onto audit` flags two
words defined into the same idea, local words that duplicate inherited
org words under different names, candidates that are secretly existing
words, and owner groupings that don't match where meanings cluster.
Advisory permanently — a cosine score proposes, only a ruling decides.

## One ontology, every repo

The org's vocabulary is authored once — any montology workspace's
`.monty/ontology.db` *is* the artifact — and inherited everywhere:

![inherit the org ontology, renames cross the fleet](docs/org.gif)

```sh
monty init --from git@github.com:acme/ontology.git    # or a path, or a .db URL
monty onto pull                                       # refresh from the pin
```

Upstream rows refresh on every pull; local words always survive; a name
defined in both places is a loud conflict (local wins — reconcile
deliberately). When the org renames a word, every repo's next pull
prints the exact `monty migrate` command: that is how a rename crosses
the fleet.

## The two models it carries (and the ones it refuses)

montology is deliberately near-modelless — the deterministic laws do the
enforcing — but it carries exactly two, each chosen for a measured floor:

| model | size | lane | what it does | what it refuses |
|---|---|---|---|---|
| **POTION** (`potion-base-8M`, model2vec) | ~30 MB, numpy-only | `[semantics]` extra | static embeddings over definitions: `onto similar`, `onto audit` — duplicate meanings, org/local doubles, misfiled clusters. Millisecond inference, no torch, no runtime. | deciding anything. A cosine score proposes; only a ruling makes vocabulary. |
| **gemma3:270m** (via Ollama, optional) | 292 MB, user-installed | `monty gen <word>` | drafts ONE-LINE definitions under the word laws (refused over written wrong) when no host agent is present — the autonomous lane. | bodies and prose. The 270M capability floor is atomic one-liners; everything longer is the host agent's work or a served endpoint (`MONTOLOGY_MODEL_URL`). |

Nothing heavier ships, ever: no torch, no onnxruntime, no bundled
weights. The host agent (Claude, Cursor, Codex) is always the best
drafter available, and the gate never needs a model at all.

## For agents

`monty init` wires the repo for Claude Code, Cursor, and Codex
(merge-safe: sections are appended, JSON keys merged, global config
never touched). The generated `words` skill carries the whole vocabulary
— words, tokens, recipes, rulings, doctrine — and the MCP server exposes
`ontology_check`, `scan_candidates`, `ontology_lint`, `structural_search`
and friends. Prose is rendered from the database, never authored; a
stale render fails the build.

## Under the hood

tree-sitter (via `tree-sitter-language-pack`) measures declarations and
CSS structurally; ast-grep (invoked, one static binary) powers
structural pattern search; SQLite holds the vocabulary. The stress
battery (`stress/run.py`, weekly in CI) proves four properties on eight
real repos — flask, excalidraw, gin, ripgrep, phoenix, sinatra,
spring-petclinic, redis: merge-safe idempotent init, zero-error parsing,
truthful collision reporting, and lossless migrate round-trips.

## Contributors

```sh
git clone https://github.com/socialite-ml/montology && cd montology
uv sync && just              # the action surface
just check                   # the gate (montology lints itself, strictly:
                             # its own toml sets collisions = "enforce")
```

The marketing-era codebase lives at the `marketing-era` tag.
