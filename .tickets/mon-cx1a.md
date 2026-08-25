---
id: mon-cx1a
status: closed
deps: [mon-mamk]
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 2
assignee: shinyobjectz
parent: mon-gh8j
tags: [canvas, governance, review]
---
# Proposals: a pull request for meaning, because ontology.db diffs as noise

montology has a gate but no review unit. Lint tells you the build is broken; it never tells you 'here are six changes to the vocabulary, one of them renames a word 40 files depend on, approve or reject'. Palantir's proposals are the model, and we need them more than they do: the ontology is a SQLite file, so git shows a vocabulary change as a binary blob.

## Design

A proposal is a set of pending changes with a status, an author, and a reason — stored in the database as intents (the same intents write mode posts), not as a second copy of the vocabulary. Applying a proposal replays them through the same code paths; that keeps one writer and means an approved proposal cannot do anything a CLI user could not.

What the reviewer sees, taken from Palantir's review experience and adapted: the changes as GHOST NODES on the live graph — additions glowing, removals faded, edits with before and after on the node. Per-change approve/reject rather than all-or-nothing, because a proposal that bundles a good rename with a bad definition should not have to be rejected whole.

Every change carries its lint verdict, computed against the ontology AS IT WOULD BE if merged. That is the part that makes this more than a UI: a rename that would strand 40 declarations is a fact the reviewer needs before approving, and `monty scan --rename` already computes it.

Merge is the existing gate: a proposal cannot merge while lint fails. No new enforcement path, no second opinion about what correct means.

CLI first, canvas second: `monty onto propose` / `list` / `show` / `approve` / `merge` should be usable in a terminal, because the agent lane matters as much as the human one and an agent should be able to propose a vocabulary change for a human to review.

## Acceptance Criteria

A set of changes can be proposed from CLI or canvas, shown as a readable diff of MEANING rather than of bytes, reviewed per change with the post-merge lint verdict attached, and merged only when the gate passes. A proposal that would strand declarations says so before approval, not after.

