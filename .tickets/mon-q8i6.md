---
id: mon-q8i6
status: in_progress
deps: [mon-by5n]
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 2
assignee: shinyobjectz
parent: mon-gh8j
tags: [ontology, schema, laws]
---
# kind_of: subsumption, the one structural relation that earns its place

The gap the research found: montology has containment, routing and rulings, but no way to say one word IS A KIND OF another. This is the relation worth adding, and the reason is the test from the link-types decision — it is enforceable. A word that is a kind of another inherits its rulings and its guard behaviour, so the edge changes what the gate does.

## Design

A kind_of table, or a column — decide when writing it, but note that a word can be a kind of more than one thing (composition over deep hierarchies, per Palantir's own principle), which argues for a table.

kind_of is NOT owner. Containment says where a word lives in the namespace; subsumption says what it is. `scan.collision` lives inside `scan` and is not a kind of scan. Getting this confused is how ontologies rot, so the distinction belongs in the doctrine and in the error text when someone draws the wrong one.

The checks that make it worth having:
  - cycles are refused (a kind of itself, transitively) — chains.py already has the shape of this for routes and the algorithm carries over.
  - OntoClean's rigidity test, as far as it can be run without a philosopher: a RIGID word (what a thing IS, permanently) may not be a kind of an ANTI-RIGID one (a role a thing plays for a while). Person is rigid; Student is a role. Person kind_of Student is the classic error and it is mechanically catchable once words carry the metaproperty.
  - inherited rulings surface in the words skill and on the canvas — an inherited ruling that is invisible is a trap.

This adds one field to the word (rigidity) and one table. Resist adding the rest of OntoClean; identity and unity need judgement the tool cannot supply, and a metaproperty nobody fills in correctly is worse than none.

## Acceptance Criteria

kind_of can be authored from the CLI and the canvas, cycles are refused with the path shown, a rigid-under-anti-rigid subsumption is refused with the OntoClean reason in plain words, and inherited rulings appear wherever the word's own rulings appear.

