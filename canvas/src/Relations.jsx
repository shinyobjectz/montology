import { useMemo } from 'react';
import { verbColor } from './lib.js';

/** The one figure. Of montology's 283 edges only 17 are a network anyone would
 *  want to SEE — the rest are a containment tree, attachments, or dependency
 *  seams, which are all better read than drawn. So the graph appears once, at
 *  the size the data deserves, and answers exactly one question. */
export default function Relations({ g, onPick }) {
  const rel = useMemo(
    () => g.edges.filter((e) => e.kind === 'relation' || e.kind === 'act'), [g]);

  const { pos, lane, ids } = useMemo(() => {
    const degree = new Map();
    for (const e of rel) {
      degree.set(e.source, (degree.get(e.source) ?? 0) + 1);
      degree.set(e.target, (degree.get(e.target) ?? 0) + 1);
    }
    const ids = [...degree.keys()].sort((a, b) => degree.get(b) - degree.get(a));
    const pos = new Map();
    const R = [0, 148, 258];
    let i = 0;
    for (let ring = 0; ring < R.length && i < ids.length; ring++) {
      const room = ring === 0 ? 1 : Math.max(7, Math.round((2 * Math.PI * R[ring]) / 96));
      const here = ids.slice(i, i + room);
      here.forEach((id, k) => {
        const t = (2 * Math.PI * k) / here.length - Math.PI / 2;
        pos.set(id, ring === 0 ? { x: 0, y: 0 }
          : { x: Math.cos(t) * R[ring], y: Math.sin(t) * R[ring] * 0.8 });
      });
      i += here.length;
    }
    const seen = new Map();
    const lane = new Map();
    for (const e of rel) {
      const k = `${e.source}|${e.target}`;
      lane.set(e.id, seen.get(k) ?? 0);
      seen.set(k, (seen.get(k) ?? 0) + 1);
    }
    for (const e of rel) {
      const k = `${e.source}|${e.target}`;
      lane.set(e.id, lane.get(e.id) - (seen.get(k) - 1) / 2);
    }
    return { pos, lane, ids };
  }, [rel]);

  if (!rel.length) return null;

  const arc = (a, b, n) => {
    const dx = b.x - a.x, dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const bow = len * 0.14 + n * 15;
    const mx = a.x + dx / 2 - (dy / len) * bow;
    const my = a.y + dy / 2 + (dx / len) * bow;
    return { d: `M${a.x},${a.y} Q${mx},${my} ${b.x},${b.y}`,
             at: { x: (a.x + b.x) / 4 + mx / 2 - (dy / len) * 13,
                   y: (a.y + b.y) / 4 + my / 2 + (dx / len) * 13 } };
  };

  return (
    <figure className="relations">
      <figcaption>
        What acts on what — {rel.length} over {ids.length} words. Every other edge
        this vocabulary holds reads better as a sentence than as a line.
      </figcaption>
      <svg viewBox="-320 -250 640 500" role="img" aria-label="what acts on what">
        {rel.map((e) => {
          const a = pos.get(e.source), b = pos.get(e.target);
          if (!a || !b) return null;
          const p = arc(a, b, lane.get(e.id));
          const c = verbColor(e.data.verb, e.data.defined !== false);
          return (
            <g key={e.id}>
              <path d={p.d} fill="none" stroke={c} strokeWidth="1.3" opacity=".9" />
              <text x={p.at.x} y={p.at.y} fill={c} textAnchor="middle">{e.data.verb}</text>
            </g>
          );
        })}
        {ids.map((id) => {
          const p = pos.get(id), node = g.byId.get(id);
          if (!p || !node) return null;
          return (
            <g key={id} className="n" onClick={() => onPick(node)}>
              <rect x={p.x - 45} y={p.y - 10} width="90" height="20" rx="4" />
              <text className="lbl" x={p.x} y={p.y + 4} textAnchor="middle">{node.label}</text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
