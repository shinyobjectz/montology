<script>
  // One word, as a section of a document — because a word IS a definition, and
  // a definition is a sentence. The graph showed 24 characters of label and
  // none of the 134-character median definition: it hid the payload and drew
  // the metadata. Everything decided about a word sits WITH the word, so a
  // reader never has to hunt across a canvas to find out what was ruled.
  import { verbColor } from './util.js';

  let { node, graph, onpick } = $props();
  const d = $derived(node.data);

  const around = $derived.by(() => {
    const out = { was: [], instead: [], ruled: [], does: [], doneBy: [], owns: [], genus: [], asks: [] };
    for (const e of graph.inn.get(node.id) ?? []) {
      const other = graph.byId.get(e.source);
      if (!other) continue;
      if (e.kind === 'renamed') out.was.push(other.label);
      else if (e.kind === 'overloaded' || e.kind === 'routes') out.instead.push({ term: other.label, e });
      else if (e.kind === 'rules') out.ruled.push(other);
      else if (e.kind === 'relation' || e.kind === 'act') out.doneBy.push({ other, e });
      else if (e.kind === 'contains') out.genus.push({ kind: 'owner', other });
      else if (e.kind === 'answers') out.asks.push(other);
    }
    for (const e of graph.out.get(node.id) ?? []) {
      const other = graph.byId.get(e.target);
      if (!other) continue;
      if (e.kind === 'contains') out.owns.push(other);
      else if (e.kind === 'relation' || e.kind === 'act') out.does.push({ other, e });
      else if (e.kind === 'genus') out.genus.push({ kind: 'genus', other });
    }
    return out;
  });

  const trouble = $derived([
    d.collides ? `${d.collides} declaration${d.collides > 1 ? 's' : ''} wear${d.collides > 1 ? '' : 's'} this name` : null,
    d.verbs_unnamed?.length ? `${d.verbs_unnamed.length} verb${d.verbs_unnamed.length > 1 ? 's' : ''} performed on it that no word names` : null,
  ].filter(Boolean));
</script>

<article id={node.id} class:trouble={trouble.length}>
  <header>
    <h3 class="mono">{node.label}</h3>
    <span class="meta mono">{d.word_kind}{d.pos ? ` · ${d.pos}` : ''}{d.code ? ` · ${d.code}` : ''}</span>
  </header>

  <p class="def">{d.definition}</p>
  {#if d.test}<p class="test"><span>is it one?</span> {d.test}</p>{/if}

  <!-- everything decided about this word, WITH the word -->
  {#if around.was.length || around.instead.length || around.ruled.length}
    <ul class="decided">
      {#each around.was as t}
        <li><b class="was mono">{t}</b> was renamed to this</li>
      {/each}
      {#each around.instead as { term, e }}
        <li>do not say <b class="was mono">{term}</b> — say this
          {#if e.data?.register && e.data.register !== 'all'}<em>in {e.data.register}</em>{/if}
          {#if e.data?.gates === false}<em class="weak">this ruling cannot gate</em>{/if}
        </li>
      {/each}
      {#each around.ruled as r}
        <li>
          {#if r.data.ruling_kind === 'collision'}
            contested with <b>{r.data.theirs}</b> — {r.data.ruling}
          {:else}
            excepted in <code class="mono">{r.data.scope}</code> — {r.data.why}
          {/if}
        </li>
      {/each}
    </ul>
  {/if}

  {#if around.does.length || around.doneBy.length}
    <p class="rels">
      {#each around.does as { other, e }}
        <span class="rel">this <b style="color:{verbColor(e.data.verb, { defined: e.data.defined !== false })}">{e.data.verb}</b>
          <button class="link mono" onclick={() => onpick(other)}>{other.label}</button></span>
      {/each}
      {#each around.doneBy as { other, e }}
        <span class="rel"><button class="link mono" onclick={() => onpick(other)}>{other.label}</button>
          <b style="color:{verbColor(e.data.verb, { defined: e.data.defined !== false })}">{e.data.verb}</b> this</span>
      {/each}
    </p>
  {/if}

  {#if around.owns.length}
    <!-- Svelte trims the whitespace around a separator, so the comma has to be
         a real gap or the list runs together into one word. -->
    <p class="owns">holds
      {#each around.owns as o}<button class="link mono" onclick={() => onpick(o)}>{o.label}</button>{/each}
    </p>
  {/if}
  {#each around.genus as g}
    <p class="owns">{g.kind === 'genus' ? 'is a kind of' : 'lives inside'}
      <button class="link mono" onclick={() => onpick(g.other)}>{g.other.label}</button></p>
  {/each}

  {#if trouble.length}
    <ul class="trouble-list">
      {#each trouble as t}<li>{t}</li>{/each}
      {#if d.at?.length}<li class="mono where">{d.at.slice(0, 3).join('  ')}</li>{/if}
      {#if d.verbs_unnamed?.length}
        <li class="mono where">{d.verbs_unnamed.join('  ')}</li>
      {/if}
    </ul>
  {/if}
</article>

<style>
  article { padding: .85rem 0 .95rem; border-bottom: 1px solid var(--line); scroll-margin-top: 1rem; }
  header { display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap; }
  h3 { font-size: .95rem; margin: 0; font-weight: 700; }
  .meta { font-size: .64rem; color: var(--dim); }
  .def { font-size: .86rem; line-height: 1.55; margin: .3rem 0 .35rem; max-width: 62ch; }
  .test { font-size: .74rem; color: var(--dim); margin: 0 0 .4rem; }
  .test span { text-transform: uppercase; font-size: .58rem; letter-spacing: .06em; }
  .decided { list-style: none; padding: 0; margin: .35rem 0; display: flex; flex-direction: column; gap: .2rem; }
  .decided li { font-size: .75rem; color: var(--ink); line-height: 1.45; max-width: 68ch;
                border-left: 2px solid var(--ruling); padding-left: .5rem; }
  .was { color: var(--term); text-decoration: line-through; }
  em { font-style: normal; color: var(--dim); font-size: .68rem; }
  em.weak { color: var(--candidate); }
  .rels { display: flex; flex-wrap: wrap; gap: .1rem .8rem; margin: .35rem 0; }
  .rel { font-size: .75rem; color: var(--dim); }
  .rel b { font-weight: 600; }
  .owns { font-size: .74rem; color: var(--dim); margin: .2rem 0;
          display: flex; flex-wrap: wrap; gap: .1rem .55rem; align-items: baseline; }
  .link { background: none; border: 0; padding: 0; font: inherit; font-size: .75rem;
          color: var(--accent); cursor: pointer; text-decoration: underline dotted; }
  .trouble-list { list-style: none; padding: .35rem .55rem; margin: .45rem 0 0;
                  border-radius: 5px; background: color-mix(in oklab, var(--candidate) 9%, transparent);
                  border-left: 2px solid var(--candidate); }
  .trouble-list li { font-size: .72rem; color: var(--candidate); line-height: 1.5; }
  .where { color: var(--dim); font-size: .64rem; }
  code { font-size: .7rem; }
</style>
