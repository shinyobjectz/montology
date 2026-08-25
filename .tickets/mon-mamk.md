---
id: mon-mamk
status: open
deps: [mon-z85n]
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 2
assignee: shinyobjectz
parent: mon-gh8j
tags: [canvas, ui, laws]
---
# Write mode: author words and rulings on the canvas, through the CLI's own code paths

Make the canvas a place you can author from — without it becoming a second writer to the database. Every mutation goes through onto_add / onto_rule / onto_route / onto_except, the same functions the CLI calls, so every law and every check applies identically whether a human typed it or dragged it.

## Design

The rule that keeps this honest: THE CANVAS HAS NO SQL. It posts intents to the local server, the server calls the same function the CLI command calls, and the response is whatever that function returns — including a refusal with its repair attached, which the canvas renders as the error rather than inventing its own wording. Errors are data with the repair attached; that already works and must not be re-implemented in TypeScript.

Check-first, live: the name field calls `onto check` as you type, so a taken name is refused with its findings BEFORE the definition has been written. This is the single most valuable thing the canvas can do, because the CLI's check-first discipline currently depends on the author remembering to run it.

isValidConnection is where the structural laws get taught: a containment drag that would make the dotted namespace stop being a tree is refused at drag time, with the reason on the cursor. A route drag opens a form that will not submit without a register — an unscopable route can never gate, so one authored without a register is a ruling that does nothing.

gen_word proposes into the same form: the atomic-tier draft appears as a suggestion in the definition field, law-checked, and a human commits it. Gen proposes, you commit — unchanged.

## Acceptance Criteria

A word, an overload, a collision ruling and a scoped route can all be authored from the canvas, and each is byte-identical in the database to what the equivalent CLI command produces. A refused write shows the engine's own refusal text. A tree-breaking containment drag is impossible, not merely warned about.

