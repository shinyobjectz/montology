<script>
  import { untrack } from 'svelte';
  // Pan and zoom, by hand. Sixty lines instead of a library, which is the whole
  // reason the flow library came out: at 169 nodes the viewport was the only
  // part of it we were still using.
  let { children, resetKey = 0, bounds = null } = $props();

  // A vocabulary of a hundred words fits the screen at about 13%, which is a
  // smear. So the range runs from "the whole thing at a glance" to "read the
  // definition on the node" — 8x, not the 2.4x a diagram tool needs.
  const MIN_K = 0.06;
  const MAX_K = 8;

  let box = $state(null);
  let t = $state({ x: 0, y: 0, k: 1 });
  let dragging = $state(false);
  let from = { x: 0, y: 0, tx: 0, ty: 0 };

  // Re-centre when the thing being looked at CHANGES — a focused canvas that
  // keeps the old viewport shows you the last question's answer.
  //
  // `bounds` is read untracked on purpose. It is a derived object, so it gets a
  // new identity on any re-render, and reading it as a dependency made every
  // unrelated update re-fit the view: you would zoom in, something upstream
  // would recompute, and the canvas would snap back. The thing being looked at
  // is `resetKey`, and it is the only reason to move the viewport.
  $effect(() => {
    resetKey;
    const b = untrack(() => bounds);
    if (!box) return;
    const r = box.getBoundingClientRect();
    if (!b) { t = { x: r.width / 2, y: r.height / 2, k: 1 }; return; }
    const pad = 130;                       // room for the node boxes themselves
    const w = b.maxX - b.minX + pad * 2, h = b.maxY - b.minY + pad * 2;
    const k = Math.max(MIN_K, Math.min(1, r.width / w, r.height / h));
    t = { k, x: r.width / 2 - ((b.minX + b.maxX) / 2) * k,
             y: r.height / 2 - ((b.minY + b.maxY) / 2) * k };
  });

  function wheel(e) {
    e.preventDefault();
    const r = box.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    const k = Math.min(MAX_K, Math.max(MIN_K, t.k * Math.exp(-e.deltaY * 0.0022)));
    // zoom at the cursor: the point under the pointer must not move
    t = { k, x: mx - ((mx - t.x) * k) / t.k, y: my - ((my - t.y) * k) / t.k };
  }
  function down(e) {
    if (e.target.closest('.node')) return;      // dragging a node is not panning
    dragging = true;
    from = { x: e.clientX, y: e.clientY, tx: t.x, ty: t.y };
    box.setPointerCapture(e.pointerId);
  }
  function move(e) {
    if (!dragging) return;
    t = { ...t, x: from.tx + (e.clientX - from.x), y: from.ty + (e.clientY - from.y) };
  }
  const up = () => { dragging = false; };

  function zoomBy(factor, at) {
    const r = box.getBoundingClientRect();
    const mx = at ? at.x - r.left : r.width / 2;
    const my = at ? at.y - r.top : r.height / 2;
    const k = Math.min(MAX_K, Math.max(MIN_K, t.k * factor));
    t = { k, x: mx - ((mx - t.x) * k) / t.k, y: my - ((my - t.y) * k) / t.k };
  }
  const dbl = (e) => { if (!e.target.closest('.node')) zoomBy(1.9, { x: e.clientX, y: e.clientY }); };
  function key(e) {
    if (e.target !== box) return;
    if (e.key === '+' || e.key === '=') zoomBy(1.3);
    else if (e.key === '-' || e.key === '_') zoomBy(1 / 1.3);
    else if (e.key === '0') resetKey = resetKey;      // handled by the fit effect
  }
</script>

<div
  class="viewport" class:dragging bind:this={box}
  role="application" aria-label="the ontology, as a graph"
  onwheel={wheel} onpointerdown={down} onpointermove={move}
  onpointerup={up} onpointercancel={up} ondblclick={dbl}
  onkeydown={key} tabindex="0"
>
  <div class="world" style="transform: translate({t.x}px,{t.y}px) scale({t.k})">
    {@render children()}
  </div>
  <div class="zoom mono">
    <button onclick={() => zoomBy(1 / 1.4)} aria-label="zoom out">−</button>
    <span>{Math.round(t.k * 100)}%</span>
    <button onclick={() => zoomBy(1.4)} aria-label="zoom in">+</button>
  </div>
</div>

<style>
  .viewport {
    position: relative; overflow: hidden; height: 100%; width: 100%;
    cursor: grab; touch-action: none;
    background-image: radial-gradient(var(--line) 1px, transparent 1px);
    background-size: 22px 22px;
  }
  .viewport.dragging { cursor: grabbing; }
  .world { position: absolute; inset: 0; transform-origin: 0 0; }
  .zoom {
    position: absolute; right: .6rem; bottom: .6rem; font-size: .68rem;
    color: var(--dim); background: var(--panel); border: 1px solid var(--line);
    border-radius: 4px; padding: .1rem .2rem; display: flex; align-items: center; gap: .1rem;
  }
  .zoom span { min-width: 40px; text-align: center; }
  .zoom button { background: none; border: 0; color: var(--dim); cursor: pointer;
                 font: inherit; padding: 0 .3rem; line-height: 1.4; }
  .zoom button:hover { color: var(--ink); }
  .viewport:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
</style>
