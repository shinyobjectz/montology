<script>
  import { KIND } from './util.js';

  let { node, focused = false, selected = false, onpick } = $props();
  const look = $derived(KIND[node.kind] ?? KIND.word);
  const d = $derived(node.data ?? {});

  // A word's relationship to the code is three different facts and they must
  // not be summed: `collides` is code wrongly wearing the name, `excepted` is
  // code deliberately wearing it with a recorded reason. One number would say
  // neither.
  const marks = $derived([
    d.collides ? { t: `${d.collides} collide`, tone: 'bad' } : null,
    d.excepted ? { t: `${d.excepted} excepted`, tone: 'ok' } : null,
    d.count ? { t: `${d.count}×`, tone: 'dim' } : null,
    d.suggested ? { t: 'suggested', tone: 'dim' } : null,
  ].filter(Boolean));
</script>

<button
  class="node {node.kind}" class:focused class:selected
  class:proposed={d.proposed} class:rejected={d.verdict === 'rejected'}
  class:approved={d.verdict === 'approved'}
  style="--c:{look.color}"
  onclick={() => onpick?.(node)}
  title={d.definition ?? d.why ?? d.body ?? node.label}
>
  <span class="glyph mono" aria-hidden="true">{look.glyph}</span>
  <span class="body">
    <span class="label mono">{node.label}</span>
    {#if d.proposed}
      <span class="prop">proposed · {d.verdict ?? 'undecided'}</span>
    {/if}
    {#if d.word_kind}<span class="sub">{d.word_kind}{d.pos ? ` · ${d.pos}` : ''}</span>{/if}
    {#if node.kind === 'ruling'}<span class="sub">{d.ruling_kind}</span>{/if}
    {#if node.kind === 'surface'}<span class="sub">{d.surface_kind}</span>{/if}
    {#if node.kind === 'token'}<span class="sub mono">{d.value}</span>{/if}
    {#if marks.length}
      <span class="marks">
        {#each marks as m}<span class="mark {m.tone}">{m.t}</span>{/each}
      </span>
    {/if}
  </span>
</button>

<style>
  .node {
    position: absolute; transform: translate(-50%, -50%);
    display: flex; gap: .5rem; align-items: flex-start; text-align: left;
    background: var(--panel); color: var(--ink);
    border: 1px solid var(--line); border-left: 3px solid var(--c);
    border-radius: 7px; padding: .45rem .6rem; min-width: 124px; max-width: 240px;
    font: inherit; cursor: pointer; box-shadow: 0 1px 2px rgb(0 0 0 / .06);
  }
  .node:hover { border-color: var(--c); }
  .node.selected { outline: 2px solid var(--c); outline-offset: 1px; }
  .node.focused { box-shadow: 0 3px 14px rgb(0 0 0 / .18); border-color: var(--c); }
  .node.focused .label { font-size: .95rem; }
  .glyph { color: var(--c); font-size: .8rem; line-height: 1.35; }
  .body { display: flex; flex-direction: column; gap: .1rem; min-width: 0; }
  .label { font-size: .82rem; font-weight: 600; overflow-wrap: break-word; hyphens: auto; }
  .sub { font-size: .66rem; color: var(--dim); }
  .marks { display: flex; gap: .3rem; flex-wrap: wrap; margin-top: .15rem; }
  .mark { font-size: .6rem; padding: 0 .3rem; border-radius: 3px; border: 1px solid var(--line); color: var(--dim); }
  .mark.bad { color: var(--term); border-color: color-mix(in oklab, var(--term) 40%, transparent); }
  /* not there yet, and never mistakable for something that is */
  .node.proposed { border-style: dashed; background: transparent; }
  .node.proposed .label { opacity: .85; }
  .node.approved { border-left-color: var(--surface); }
  .node.rejected { opacity: .45; text-decoration: line-through; }
  .prop { font-size: .58rem; color: var(--accent); text-transform: uppercase; letter-spacing: .04em; }
  .mark.ok { color: var(--surface); border-color: color-mix(in oklab, var(--surface) 40%, transparent); }
</style>
