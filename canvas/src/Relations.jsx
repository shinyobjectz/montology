import { useMemo } from 'react';
import { verbColor } from './lib.js';

/** The one figure, laid out as the sentences it encodes.
 *
 *  Rings put a hub in the middle and every edge crossed the centre, so nothing
 *  could be followed. But every relation here IS a sentence — subject, verb,
 *  object — so the graph is layered LEFT TO RIGHT: a thing that only acts sits
 *  on the left, a thing only acted on sits on the right, and an edge never
 *  doubles back. Following one is then just reading.
 *
 *  Deterministic throughout — layers by longest path, order within a layer by
 *  barycentre. A picture that moves when nothing moved cannot be trusted.
 */
const NODE_W = 116;
const NODE_H = 26;
const ROW = 42;
const COL = 268;

function layout(rel, ids) {
  const outs = new Map();
  const ins = new Map();
  for (const id of ids) { outs.set(id, []); ins.set(id, []); }
  for (const e of rel) {
    if (!outs.has(e.source) || !ins.has(e.target)) continue;
    outs.get(e.source).push(e.target);
    ins.get(e.target).push(e.source);
  }

  // Layer = longest path from a source. Cycles are broken by the visit guard
  // rather than by refusing to draw: a vocabulary may contain one.
  const layer = new Map(ids.map((id) => [id, 0]));
  const order = [...ids].sort((a, b) => ins.get(a).length - ins.get(b).length);
  for (let pass = 0; pass < ids.length; pass++) {
    let moved = false;
    for (const id of order) {
      for (const t of outs.get(id)) {
        if (layer.get(t) < layer.get(id) + 1) { layer.set(t, layer.get(id) + 1); moved = true; }
      }
    }
    if (!moved) break;
  }

  const cols = new Map();
  for (const id of ids) {
    const l = layer.get(id);
    if (!cols.has(l)) cols.set(l, []);
    cols.get(l).push(id);
  }
  const keys = [...cols.keys()].sort((a, b) => a - b);

  // Barycentre ordering: a node sits opposite the average of its neighbours,
  // which is the cheap half of crossing reduction and enough at this size.
  const row = new Map();
  for (const k of keys) cols.get(k).forEach((id, i) => row.set(id, i));
  for (let sweep = 0; sweep < 4; sweep++) {
    const forward = sweep % 2 === 0;
    for (const k of forward ? keys : [...keys].reverse()) {
      const near = (id) => (forward ? ins.get(id) : outs.get(id));
      cols.get(k).sort((a, b) => {
        const mean = (id) => {
          const n = near(id);
          return n.length ? n.reduce((s, x) => s + (row.get(x) ?? 0), 0) / n.length : row.get(id) ?? 0;
        };
        return mean(a) - mean(b);
      });
      cols.get(k).forEach((id, i) => row.set(id, i));
    }
  }

  const pos = new Map();
  let height = 0;
  for (const k of keys) {
    const here = cols.get(k);
    const top = -((here.length - 1) * ROW) / 2;
    here.forEach((id, i) => pos.set(id, { x: k * COL, y: top + i * ROW }));
    height = Math.max(height, here.length * ROW);
  }
  return { pos, width: (keys.length - 1) * COL, height };
}

export default function Relations({ g, onPick }) {
  const rel = useMemo(
    () => g.edges.filter((e) => e.kind === 'relation' || e.kind === 'act'), [g]);

  const view = useMemo(() => {
    const ids = [...new Set(rel.flatMap((e) => [e.source, e.target]))]
      .filter((id) => g.byId.has(id));
    const { pos, width, height } = layout(rel, ids);

    // Parallel relations between one pair fan apart, and every label is pushed
    // clear of any it would sit on — a label you cannot read is an edge you
    // cannot follow.
    const seen = new Map();
    const slot = new Map();     // how many labels this subject has placed
    const drawn = [];
    const taken = [];
    for (const e of rel) {
      const a = pos.get(e.source);
      const b = pos.get(e.target);
      if (!a || !b) continue;
      const key = `${e.source}|${e.target}`;
      const n = seen.get(key) ?? 0;
      seen.set(key, n + 1);
      const lift = (n - 0.5 * ((rel.filter((x) => `${x.source}|${x.target}` === key).length) - 1)) * 15;

      const x1 = a.x + NODE_W / 2;
      const x2 = b.x - NODE_W / 2;
      const back = x2 < x1;                       // same layer, or a cycle
      const cx = (x1 + x2) / 2;
      const d = back
        ? `M${x1},${a.y} C${x1 + 70},${a.y + 46 + lift} ${x2 - 70},${b.y + 46 + lift} ${x2},${b.y}`
        : `M${x1},${a.y} C${cx},${a.y + lift} ${cx},${b.y + lift} ${x2},${b.y}`;

      // Every label at the curve's midpoint put twelve of them in one narrow
      // band. Each now rides its OWN curve at its own fraction, so they spread
      // along the span instead of stacking — and a label beside the line it
      // belongs to is a label you can attribute without counting.
      const spread = (slot.get(`${e.source}`) ?? 0);
      slot.set(`${e.source}`, spread + 1);
      const tt = 0.3 + ((spread * 0.17) % 0.42);
      const P = [{ x: x1, y: a.y }, { x: cx, y: a.y + lift },
                 { x: cx, y: b.y + lift }, { x: x2, y: b.y }];
      const u = 1 - tt;
      let lx = u * u * u * P[0].x + 3 * u * u * tt * P[1].x
             + 3 * u * tt * tt * P[2].x + tt * tt * tt * P[3].x;
      let ly = u * u * u * P[0].y + 3 * u * u * tt * P[1].y
             + 3 * u * tt * tt * P[2].y + tt * tt * tt * P[3].y - 6;
      if (back) { lx = cx; ly = (a.y + b.y) / 2 + 40 + lift; }
      // A verb mined from code can be `predictionfromfeatures_error_`, which
      // is wider than the gap between two layers and ran off the frame. Shown
      // short, with the whole of it on hover — the label has to fit the picture
      // or it stops being one.
      const full = e.data.verb;
      const short = full.length > 17 ? `${full.slice(0, 16)}…` : full;
      const w = short.length * 6;
      for (let guard = 0; guard < 40; guard++) {
        const clash = taken.find((t) => Math.abs(t.x - lx) * 2 < t.w + w + 10
                                     && Math.abs(t.y - ly) < 12);
        if (!clash) break;
        ly = clash.y + 12;
      }
      taken.push({ x: lx, y: ly, w });
      drawn.push({ e, d, lx, ly, short, full,
                   color: verbColor(full, e.data.defined !== false) });
    }
    return { pos, drawn, width, height, ids };
  }, [rel, g]);

  if (!rel.length) return null;

  // Rendered 1:1. Letting the viewBox scale to the container blew the whole
  // figure up to twice size and took the 10px labels with it — a diagram that
  // resizes its own typography is a diagram you cannot set.
  const padY = 54;
  const w = view.width + NODE_W + 40;
  const h = view.height + padY * 2;
  const vb = `${-NODE_W / 2 - 20} ${-view.height / 2 - padY} ${w} ${h}`;

  return (
    <figure className="relations">
      <figcaption>
        What acts on what — {rel.length} over {view.ids.length} words, read left to right.
        Every other edge this vocabulary holds reads better as a sentence than as a line.
      </figcaption>
      <div className="scroller">
      <svg viewBox={vb} width={w} height={h} role="img" aria-label="what acts on what">
        {view.drawn.map(({ e, d, color }) => (
          <path key={e.id} d={d} fill="none" stroke={color} strokeWidth="1.4"
                opacity=".75" markerEnd={`url(#tip)`} />
        ))}
        <defs>
          <marker id="tip" viewBox="0 0 8 8" refX="7" refY="4"
                  markerWidth="5" markerHeight="5" orient="auto">
            <path d="M0,1 L7,4 L0,7" fill="none" stroke="currentColor" strokeWidth="1.2" />
          </marker>
        </defs>
        {view.drawn.map(({ e, lx, ly, color, short, full }) => (
          <text key={`${e.id}t`} x={lx} y={ly} fill={color} textAnchor="middle">
            {short}<title>{full}</title>
          </text>
        ))}
        {view.ids.map((id) => {
          const p = view.pos.get(id);
          const node = g.byId.get(id);
          if (!p || !node) return null;
          return (
            <g key={id} className="n" onClick={() => onPick(node)}>
              <rect x={p.x - NODE_W / 2} y={p.y - NODE_H / 2}
                    width={NODE_W} height={NODE_H} rx="5" />
              <text className="lbl" x={p.x} y={p.y + 4} textAnchor="middle">{node.label}</text>
            </g>
          );
        })}
      </svg>
      </div>
    </figure>
  );
}
