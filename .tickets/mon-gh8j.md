---
id: mon-gh8j
status: closed
deps: []
links: []
created: 2026-08-25T19:36:19Z
type: epic
priority: 1
assignee: shinyobjectz
tags: [canvas, ontology, ui, research]
---
# The ontology canvas: build, write and review the vocabulary on a graph

montology's vocabulary is a database with a gate, and the only two faces on it are a CLI and a rendered skill. Neither shows the SHAPE of what is there. That matters more than it sounds: a vocabulary is a graph, people reason about graphs by looking at them, and the one thing a table cannot show is which words are load-bearing and which are floating unattached to any code.

The research (Palantir Foundry Ontology; Microsoft Azure Digital Twins/DTDL and Fabric's digital twin builder) says the pros' differentiator is NOT the metamodel — their metamodels are thinner than ours in the places that matter. It is two other things: governance (a proposal is a pull request for meaning, reviewed per resource before it lands) and a canvas (Fabric's 'semantic canvas' is where entities and relationships are actually authored).

The finding that shapes this epic: montology already carries FIVE kinds of edge that nobody can currently see — containment (owner + dotted code), routes (say-this-not-that, scoped by REGISTER, which no vendor has), rulings (overload/collision/rename/exception), bearings and seams (word to code surface), and doctrine. Plus the scan, which means our graph includes the source tree: 5,237 declarations in qubie resolving — or failing to resolve — to 99 words. Neither Palantir nor Microsoft reads your code.

So the order is: render what exists before adding anything. A canvas over the five edges we already have is more expressive than either vendor's, on day one.

## Design

ONE canvas, three modes, matching the three verbs.

BUILD — the graph as it is. Word nodes coloured by kind, containment as layout, routes as directed edges labelled with their register, rulings rendered as NODES rather than edge labels (a collision carries a why and a date; an edge label cannot hold that), surface nodes with seam edges, candidates greyed in from the scan — 'the code is asking for this word'. A word node shows its declaration count and how many resolve wrongly.

WRITE — a node opens into a law-checked draft. `monty onto check` runs live against the name field; the one-sentence law, the no-vendor law and the definition-shape law fire BEFORE save. Svelte Flow's isValidConnection refuses a drag that would break the code namespace's tree property at drag time — the difference between a canvas that teaches and one that records.

REVIEW — proposals. Pending changes render as ghost nodes and edges over the live graph: additions glow, removals fade, each carrying its lint verdict. Per-word approve, taken straight from Palantir. This is also how the binary-diff problem gets solved: the diff is rendered from a proposal table, not from git, because ontology.db is a SQLite file and git shows it as noise.

ARCHITECTURE — follow the intake precedent exactly, because it already works: a stdlib HTTP server bound to localhost, a self-contained page, the process exit as the agent's signal, state on disk as the contract. The Svelte Flow bundle is built in canvas/ and its OUTPUT is committed into the Python package under the same discipline as sync — generated, never hand-edited, provenance-hashed, lint catches drift. Every write goes through the existing onto add / onto rule / onto route code paths, so the canvas is a FACE, not a second writer. That is not a nicety: one truth with one gate is the whole thesis. Nothing leaves localhost.

WHAT WE ARE NOT BUILDING — see the decision ticket. Palantir-style domain link types (hasPart, usedIn) exist to power runtime object traversal. montology has no runtime objects. Copying them would be cargo cult.

## Acceptance Criteria

`monty canvas` opens a local page showing montology's own 26 words and qubie's 99 with every edge type visible; a word can be authored and a ruling made from the canvas with every existing law enforced; a set of changes can be proposed, reviewed with its lint verdict attached, and merged; and `monty onto review` names anti-patterns in the vocabulary the way Palantir's catalogue names them. The canvas never writes the database except through the code paths the CLI uses.


## Notes

**2026-08-25T20:03:45Z**

TECH DECISION, taken during mon-gskj: NOT Svelte Flow. Two reasons that only appeared once the graph endpoint existed. (1) Every edge in montology is a form, not a gesture — a route is (from_term, to_word, register, scope, why), so a drag gives you two of five fields and still needs the modal; drag-to-connect with isValidConnection was the strongest argument for the library and it does not hold. (2) The graph is a sparse tree with satellites (qubie: 169 nodes, 82 edges, 36 containment), which is precisely where node-link diagrams read worst — and the layout was hand-written anyway, which is where a flow library earns most of its keep. Built on plain Svelte + SVG instead: 58kB vs 216kB for a TRIVIAL Svelte Flow app. Consequence for mon-mamk: the write mode's 'isValidConnection refuses a tree-breaking drag' becomes 'the form refuses it', which is the same law in the right place. The canvas also opens FOCUSED on one word's neighbourhood rather than showing the whole graph.

**2026-08-25T20:28:36Z**

EPIC COMPLETE. All eight children closed; gate green (204 tests, monty lint ok, bundle current). Verified end to end against both workspaces: montology 33 words / 95 nodes / 262 edges, qubie 99 words / 192 nodes / 88 edges, with all eight edge kinds drawn across the two (contains, genus, rules, answers, bears, seam, routes, renamed, overloaded). Author from the canvas with check-first unskippable; propose, review with the gate run against the merged world, and merge; monty onto review names the anti-patterns. The canvas writes only through the ontology's intents, which are the same functions the CLI calls. Two epic assumptions were corrected by contact with the work and both are recorded in the notes above: Svelte Flow was dropped (every edge here is a form, not a gesture; the graph is a sparse tree, not a network), and a word node carries collides/excepted rather than 'declarations that resolve to it', because in montology's model a declaration wearing a word's name is a COLLISION. Four bugs were found by the tools building each other rather than by reasoning: the words skill defining scan as 'the tree-sitter sweep' (a seeded vendor the word laws never checked), scan exclude matching bare names while every workspace writes globs (qubie: 5237 declarations to 2180), Chrome not painting a zero-sized svg, and qubie routing intelligence to brain at register all where it can never gate.
