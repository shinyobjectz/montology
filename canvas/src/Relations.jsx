import { useEffect, useMemo, useRef, useState } from 'react';
import { verbColor } from './lib.js';

/** The one figure: an inset canvas you can move around in.
 *
 *  Three things it learned the hard way. Curves cannot be followed once more
 *  than two leave the same node, so the routing is ORTHOGONAL with generous
 *  corners — the shape every graph tool settled on, because a right angle tells
 *  you where a line is going and a bezier does not. Each edge gets its OWN
 *  vertical channel in the gap between layers, so two lines never lie on each
 *  other. And the label sits in a real BREAK in the line rather than on top of
 *  it: a halo over a wire still reads as two things fighting.
 *
 *  It is inset rather than page-sized because a diagram that pushes the text
 *  off the screen has stopped being a figure and become a detour.
 */
const NODE_W = 132;
const NODE_H = 30;
const ROW = 52;
const COL = 440;
const R = 14;               // corner radius — large on purpose, this is a map
const BOX_H = 540;          // the inset

function layers(rel, ids) {
  const outs = new Map(ids.map((i) => [i, []]));
  const ins = new Map(ids.map((i) => [i, []]));
  for (const e of rel) {
    if (!outs.has(e.source) || !ins.has(e.target)) continue;
    outs.get(e.source).push(e.target);
    ins.get(e.target).push(e.source);
  }
  const layer = new Map(ids.map((i) => [i, 0]));
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
  const row = new Map();
  for (const k of keys) cols.get(k).forEach((id, i) => row.set(id, i));
  for (let sweep = 0; sweep < 4; sweep++) {
    const fwd = sweep % 2 === 0;
    for (const k of fwd ? keys : [...keys].reverse()) {
      const near = (id) => (fwd ? ins.get(id) : outs.get(id));
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
    height = Math.max(height, (here.length - 1) * ROW + NODE_H);
  }
  return { pos, layer, width: (keys.length - 1) * COL, height };
}

/** Out right, down its own channel, in from the left — with a real BREAK in the
 *  line where the label goes.
 *
 *  The break is put on the vertical run when there is room for it and on the
 *  horizontal run out of the source when there is not. Every edge gets a label
 *  either way: an unlabelled edge in a graph of verbs is a line that says
 *  nothing, and the first version dropped eight of seventeen that way.
 */
function route(a, b, channelX, label) {
  const x1 = a.x + NODE_W / 2;
  const x2 = b.x - NODE_W / 2;
  const dy = b.y - a.y;
  const s = Math.sign(dy) || 1;

  if (Math.abs(dy) < 2) {
    const mid = (x1 + x2) / 2;
    return { parts: [`M${x1},${a.y} L${mid - label.w / 2},${a.y}`,
                     `M${mid + label.w / 2},${b.y} L${x2},${b.y}`],
             at: { x: mid, y: a.y }, along: 'x', range: [x1 + label.w / 2, x2 - label.w / 2] };
  }

  const r = Math.max(4, Math.min(R, Math.abs(dy) / 2, (channelX - x1) / 2, (x2 - channelX) / 2));
  const head = `M${x1},${a.y} L${channelX - r},${a.y} Q${channelX},${a.y} ${channelX},${a.y + r * s}`;
  const tail = `M${channelX},${b.y - r * s} Q${channelX},${b.y} ${channelX + r},${b.y} L${x2},${b.y}`;
  const from = a.y + r * s;
  const to = b.y - r * s;

  // room on the vertical run? put it there — text is horizontal, so a gap in a
  // vertical line reads as cleanly as a guard on a flowchart
  if (Math.abs(to - from) > label.h + 14) {
    const mid = (from + to) / 2;
    return { parts: [`${head} L${channelX},${mid - (label.h / 2) * s}`,
                     `M${channelX},${mid + (label.h / 2) * s} L${channelX},${to}`,
                     tail],
             at: { x: channelX, y: mid }, along: 'y',
             range: [Math.min(from, to) + label.h, Math.max(from, to) - label.h] };
  }
  // otherwise break the run OUT of the source, which is always long enough
  const cut = Math.min(x1 + 26 + label.w / 2, channelX - r - 6);
  return { parts: [`M${x1},${a.y} L${cut - label.w / 2},${a.y}`,
                   `M${cut + label.w / 2},${a.y} L${channelX - r},${a.y} `
                   + `Q${channelX},${a.y} ${channelX},${a.y + r * s} L${channelX},${to}`,
                   tail],
           at: { x: cut, y: a.y }, along: 'x',
           range: [x1 + label.w / 2 + 4, channelX - r - label.w / 2 - 4] };
}

export default function Relations({ g, onPick }) {
  const rel = useMemo(
    () => g.edges.filter((e) => e.kind === 'relation' || e.kind === 'act'), [g]);

  const view = useMemo(() => {
    const ids = [...new Set(rel.flatMap((e) => [e.source, e.target]))].filter((id) => g.byId.has(id));
    const { pos, layer, width, height } = layers(rel, ids);

    // One channel per edge in the gap it crosses, ordered by where it lands, so
    // channels do not cross each other on their way down.
    const gaps = new Map();
    for (const e of rel) {
      if (!pos.has(e.source) || !pos.has(e.target)) continue;
      const k = layer.get(e.source);
      if (!gaps.has(k)) gaps.set(k, []);
      gaps.get(k).push(e);
    }
    const channel = new Map();
    for (const [k, here] of gaps) {
      here.sort((p, q) => (pos.get(p.target).y - pos.get(q.target).y)
                       || (pos.get(p.source).y - pos.get(q.source).y));
      const from = k * COL + NODE_W / 2;
      const to = (k + 1) * COL - NODE_W / 2;
      here.forEach((e, i) => channel.set(e.id, from + ((to - from) * (i + 1)) / (here.length + 1)));
    }

    const drawn = rel.map((e) => {
      const a = pos.get(e.source);
      const b = pos.get(e.target);
      if (!a || !b) return null;
      const full = e.data.verb;
      const short = full.length > 18 ? `${full.slice(0, 17)}…` : full;
      const cx = channel.get(e.id) ?? (a.x + b.x) / 2;
      const { parts, at, along, range } = route(a, b, cx, { w: short.length * 6.4 + 10, h: 17 });
      return { e, parts, at, along, range, short, full,
               color: verbColor(full, e.data.defined !== false) };
    }).filter(Boolean);

    // Two labels that land on each other are two edges nobody can tell apart —
    // and one that lands on a NODE is worse, because it reads as that node's.
    // Both are the same problem, so the nodes go in the same list.
    // Each obstacle carries its own HEIGHT. A flat threshold let a label clear
    // another label and still sit on a node, which is twice as tall.
    const taken = [...pos.values()].map((p) => ({ x: p.x, y: p.y, w: NODE_W + 10, h: NODE_H + 6 }));
    for (const d of drawn) {
      const w = d.short.length * 6.4 + 8;
      const h = 16;
      // Slide the label ALONG its own line, never away from it. Pushing
      // perpendicular cleared the overlap and left a column of verbs floating
      // beside the edges they belonged to — which is worse than touching, since
      // a label you cannot attribute is a label that says nothing.
      const [lo, hi] = d.range ?? [d.at.x, d.at.x];
      const step = (d.along === 'x' ? w : h) * 0.55 + 4;
      const start = d.along === 'x' ? d.at.x : d.at.y;
      const free = (at) => !taken.find((t) => Math.abs(t.x - at.x) * 2 < t.w + w
                                           && Math.abs(t.y - at.y) * 2 < t.h + h);
      const put = (v) => (d.along === 'x' ? { x: v, y: d.at.y } : { x: d.at.x, y: v });
      let placed = null;
      for (let i = 0; i < 26 && !placed; i++) {
        // walk outward from where it wants to be, both ways
        const cand = start + (i % 2 ? -1 : 1) * Math.ceil(i / 2) * step;
        if (cand < lo || cand > hi) continue;
        if (free(put(cand))) placed = put(cand);
      }
      // A run with no free slot on it at all — a short one carrying two long
      // verbs. Then and only then, step off the line: still beside its own
      // edge, and legible, which beats two words printed on each other.
      if (!placed) {
        for (const dy of [h + 2, -(h + 2), 2 * h + 4, -(2 * h + 4)]) {
          const at = { x: d.at.x, y: d.at.y + dy };
          if (free(at)) { placed = at; break; }
        }
      }
      d.at = placed ?? d.at;
      taken.push({ x: d.at.x, y: d.at.y, w, h });
    }

    return { pos, drawn, ids, width, height };
  }, [rel, g]);

  // pan and zoom, inside the inset only
  const box = useRef(null);
  const [t, setT] = useState({ x: 0, y: 0, k: 1 });
  const drag = useRef(null);

  useEffect(() => {
    const el = box.current;
    if (!el || !view.ids.length) return;
    const r = el.getBoundingClientRect();
    const w = view.width + NODE_W + 60;
    const h = view.height + 60;
    const k = Math.min(1.35, r.width / w, r.height / h);
    setT({ k, x: r.width / 2 - (view.width / 2) * k, y: r.height / 2 * 1 });
  }, [view]);

  if (!rel.length) return null;

  const wheel = (ev) => {
    ev.preventDefault();
    const r = box.current.getBoundingClientRect();
    const mx = ev.clientX - r.left;
    const my = ev.clientY - r.top;
    const k = Math.min(3, Math.max(0.3, t.k * Math.exp(-ev.deltaY * 0.002)));
    setT({ k, x: mx - ((mx - t.x) * k) / t.k, y: my - ((my - t.y) * k) / t.k });
  };
  const down = (ev) => {
    if (ev.target.closest('.n')) return;
    drag.current = { x: ev.clientX, y: ev.clientY, tx: t.x, ty: t.y };
    box.current.setPointerCapture(ev.pointerId);
  };
  const move = (ev) => {
    if (!drag.current) return;
    setT((p) => ({ ...p, x: drag.current.tx + (ev.clientX - drag.current.x),
                          y: drag.current.ty + (ev.clientY - drag.current.y) }));
  };
  const up = () => { drag.current = null; };

  return (
    <figure className="relations">
      <figcaption>
        What acts on what — {rel.length} over {view.ids.length} words, read left to right.
        Drag to move, scroll to zoom. Every other edge this vocabulary holds reads
        better as a sentence than as a line.
      </figcaption>
      <div ref={box} className="inset" style={{ height: BOX_H }}
           onWheel={wheel} onPointerDown={down} onPointerMove={move}
           onPointerUp={up} onPointerCancel={up}>
        <svg width="100%" height="100%" role="img" aria-label="what acts on what">
          <g transform={`translate(${t.x},${t.y}) scale(${t.k})`}>
            {view.drawn.map(({ e, parts, color }) => (
              <g key={e.id} style={{ color }}>
                {parts.map((d, i) => (
                  <path key={i} d={d} fill="none" stroke={color} strokeWidth="1.6"
                        strokeLinecap="round"
                        markerEnd={i === parts.length - 1 ? 'url(#tip)' : undefined} />
                ))}
              </g>
            ))}
            <defs>
              <marker id="tip" viewBox="0 0 8 8" refX="7" refY="4"
                      markerWidth="5.5" markerHeight="5.5" orient="auto">
                <path d="M0.5,1 L7,4 L0.5,7" fill="none" stroke="currentColor" strokeWidth="1.4" />
              </marker>
            </defs>
            {view.drawn.map(({ e, at, short, full, color }) => (
              <text key={`${e.id}t`} x={at.x} y={at.y + 4} fill={color} textAnchor="middle">
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
                        width={NODE_W} height={NODE_H} rx="7" />
                  <text className="lbl" x={p.x} y={p.y + 4} textAnchor="middle">{node.label}</text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
    </figure>
  );
}
