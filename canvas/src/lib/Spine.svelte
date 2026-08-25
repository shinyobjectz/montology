<script>
  import { KIND } from './util.js';
  // The navigation spine. A vocabulary is a list before it is a picture, and
  // this is how you find the word you meant — the canvas answers what is
  // AROUND it once you have.
  let { graph, selected, onpick } = $props();
  let q = $state('');
  let kinds = $state(new Set(['word', 'term', 'ruling', 'candidate']));

  const groups = $derived.by(() => {
    const hit = (n) => {
      if (!kinds.has(n.kind)) return false;
      if (!q.trim()) return true;
      const s = q.toLowerCase();
      return n.label.toLowerCase().includes(s)
        || (n.data?.definition ?? '').toLowerCase().includes(s);
    };
    const words = graph.nodes.filter((n) => n.kind === 'word' && hit(n));
    const known = new Set(graph.nodes.filter((n) => n.kind === 'word').map((n) => n.label));
    const by = new Map();
    for (const w of words) {
      const key = w.data.owner && known.has(w.data.owner) ? w.data.owner : '·';
      if (!by.has(key)) by.set(key, []);
      by.get(key).push(w);
    }
    const out = [...by.entries()]
      .map(([k, v]) => [k, v.sort((a, b) => a.label.localeCompare(b.label))])
      .sort((a, b) => (a[0] === '·' ? -1 : b[0] === '·' ? 1 : a[0].localeCompare(b[0])));
    for (const k of ['term', 'ruling', 'candidate', 'surface', 'doctrine', 'token']) {
      const rest = graph.nodes.filter((n) => n.kind === k && hit(n));
      if (rest.length) out.push([KIND[k].name + 's', rest.sort((a, b) => a.label.localeCompare(b.label))]);
    }
    return out;
  });

  function toggle(k) {
    const next = new Set(kinds);
    next.has(k) ? next.delete(k) : next.add(k);
    kinds = next;
  }
</script>

<input class="find mono" bind:value={q} placeholder="find a word…" spellcheck="false" />
<div class="filters">
  {#each Object.entries(KIND) as [k, v]}
    <button class:on={kinds.has(k)} style="--c:{v.color}" onclick={() => toggle(k)}>{v.glyph} {v.name}</button>
  {/each}
</div>
<nav>
  {#each groups as [head, items]}
    <p class="head mono">{head}</p>
    {#each items as n}
      <button class="row mono" class:sel={selected?.id === n.id}
              style="--c:{(KIND[n.kind] ?? KIND.word).color}" onclick={() => onpick(n)}>
        {n.label}
        {#if n.data?.collides}<span class="bad">{n.data.collides}</span>{/if}
      </button>
    {/each}
  {/each}
  {#if !groups.length}<p class="none">nothing matches</p>{/if}
</nav>

<style>
  .find { width: 100%; padding: .35rem .5rem; font-size: .76rem; border-radius: 5px;
          border: 1px solid var(--line); background: var(--bg); color: var(--ink); }
  .filters { display: flex; flex-wrap: wrap; gap: .22rem; margin: .5rem 0 .7rem; }
  .filters button { font-size: .6rem; padding: .1rem .3rem; border-radius: 4px; cursor: pointer;
                    border: 1px solid var(--line); background: none; color: var(--dim); }
  .filters button.on { color: var(--c); border-color: var(--c); }
  nav { overflow-y: auto; flex: 1; margin: 0 -.2rem; }
  .head { font-size: .6rem; text-transform: uppercase; letter-spacing: .07em;
          color: var(--dim); margin: .7rem .2rem .2rem; }
  .row { display: flex; justify-content: space-between; gap: .4rem; width: 100%;
         text-align: left; font-size: .74rem; padding: .16rem .35rem; border-radius: 4px;
         border: 0; border-left: 2px solid var(--c); background: none; color: var(--ink); cursor: pointer; }
  .row:hover { background: var(--line); }
  .row.sel { background: var(--line); font-weight: 600; }
  .bad { color: var(--term); font-size: .62rem; }
  .none { font-size: .72rem; color: var(--dim); }
</style>
