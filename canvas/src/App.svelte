<script>
  // ONE view: the ontology as a document you can read top to bottom.
  //
  // Four canvas depths, a focus mode and a hairball came before this, and the
  // audit that ended them is worth keeping written down. Of montology's 283
  // edges only 17 are a network anyone would want to SEE — 186 are seams, 31
  // are a containment tree, 9 are attachments. Definitions run a median of 134
  // characters and a node box shows none of them. And six incomparable kinds
  // were drawn as peer boxes: a ruling is ABOUT a word, a question is ANSWERED
  // BY words, a surface is code and not vocabulary at all.
  //
  // So: a document, with everything decided about a word sitting WITH the word,
  // and a graph kept as one figure at the size the data deserves. This is also
  // what the repo already believes — prose is rendered, never authored — and
  // the words skill has been quietly doing it all along.
  import Word from './lib/Word.svelte';
  import Figure from './lib/Figure.svelte';
  import Spine from './lib/Spine.svelte';
  import Compose from './lib/Compose.svelte';
  import { index } from './lib/util.js';

  let graph = $state(null);
  let error = $state('');
  let selected = $state(null);
  let authoring = $state(false);
  let scroller = $state(null);

  function load() {
    return fetch('./api/graph')
      .then((r) => (r.ok ? r.json() : r.json().then((e) => Promise.reject(e.error ?? r.statusText))))
      .then((g) => { graph = index(g); })
      .catch((e) => { error = String(e); });
  }
  $effect(() => { load(); });

  // The document's ORDER, which is the thing a graph could never have: areas
  // first with what they hold, then the words that belong to no area.
  const chapters = $derived.by(() => {
    if (!graph) return [];
    const words = graph.nodes.filter((n) => n.kind === 'word');
    const known = new Set(words.map((w) => w.label));
    const kids = new Map();
    for (const w of words) {
      const o = w.data.owner;
      if (o && known.has(o)) (kids.get(o) ?? kids.set(o, []).get(o)).push(w);
    }
    const areas = words
      .filter((w) => kids.has(w.label))
      .sort((a, b) => kids.get(b.label).length - kids.get(a.label).length);
    const inArea = new Set(areas.flatMap((a) => [a.label, ...kids.get(a.label).map((k) => k.label)]));
    const rest = words.filter((w) => !inArea.has(w.label))
                      .sort((a, b) => a.label.localeCompare(b.label));
    return [
      ...areas.map((a) => ({ title: a.label, lead: a, words: kids.get(a.label).sort((x, y) => x.label.localeCompare(y.label)) })),
      ...(rest.length ? [{ title: 'On their own', lead: null, words: rest }] : []),
    ];
  });

  const findings = $derived.by(() => {
    const s = graph?.stats ?? {};
    const q = graph?.nodes.filter((n) => n.kind === 'question' && n.data.unanswered).length ?? 0;
    return [
      s.collides && { n: s.collides,
        what: `declaration${s.collides > 1 ? 's' : ''} wear${s.collides > 1 ? '' : 's'} a word’s name` },
      s.unnamed_verbs && { n: s.unnamed_verbs,
        what: `verb${s.unnamed_verbs > 1 ? 's' : ''} performed on words that no word names` },
      s.candidates && { n: s.candidates,
        what: `name${s.candidates > 1 ? 's' : ''} the code repeats with no word` },
      q && { n: q, what: `question${q > 1 ? 's' : ''} no word answers` },
    ].filter(Boolean);
  });

  function pick(node) {
    selected = node;
    scroller?.querySelector(`[id="${CSS.escape(node.id)}"]`)
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
</script>

<div class="shell" class:open={authoring}>
  <aside class="rail left">
    <h1 class="mono">montology{#if graph}<span class="ws"> · {graph.workspace}</span>{/if}</h1>
    {#if graph}<Spine {graph} {selected} onpick={pick} />{/if}
  </aside>

  <main bind:this={scroller}>
    {#if error}
      <p class="error mono">{error}</p>
    {:else if !graph}
      <p class="loading mono">reading the ontology…</p>
    {:else}
      <div class="doc">
        <header class="top">
          <h2>{graph.workspace}</h2>
          <p class="lede">
            {graph.stats.words} words{#if graph.stats.relations}, {graph.stats.relations} relations{/if}{#if graph.stats.rulings}, {graph.stats.rulings} rulings{/if}.
            Rendered from <code class="mono">.monty/ontology.db</code> — the database is the truth,
            this is a reading of it.
          </p>
          <button class="author mono" onclick={() => (authoring = !authoring)}>
            {authoring ? 'close' : '+ author'}
          </button>
          {#if findings.length}
            <ul class="findings">
              {#each findings as f}<li><b>{f.n}</b> {f.what}</li>{/each}
            </ul>
          {/if}
        </header>

        <Figure {graph} onpick={pick} />

        {#each chapters as ch}
          <section>
            <h2 class="chapter mono">{ch.title}</h2>
            {#if ch.lead}<Word node={ch.lead} {graph} onpick={pick} />{/if}
            {#each ch.words as w (w.id)}<Word node={w} {graph} onpick={pick} />{/each}
          </section>
        {/each}

        {#each graph.nodes.filter((n) => n.kind === 'doctrine') as d (d.id)}
          <section class="doctrine">
            <h2 class="chapter">{d.label}</h2>
            <p>{d.data.body}</p>
          </section>
        {/each}
      </div>
    {/if}
  </main>

  {#if graph && authoring}
    <aside class="rail right">
      <Compose intents={graph.intents ?? []} token={graph.token} onwrote={load} />
    </aside>
  {/if}
</div>

<style>
  .shell { display: grid; grid-template-columns: 236px 1fr; height: 100%; }
  .shell.open { grid-template-columns: 236px 1fr 316px; }
  .rail { display: flex; flex-direction: column; padding: .7rem .75rem; overflow: hidden;
          background: var(--panel); }
  .rail.left { border-right: 1px solid var(--line); }
  .rail.right { border-left: 1px solid var(--line); overflow-y: auto; }
  h1 { font-size: .82rem; margin: 0 0 .6rem; font-weight: 700; }
  .ws { color: var(--dim); font-weight: 400; }
  main { overflow-y: auto; min-width: 0; }
  .doc { max-width: 860px; margin: 0 auto; padding: 2rem 2.2rem 6rem; }
  .top { position: relative; margin-bottom: 1.6rem; }
  .top h2 { font-size: 1.5rem; margin: 0; letter-spacing: -.02em; }
  .lede { font-size: .82rem; color: var(--dim); line-height: 1.55; margin: .35rem 0 0; max-width: 62ch; }
  .author { position: absolute; top: 0; right: 0; font-size: .7rem; padding: .2rem .5rem;
            cursor: pointer; border-radius: 5px; border: 1px solid var(--line);
            background: none; color: var(--dim); }
  .author:hover { color: var(--accent); border-color: var(--accent); }
  .findings { list-style: none; padding: .5rem .7rem; margin: .9rem 0 0; border-radius: 6px;
              border-left: 2px solid var(--candidate);
              background: color-mix(in oklab, var(--candidate) 8%, transparent); }
  .findings li { font-size: .76rem; color: var(--ink); line-height: 1.6; }
  .findings b { color: var(--candidate); }
  .chapter { font-size: .68rem; text-transform: uppercase; letter-spacing: .1em;
             color: var(--dim); margin: 2rem 0 .2rem; font-weight: 600; }
  section.doctrine p { font-size: .84rem; line-height: 1.6; max-width: 62ch;
                       white-space: pre-wrap; margin: .4rem 0 0; }
  section.doctrine .chapter { text-transform: none; letter-spacing: 0; font-size: .95rem;
                              color: var(--ink); font-weight: 700; }
  .loading, .error { padding: 1.4rem; font-size: .78rem; color: var(--dim); }
  .error { color: var(--term); }
</style>
