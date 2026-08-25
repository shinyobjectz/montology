---
id: mon-by5n
status: closed
deps: []
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 1
assignee: shinyobjectz
parent: mon-gh8j
tags: [decision, research, ontology]
---
# DECIDE: no domain link types — what montology deliberately will not copy

Palantir's link types and DTDL's relationships are the first thing anyone reaches for when they see an ontology on a canvas: hasPart, usedIn, cools, isBilledTo. Decide DELIBERATELY whether montology grows them, because it is hard to reverse — once a repo has authored two hundred domain edges they are load-bearing whether or not they were a good idea.

## Design

The case FOR: it is what the pros do, it makes the canvas immediately richer, and it is what a newcomer expects an ontology to be.

The case AGAINST, which I think wins: link types exist to power RUNTIME OBJECT TRAVERSAL. Palantir has objects — instances, millions of them — and a link type is how a query walks from one to another. DTDL has twins. Fabric has entity INSTANCES alongside entity types. montology has none of that: it has words and the code that answers to them. A hasPart edge between two words would be an assertion nothing can check, and an ontology whose edges cannot be enforced is a diagram — which is the artefact this repo exists to replace.

Every edge montology has today is enforceable: containment gates the code namespace, a route gates what you may say in a register, a ruling gates a name, a bearing is checked against the scan. That is the test a new edge type has to pass.

The one relation that DOES pass it is subsumption (kind_of) — see the separate ticket — because a word that is a kind of another inherits its rulings and its guard behaviour, so the edge changes what the gate does.

Capabilities/interfaces (Palantir's Inspectable, Schedulable) are the strongest idea in their model and are DEFERRED, not rejected: they exist so functions and actions can target many types, and montology has neither yet. Revisit if montology ever grows a kinetic layer.

## Acceptance Criteria

A doctrine block in the database saying what montology's edges are for and why domain relations are not among them — so the question is answered once and not re-litigated every time someone new sees the canvas. `monty onto check` on the words the decision introduces runs before any of them are named.


## Notes

**2026-08-25T19:44:21Z**

DECIDED: no domain link types. Doctrine 'An edge must be enforceable' (ord 60) is in the database and renders into the words skill. The admission test is stated: every relation montology holds gates something — containment gates the namespace, a route gates a register, a ruling gates a name, a bearing is checked against the scan. Palantir/DTDL link types fail it because they exist for runtime object traversal and montology has no instances. The genus PASSES (a word inherits its genus's rulings and guard behaviour) and is named genus rather than kind-of because kind already means provenance. Capabilities deferred, not refused, with the condition for revisiting written down. New word: edge (onto.edge), checked free before naming.
