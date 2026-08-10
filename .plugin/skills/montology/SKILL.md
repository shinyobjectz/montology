---
name: montology
description: The ontology layer for this repo — a vocabulary as a database, enforced against the code. Use when naming anything (a class, a concept, a tag), when a name feels contested, when vocabulary and code have drifted, or to build an ontology for a codebase from what it already declares.
---

# Montology: the vocabulary is a database

One idea: a repo's words live in `.monty/ontology.db`, prose renders FROM
it, and a scan enforces it against the code. A vocabulary kept in prose
stays correct only as long as someone remembers it; this one has a gate.

## The contract, in order

1. **Check before naming anything.** `monty onto check <name>` (or the
   `ontology_check` tool). FREE means yours; TAKEN shows the definition
   you would collide with; RULED shows what to say instead.
2. **Author deliberately.** `monty onto add <name> "<definition>"
   --test "<one-line what-is-it>" --code <dotted>` — refused with findings
   if taken. One word means one thing; a dotted code lives inside the word
   owning its prefix (`har.cell` needs `har`).
3. **Let the code ask for words.** `monty scan --candidates` mines
   recurring declared names with no word — that is the raw material for
   building an ontology FROM a codebase instead of imposing one on it.
   Define the load-bearing ones; skip the noise.
4. **The gate runs in CI.** `monty lint` fails on: a declaration named
   after a word that means something else (collision), a code prefix that
   resolves to nothing, and generated prose gone stale behind the db.
   Every FAIL carries its repair. An exception you decide to keep is
   recorded in `.monty/montology.toml` `[scan] allow` — a decision, not
   a silence.
5. **Never hand-edit the words skill.** It is GENERATED; `monty sync`
   re-renders it after any change (onto add/rule do this themselves).

## Structural search

`monty grep '<pattern>' --lang <language>` runs ast-grep: patterns parse,
so `def $F($$$)` finds function shapes, not text that looks like them.
Use it to find every usage of a word-bearing symbol before renaming.

## Rules

- A word means one thing. If it cannot, pick a different word.
- Vendors are not vocabulary — tools you buy belong in code, never in a
  sentence about what the system means.
- At a framework's boundary, speak the framework's word; record the
  collision ruling (`monty onto rule`) so the choice is findable.
- Errors are data with the repair attached — relay repairs, do not
  improvise workarounds.
