# montology — repo instructions

Public repo, `socialite-ml/montology`. Also mounted as a submodule of the
private `socialite` repo — never assume socialite's code or vocabulary is
reachable from here; this repo stands alone.

**What this is:** the ontology context layer for any monorepo — a
vocabulary as a database, enforced against the code by a tree-sitter scan.
Nothing else. The marketing era ended at the `marketing-era` tag; do not
resurrect it here.

## The shape

- `.monty/core` — workspace discovery (walk up for `.monty`, like git).
- `.monty/onto` — the database: word / doctrine / overload / gen_runs.
  Montology's own words are authored ONLY in `seed.py` (`just seed`).
- `.monty/scan` — the multiast layer: tree-sitter declarations per
  language, the lint (collision / code-resolution / drift), candidates
  mining, ast-grep invoked for structural search.
- `.monty/gen` — `sync` (deterministic render of the words skill),
  `gen_word` (atomic-tier drafts under law), `lint` (the drift gate + the
  no-prompt ban).
- `.monty/cli` — `monty`; `.plugin/` — the Agent Plugins face; `npm/` —
  the launcher.

## Ground rules

- **Dogfood**: this repo is itself a montology workspace. `monty onto
  check <name>` before naming anything; `just check` runs `monty lint`,
  so a collision or a stale words skill fails the build here too.
- **Prose is rendered, never authored.** `.claude/skills/words/SKILL.md`
  is GENERATED (`monty sync`); hand edits are lost and lint catches them.
- Errors are data with the repair attached. A word means one thing.
  Vendors are not vocabulary.
- This repo is public: nothing tenant-specific, nothing credentialed,
  nothing from socialite's private tree crosses into it.
