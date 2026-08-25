<script>
  import Viewport from './lib/Viewport.svelte';
  import GraphNode from './lib/GraphNode.svelte';
  import Detail from './lib/Detail.svelte';
  import Spine from './lib/Spine.svelte';
  import Compose from './lib/Compose.svelte';
  import { index, edgeLook, elbow } from './lib/util.js';
  import { focusLayout, overviewLayout } from './lib/layout.js';

  // Half the wire layer's box. Big enough that no laid-out graph reaches the
  // edge of it, small enough to stay an ordinary coordinate space.
  const SPAN = 12000;

  let graph = $state(null);
  let error = $state('');
  let focus = $state(null);      // the node the canvas is answering about
  let selected = $state(null);   // what the detail rail is showing
  let authoring = $state(false);

  function load() {
    return fetch('./api/graph')
      .then((r) => (r.ok ? r.json() : r.json().then((e) => Promise.reject(e.error ?? r.statusText))))
      .then((g) => {
        graph = index(g);
        // a node the write may have replaced must not stay on screen stale
        if (focus) focus = graph.byId.get(focus.id) ?? null;
        if (selected) selected = graph.byId.get(selected.id) ?? null;
      })
      .catch((e) => { error = String(e); });
  }

  $effect(() => { load(); });

  const view = $derived.by(() => {
    if (!graph) return { pos: new Map(), shown: new Set() };
    return focus ? focusLayout(graph, focus.id) : overviewLayout(graph);
  });

  const shownNodes = $derived(graph ? graph.nodes.filter((n) => view.shown.has(n.id)) : []);
  // Fit to what is on the canvas, not to the origin: a view centred on (0,0)
  // shows the middle of a layout that starts there and runs down.
  const bounds = $derived.by(() => {
    const ps = [...view.pos.values()];
    if (!ps.length) return null;
    const xs = ps.map((p) => p.x), ys = ps.map((p) => p.y);
    return { minX: Math.min(...xs), maxX: Math.max(...xs),
             minY: Math.min(...ys), maxY: Math.max(...ys) };
  });
  const shownEdges = $derived(graph
    ? graph.edges.filter((e) => view.pos.has(e.source) && view.pos.has(e.target))
    : []);
  // Two rulings between the same pair are two decisions. Give each its own lane
  // so neither the wire nor the label can be mistaken for the other's.
  const lane = $derived.by(() => {
    const seen = new Map(), out = new Map();
    for (const e of shownEdges) {
      const key = `${e.source}|${e.target}`;
      const n = seen.get(key) ?? 0;
      seen.set(key, n + 1);
      out.set(e.id, n);
    }
    // centre the lanes on the direct line rather than hanging them below it
    for (const e of shownEdges) {
      const key = `${e.source}|${e.target}`;
      out.set(e.id, out.get(e.id) - (seen.get(key) - 1) / 2);
    }
    return out;
  });

  function pick(node) {
    selected = node;
    // Picking a word MOVES the canvas to it. Anything else only fills the rail:
    // a ruling's neighbourhood is the word it rules on, which you are already
    // looking at, so re-centring on it would lose your place for nothing.
    if (node.kind === 'word' || node.kind === 'surface') focus = node;
  }
</script>

<div class="shell">
  <aside class="rail left">
    <h1 class="mono">montology{#if graph}<span class="ws"> · {graph.workspace}</span>{/if}</h1>
    {#if graph}<Spine {graph} {selected} onpick={pick} />{/if}
  </aside>

  <main>
    {#if error}
      <p class="error mono">{error}</p>
    {:else if !graph}
      <p class="loading mono">reading the ontology…</p>
    {:else}
      <div class="bar">
        <button class="crumb mono" class:on={!focus} onclick={() => { focus = null; selected = null; }}>
          all {graph.stats.words} words
        </button>
        {#if focus}<span class="sep">›</span><span class="crumb on mono">{focus.label}</span>{/if}
        <button class="author mono" class:on={authoring}
                onclick={() => (authoring = !authoring)}>{authoring ? '× close' : '+ author'}</button>
        <span class="vitals mono">
          {#each Object.entries(graph.stats) as [k, v]}<span>{v} {k}</span>{/each}
        </span>
      </div>

      <Viewport resetKey={focus?.id ?? 'all'} {bounds}>
        {#snippet children()}
          <!-- A zero-sized <svg> is not painted, `overflow: visible` or not, so
               the wire layer is given a real box and its contents are shifted
               back onto the world origin. -->
          <svg class="wires" width={SPAN * 2} height={SPAN * 2} style="--span:{SPAN}">
            <defs>
              {#each [...new Set(shownEdges.map((e) => e.kind))] as kind}
                <marker id="a-{kind}" viewBox="0 0 8 8" refX="7" refY="4"
                        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M0,0 L8,4 L0,8 z" fill={edgeLook({ kind }).color} />
                </marker>
              {/each}
            </defs>
            <g transform="translate({SPAN},{SPAN})">
            {#each shownEdges as e (e.id)}
              {@const look = edgeLook(e)}
              <path d={elbow(view.pos.get(e.source), view.pos.get(e.target), lane.get(e.id))}
                    fill="none" stroke={look.color} stroke-width={look.width}
                    stroke-dasharray={look.dash} opacity={look.opacity}
                    marker-end={e.kind === 'contains' ? null : `url(#a-${e.kind})`} />
            {/each}
            <!-- A route's REGISTER is the thing that makes it enforceable, so it
                 is on the wire, not hidden in a panel. Containment needs no
                 label: the geometry already says it. -->
            {#each shownEdges.filter((e) => e.kind !== 'contains' && e.kind !== 'seam') as e (e.id + ':t')}
              {@const a = view.pos.get(e.source)}
              {@const b = view.pos.get(e.target)}
              {@const look = edgeLook(e)}
              <text class="wirelabel" x={(a.x + b.x) / 2}
                    y={(a.y + b.y) / 2 - 7 + lane.get(e.id) * 13}
                    text-anchor="middle" fill={look.color} opacity={look.opacity}>
                {look.label}{e.data?.gates === false ? ' · cannot gate' : ''}
              </text>
            {/each}
            </g>
          </svg>

          {#each shownNodes as n (n.id)}
            {@const p = view.pos.get(n.id)}
            <div style="position:absolute; left:{p.x}px; top:{p.y}px">
              <GraphNode node={n} focused={focus?.id === n.id}
                         selected={selected?.id === n.id} onpick={pick} />
            </div>
          {/each}
        {/snippet}
      </Viewport>
    {/if}
  </main>

  <aside class="rail right">
    {#if graph}
      {#if authoring}
        <Compose intents={graph.intents ?? []} token={graph.token} onwrote={load} />
      {:else}
        <Detail node={selected} {graph} onpick={pick} />
      {/if}
    {/if}
  </aside>
</div>

<style>
  .shell { display: grid; grid-template-columns: 258px 1fr 314px; height: 100%; }
  .rail { display: flex; flex-direction: column; padding: .7rem .75rem; overflow: hidden;
          background: var(--panel); }
  .rail.left { border-right: 1px solid var(--line); }
  .rail.right { border-left: 1px solid var(--line); overflow-y: auto; }
  h1 { font-size: .82rem; margin: 0 0 .6rem; font-weight: 700; letter-spacing: -.01em; }
  .ws { color: var(--dim); font-weight: 400; }
  main { display: flex; flex-direction: column; min-width: 0; }
  .bar { display: flex; align-items: center; gap: .4rem; padding: .45rem .7rem;
         border-bottom: 1px solid var(--line); background: var(--panel); }
  .crumb { font-size: .72rem; background: none; border: 0; color: var(--dim); cursor: pointer; padding: 0; }
  .crumb.on { color: var(--ink); font-weight: 600; }
  .sep { color: var(--dim); font-size: .72rem; }
  .author { font-size: .68rem; margin-left: .6rem; padding: .1rem .4rem; cursor: pointer;
            border-radius: 4px; border: 1px solid var(--line); background: none; color: var(--dim); }
  .author.on { color: var(--accent); border-color: var(--accent); }
  .vitals { margin-left: auto; display: flex; gap: .7rem; font-size: .64rem; color: var(--dim); }
  .wires { position: absolute; left: calc(var(--span) * -1px); top: calc(var(--span) * -1px);
           pointer-events: none; }
  .wirelabel { font: 9px ui-monospace, SFMono-Regular, Menlo, monospace;
               paint-order: stroke; stroke: var(--bg); stroke-width: 3px; stroke-linejoin: round; }
  .loading, .error { padding: 1.4rem; font-size: .78rem; color: var(--dim); }
  .error { color: var(--term); }
</style>
