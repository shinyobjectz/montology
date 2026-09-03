# montology-canvas

The vocabulary as a **standard ontology graph** — [WebVOWL](https://github.com/VisualDataWeb/WebVOWL)
renders the exported VOWL JSON. Montology stays the source of truth in SQLite; the
canvas is a thin shell around the real renderer.

    monty canvas export          # Turtle (default)
    monty canvas export xml      # RDF/XML
    monty canvas export vowl     # WebVOWL JSON (what the viewer loads)
    monty canvas                 # serve the graph, open the browser

The page fetches **`/api/ontology.vowl.json`**. Native **`/api/graph`** remains for
tools and tests; the viewer does not use it.

Nothing leaves localhost.

## Building the bundle

From repo root (requires Node):

    cd canvas && npm install && npm run build
    monty canvas stamp

The output lands in `.monty/canvas/src/montology_canvas/static/` (including
`vendor/webvowl.js`) and is committed so `uvx monty canvas` works without Node.
