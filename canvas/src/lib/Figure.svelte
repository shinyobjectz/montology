<script>
  // The ONE place a graph earns its keep. Of montology's 283 edges, 186 are
  // seams (dependency code, a different subject), 31 are containment (a tree)
  // and 9 are attachments — only the 17 relations are a network you would want
  // to SEE. So the graph is a figure inside the document, at the size the data
  // deserves, rather than the document being a graph.
  import { arc, verbColor } from './util.js';

  let { graph, onpick } = $props();

  const rel = $derived(graph.edges.filter((e) => e.kind === 'relation' || e.kind === 'act'));

  const view = $derived.by(() => {
    const degree = new Map();
    for (const e of rel) {
      degree.set(e.source, (degree.get(e.source) ?? 0) + 1);
      degree.set(e.target, (degree.get(e.target) ?? 0) + 1);
    }
    const ids = [...degree.keys()].sort((a, b) => degree.get(b) - degree.get(a));
    const pos = new Map();
    const R = [0, 150, 250];
    let i = 0;
    for (let ring = 0; ring < R.length && i < ids.length; ring++) {
      const room = ring === 0 ? 1 : Math.max(7, Math.round((2 * Math.PI * R[ring]) / 92));
      const here = ids.slice(i, i + room);
      here.forEach((id, k) => {
        const a = (2 * Math.PI * k) / here.length - Math.PI / 2;
        pos.set(id, ring === 0 ? { x: 0, y: 0 }
          : { x: Math.cos(a) * R[ring], y: Math.sin(a) * R[ring] * 0.82 });
      });
      i += here.length;
    }
    const lane = new Map();
    const seen = new Map();
    for (const e of rel) {
      const k = `${e.source}|${e.target}`;
      const n = seen.get(k) ?? 0;
      seen.set(k, n + 1);
      lane.set(e.id, n);
    }
    for (const e of rel) {
      const k = `${e.source}|${e.target}`;
      lane.set(e.id, lane.get(e.id) - (seen.get(k) - 1) / 2);
    }
    return { pos, lane, ids };
  });
</script>

{#if rel.length}
  <figure>
    <figcaption>
      What acts on what — {rel.length} relation{rel.length > 1 ? 's' : ''} over
      {view.ids.length} words. The only part of this vocabulary that is a network.
    </figcaption>
    <svg viewBox="-330 -260 660 520" role="img" aria-label="the relation graph">
      {#each rel as e (e.id)}
        {@const a = view.pos.get(e.source)}
        {@const b = view.pos.get(e.target)}
        {#if a && b}
          {@const path = arc(a, b, view.lane.get(e.id) * 0.5)}
          {@const c = verbColor(e.data.verb, { defined: e.data.defined !== false })}
          <path d={path.d} fill="none" stroke={c} stroke-width="1.4" opacity=".85" />
          <text x={path.mid.x} y={path.mid.y} fill={c} text-anchor="middle">{e.data.verb}</text>
        {/if}
      {/each}
      {#each view.ids as id (id)}
        {@const p = view.pos.get(id)}
        {@const node = graph.byId.get(id)}
        {#if p && node}
          <g class="n" onclick={() => onpick(node)} role="button" tabindex="0"
             onkeydown={(e) => e.key === 'Enter' && onpick(node)}>
            <rect x={p.x - 46} y={p.y - 11} width="92" height="22" rx="4" />
            <text class="lbl" x={p.x} y={p.y + 4} text-anchor="middle">{node.label}</text>
          </g>
        {/if}
      {/each}
    </svg>
  </figure>
{/if}

<style>
  figure { margin: 0 0 1.4rem; }
  figcaption { font-size: .72rem; color: var(--dim); line-height: 1.5; margin-bottom: .3rem; max-width: 62ch; }
  svg { width: 100%; max-width: 660px; height: auto; display: block; }
  text { font: 600 9px ui-monospace, SFMono-Regular, Menlo, monospace;
         paint-order: stroke; stroke: var(--bg); stroke-width: 3.5px; stroke-linejoin: round; }
  .n rect { fill: var(--panel); stroke: var(--line); }
  .n:hover rect { stroke: var(--accent); }
  .n { cursor: pointer; }
  .lbl { fill: var(--ink); stroke: var(--panel); }
</style>
