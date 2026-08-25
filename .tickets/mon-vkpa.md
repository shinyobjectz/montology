---
id: mon-vkpa
status: open
deps: [mon-z85n]
links: []
created: 2026-08-25T19:38:08Z
type: task
priority: 3
assignee: shinyobjectz
parent: mon-gh8j
tags: [intake, review, ontology]
---
# Competency questions: keep what intake asks, and re-run it as a test

The academic practice both vendors underplay: an ontology is correct if it answers the questions it was built to answer. Competency questions are the requirements, and they are supposed to be kept and re-run. montology already ASKS the right questions in intake — and then throws the requirement away once the answers are on disk.

## Design

A question is a durable row linked to the words that answer it. That gives coverage in both directions, and both directions are findings:
  - a question no word answers — the vocabulary has a hole where somebody said there was a need.
  - a word no question motivates — vocabulary nobody asked for, which is how a glossary grows into something nobody reads.

The second is the more interesting one and it is the check no vendor ships.

Source them from intake, which already runs phased rounds and writes each round from the last — phase 1 is already close to a competency-question round in everything but what it does with the answers. The glossary render is the natural place to show coverage.

On the canvas a question is a node, and the edges to the words that answer it are the coverage. An unanswered question and an unmotivated word should both be visible without filtering for them.

## Acceptance Criteria

Questions survive intake as rows, `monty onto health` reports coverage both ways, and the canvas shows unanswered questions and unmotivated words. Running intake twice does not duplicate a question.

