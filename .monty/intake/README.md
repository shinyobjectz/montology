# montology-intake

How a workspace's vocabulary gets its first words: the agent asks, the
people who own the code answer in a browser, the answers land in
`.monty/answers/` as JSON, and the agent writes the next round from them.

- `monty intake ask <phase.json>` — serve one phase as a one-question-at-a-time
  form on localhost, open the browser, block until submitted, write
  `.monty/answers/<phase>.answers.json`, exit. The exit is the signal.
- `monty intake answers` — every answered phase, merged, as JSON.
- `monty intake status` — open and answered phases, glossary state.
- `monty intake glossary` — the closing page: the whole ontology (words,
  rulings, doctrine) rendered from the database, the answers as appendix.

No hosted service, no CDN: a file on disk plus a stdlib HTTP server that
lives only as long as one phase takes to answer.
