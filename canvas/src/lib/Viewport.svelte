<script>
  // Pan and zoom, by hand. Sixty lines instead of a library, which is the whole
  // reason the flow library came out: at 169 nodes the viewport was the only
  // part of it we were still using.
  let { children, resetKey = 0, bounds = null } = $props();

  let box = $state(null);
  let t = $state({ x: 0, y: 0, k: 1 });
  let dragging = $state(false);
  let from = { x: 0, y: 0, tx: 0, ty: 0 };

  // Re-centre when the thing being looked at changes — a focused canvas that
  // keeps the old viewport shows you the last question's answer.
  $effect(() => {
    resetKey;
    const b = bounds;
    if (!box) return;
    const r = box.getBoundingClientRect();
    if (!b) { t = { x: r.width / 2, y: r.height / 2, k: 1 }; return; }
    const pad = 130;                       // room for the node boxes themselves
    const w = b.maxX - b.minX + pad * 2, h = b.maxY - b.minY + pad * 2;
    const k = Math.min(1, r.width / w, r.height / h);
    t = { k, x: r.width / 2 - ((b.minX + b.maxX) / 2) * k,
             y: r.height / 2 - ((b.minY + b.maxY) / 2) * k };
  });

  function wheel(e) {
    e.preventDefault();
    const r = box.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    const k = Math.min(2.4, Math.max(0.25, t.k * Math.exp(-e.deltaY * 0.0016)));
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
</script>

<div
  class="viewport" class:dragging bind:this={box}
  role="application" aria-label="the ontology, as a graph"
  onwheel={wheel} onpointerdown={down} onpointermove={move}
  onpointerup={up} onpointercancel={up}
>
  <div class="world" style="transform: translate({t.x}px,{t.y}px) scale({t.k})">
    {@render children()}
  </div>
  <div class="zoom mono">{Math.round(t.k * 100)}%</div>
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
    border-radius: 4px; padding: .1rem .35rem; pointer-events: none;
  }
</style>
