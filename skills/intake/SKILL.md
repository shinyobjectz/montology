---
name: intake
description: How a workspace's vocabulary starts — phased questions served to the people who own the code as a clean one-question-at-a-time form in their browser (a local HTML file, no hosted service), answers returned to the agent on disk, each round written from the last and from what the code itself declares, closing with one glossary page rendered from the ontology. Use right after `monty init`, when a repo has few or no words, when someone says "let's define our terms", or before any rename, migration or design-token adoption in a codebase whose vocabulary was never written down.
---

# The intake: the words come from the people, the gate comes from the db

A fresh `monty init` leaves an empty ontology. The code has names; the
people have meanings; nobody has written down which is which. The intake
asks — in a form, because a form is a record and a chat is not — and ends
with `monty onto add`, never with prose. Everything lands in
`.monty/answers/`.

## The loop

```sh
monty intake ask <phase.json>       # serves the form, BLOCKS until submitted, writes .monty/answers/<phase>.answers.json
monty intake answers                # everything answered so far, merged — read this before writing the next phase
monty intake status                 # what is open, what is answered, whether the glossary is rendered
monty intake glossary --open        # the closing page: the whole ontology, rendered from the database
```

`ask` blocks until the submit — run it with the Bash tool's
`run_in_background` and keep working; the process exits the moment the
answers land, which re-invokes you with the result line
`answered  .monty/answers/<phase>.answers.json (N answers)`. If you would
rather watch the file than the process, a Monitor on
`until [ -f .monty/answers/<phase>.answers.json ]; do sleep 1; done; echo answered`
gives the same single notification. Tell the person the form has opened
(the URL is the first line `ask` prints) and that the next round opens
when it is ready — never poll them in chat for answers the form is
collecting.

### Phase 1 — the domain (fixed)

`phases/1-domain.json` in this skill folder is the opening round; serve it
as-is. It asks what the system is, who it serves, what the central things
are called, which words cause arguments, and what frameworks' words are
spoken at the boundary.

### Phase 2 — what the code is asking for (written from phase 1 + the scan)

Run `monty scan --candidates 15` (and `monty explain` if the repo is
unfamiliar). Copy `phases/2-candidates.json` and REWRITE it: one question
per load-bearing candidate, quoting the count (`the code declares
"Harness" 14 times — what is it?`), with the phase 1 answers shaping the
options. A phase 2 that could have been asked of any repo is one you did
not write. Keep it to 6–10 questions; every question exists because the
scan or a phase 1 answer raised it.

### Phase 3 — the definitions (written from phases 1–2)

By now each candidate word has a meaning in the owners' words. For each,
run `monty onto check <term>` and `monty onto similar "<definition>"`
(where the semantics extra is installed) BEFORE proposing it — taken and
near-duplicate meanings are shown. Copy `phases/3-definitions.json`: one
question per word asking them to confirm the one-sentence definition you
drafted or correct it, a part-of-speech question where the collision
judgment needs it, and a choice between alternatives where the name is
already spoken for. Keep it to the 8–12 words that will carry weight.

### Closing — author, then render

1. For each confirmed word: `monty onto add <name> "<their definition,
   one sentence>" --test "<the one-line what-is-it>" --pos noun|verb|value
   [--owner <word>] [--code <dotted>] --note intake:3-definitions`.
   A REFUSED add is the gate — pick the alternative they chose, never
   rename silently. Where they said "we say X, never Y":
   `monty onto rule Y X "<why>"`. Where a framework's word is spoken at
   the boundary: `monty onto collide <term> <framework> "<their meaning>"
   "<ruling>"`.
2. `monty intake glossary --open`. The page renders every word, ruling
   and doctrine block FROM the database, with the answered phases as the
   appendix. An empty ontology is refused with the `onto add` repair.
3. `monty lint` — the new words are now enforced against the code; a
   collision it reports is the first real finding of the vocabulary.

## The phase spec (what `ask` accepts)

```json
{"phase": "2-candidates", "title": "What the code is asking for", "intro": "one line on why these questions",
 "questions": [
   {"id": "snake_case_key", "type": "text|long|url|email|number|choice|multi|scale|yesno",
    "label": "the question, in their language", "help": "optional one line",
    "options": ["for choice/multi"], "min": 1, "max": 5, "labels": ["low", "high"], "required": true}
 ]}
```

`ask` refuses a bad spec with each problem and its repair, and saves the
spec as `.monty/answers/<phase>.json` with the rendered `<phase>.html`
beside it.

## Rules

- **Questions are in their language**, never ours: ask "what do you call
  the thing a user signs up for?" not "define the tenant entity".
- **One question, one thing.** A question that asks two things yields an
  answer that means neither.
- **Choices carry an escape.** Every `choice` ends with an "Other / none
  of these" option unless the options are exhaustive by construction.
- **Answers are evidence, words are rulings.** Quote the answers in the
  word's `--note`; only `monty onto add` makes a word. Never write a
  definition into prose the database does not hold.
- **Never wait in chat for what the form collects.** The process exit or
  the file is the signal; the owners' time is the scarce thing here.
