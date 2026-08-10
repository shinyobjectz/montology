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

## The part that keeps you: words

A repo's concepts drift exactly like its colors. montology's vocabulary
is a **database, not a doc** — one word, one meaning, a one-line test,
an optional dotted code — rendered into a generated agent skill and
enforced against every declaration tree-sitter can parse (python,
ts/tsx, js, go, rust, elixir, ruby, java, c, c++):

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

## One ontology, every repo

The org's vocabulary is authored once — any montology workspace's
`.monty/ontology.db` *is* the artifact — and inherited everywhere:

```sh
monty init --from git@github.com:acme/ontology.git    # or a path, or a .db URL
monty onto pull                                       # refresh from the pin
```

Upstream rows refresh on every pull; local words always survive; a name
defined in both places is a loud conflict (local wins — reconcile
deliberately). When the org renames a word, every repo's next pull
prints the exact `monty migrate` command: that is how a rename crosses
the fleet.

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
