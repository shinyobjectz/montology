<script>
  import { KIND, EDGE } from './util.js';
  let { node, graph, onpick, onclose } = $props();

  const d = $derived(node?.data ?? {});
  const around = $derived.by(() => {
    if (!node) return [];
    const rows = [];
    for (const e of graph.out.get(node.id) ?? []) rows.push({ e, other: graph.byId.get(e.target), dir: '→' });
    for (const e of graph.inn.get(node.id) ?? []) rows.push({ e, other: graph.byId.get(e.source), dir: '←' });
    return rows.filter((r) => r.other);
  });
</script>

{#if !node}
  <p class="empty">Pick a word to see what it means, what was decided about it,
    and what the code does with its name.</p>
{:else}
  <header>
    <span class="glyph mono" style="color:{(KIND[node.kind] ?? KIND.word).color}">{(KIND[node.kind] ?? KIND.word).glyph}</span>
    <h2 class="mono">{node.label}</h2>
    <button class="x" onclick={() => onclose?.()} aria-label="close">×</button>
  </header>
  <p class="kindline">{(KIND[node.kind] ?? KIND.word).name}{d.word_kind ? ` · ${d.word_kind}` : ''}{d.pos ? ` · ${d.pos}` : ''}</p>

  {#if d.definition}<p class="def">{d.definition}</p>{/if}
  {#if d.test}<p class="test"><span>is it one?</span> {d.test}</p>{/if}
  {#if d.code}<p class="mono code">{d.code}</p>{/if}
  {#if d.body}<p class="def">{d.body}</p>{/if}
  {#if d.ruling}<p class="def">{d.ruling}</p>{/if}
  {#if d.their_meaning}<p class="test"><span>theirs</span> {d.their_meaning}</p>{/if}
  {#if d.why}<p class="test"><span>why</span> {d.why}</p>{/if}
  {#if d.scope}<p class="test"><span>where</span> <code class="mono">{d.scope}</code></p>{/if}
  {#if d.value}<p class="mono code">{d.value}</p>{/if}

  {#if d.collides || d.excepted}
    <h3>In the code</h3>
    <p class="counts">
      {#if d.collides}<span class="bad">{d.collides} declaration(s) wear this name</span>{/if}
      {#if d.excepted}<span class="ok">{d.excepted} excepted</span>{/if}
    </p>
    {#if d.at?.length}
      <ul class="places mono">{#each d.at as at}<li>{at}</li>{/each}</ul>
    {/if}
  {/if}

  {#if d.verbs_unnamed?.length || d.verbs_named?.length}
    <h3>Made to do</h3>
    <p class="verbs">
      {#each d.verbs_named ?? [] as v}<span class="verb named mono">{v}</span>{/each}
      {#each d.verbs_unnamed ?? [] as v}<span class="verb mono">{v}</span>{/each}
    </p>
    {#if d.verbs_unnamed?.length}
      <p class="test">{d.verbs_unnamed.length} of these are not words. A noun the
        code makes do five things, with no word for any of them, is standing in
        for a behaviour nobody has settled.</p>
    {/if}
  {/if}

  {#if around.length}
    <h3>Around it</h3>
    <ul class="around">
      {#each around as r}
        <li>
          <span class="ekind" style="color:{(EDGE[r.e.kind] ?? EDGE.seam).color}">
            {r.e.kind === 'act' ? r.e.data.verb : r.e.kind}</span>
          <span class="dir">{r.dir}</span>
          <button class="mono link" onclick={() => onpick(r.other)}>{r.other.label}</button>
          {#if r.e.data?.gates === false}<span class="toothless">cannot gate</span>{/if}
          {#if r.e.kind === 'act' && r.e.data?.defined === false}<span class="toothless">no word</span>{/if}
        </li>
      {/each}
    </ul>
  {/if}
{/if}

<style>
  header { display: flex; gap: .45rem; align-items: baseline; }
  h2 { font-size: 1rem; margin: 0; overflow-wrap: anywhere; }
  h3 { font-size: .68rem; text-transform: uppercase; letter-spacing: .06em;
       color: var(--dim); margin: 1.1rem 0 .35rem; }
  .kindline { font-size: .68rem; color: var(--dim); margin: .15rem 0 .7rem; }
  .def { font-size: .8rem; line-height: 1.5; margin: 0 0 .55rem; }
  .test { font-size: .72rem; color: var(--dim); margin: 0 0 .4rem; line-height: 1.45; }
  .test span { text-transform: uppercase; letter-spacing: .05em; font-size: .6rem; }
  .code { font-size: .7rem; color: var(--accent); }
  .x { margin-left: auto; background: none; border: 0; color: var(--dim);
       cursor: pointer; font-size: 1rem; line-height: 1; padding: 0 .1rem; }
  .x:hover { color: var(--ink); }
  .counts { display: flex; gap: .5rem; flex-wrap: wrap; font-size: .72rem; margin: 0; }
  .bad { color: var(--term); } .ok { color: var(--surface); }
  .places { list-style: none; padding: 0; margin: .4rem 0 0; font-size: .68rem; color: var(--dim); }
  .verbs { display: flex; flex-wrap: wrap; gap: .25rem; margin: 0 0 .4rem; }
  .verb { font-size: .66rem; padding: .05rem .3rem; border-radius: 3px;
          border: 1px dashed color-mix(in oklab, var(--candidate) 45%, transparent);
          color: var(--candidate); }
  .verb.named { border-style: solid; border-color: color-mix(in oklab, var(--surface) 45%, transparent);
                color: var(--surface); }
  .around { list-style: none; padding: 0; margin: 0; }
  .around li { display: flex; gap: .4rem; align-items: baseline; padding: .16rem 0; font-size: .72rem; }
  .ekind { font-size: .62rem; min-width: 66px; }
  .dir { color: var(--dim); }
  .link { background: none; border: 0; padding: 0; color: var(--ink); cursor: pointer;
          font: inherit; font-size: .74rem; text-decoration: underline dotted; }
  .toothless { font-size: .6rem; color: var(--candidate); }
</style>
