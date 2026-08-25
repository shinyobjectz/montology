// Layout for a FOCUSED neighbourhood, not for the whole graph.
//
// The decision behind this (see mon-gskj): montology's graph is a sparse tree
// with satellites — 169 nodes and 82 edges in qubie, 36 of them containment.
// A node-link diagram of all of it wastes the screen and reads worse than the
// outline it already is. So the canvas answers one question at a time: what is
// around THIS word. Reading outward from the centre —
//
//                                   ↑ owner · what it is a kind of
//        terms that died into it   ←  [ WORD ]  →   rulings taken about it
//                                        ↓ the words it owns   → what bears it
//                                   ↓ the questions it answers
//
// Everything is placed by rule, never by force: a layout that moves when
// nothing moved is a layout you cannot trust to mean anything.
//
// Every stack goes through `stack()`, which advances by each node's OWN height.
// Nothing here may assume nodes are the same size — they are not, and a fixed
// pitch is how long names ended up drawn through their neighbours.

import { NODE_GAP_X, nodeHeight, nodeWidth, stack } from './util.js';

const R = { owner: -190, child: 210, ring: 380, far: 700, asked: 340 };

export function focusLayout(graph, focusId, measured) {
  const { byId, out, inn } = graph;
  const focus = byId.get(focusId);
  if (!focus) return { pos: new Map(), shown: new Set() };

  const pos = new Map([[focusId, { x: 0, y: 0 }]]);
  const seen = new Set([focusId]);
  const take = (edges, dir) => edges
    .map((e) => byId.get(dir === 'out' ? e.target : e.source))
    .filter((n) => n && !seen.has(n.id));

  const outs = out.get(focusId) || [];
  const ins = inn.get(focusId) || [];

  const owner = take(ins.filter((e) => e.kind === 'contains'), 'in');
  const kids = take(outs.filter((e) => e.kind === 'contains'), 'out');
  const dead = take(ins.filter((e) => ['renamed', 'overloaded', 'routes'].includes(e.kind)), 'in');
  const rulings = take(ins.filter((e) => e.kind === 'rules'), 'in');
  const bears = take(outs.filter((e) => e.kind === 'bears'), 'out');
  const onward = take(outs.filter((e) => ['renamed', 'overloaded', 'routes'].includes(e.kind)), 'out');
  const kinds = take(outs.filter((e) => e.kind === 'genus'), 'out');
  const asked = take(ins.filter((e) => e.kind === 'answers'), 'in');

  // centred on the focus, so a column of two and a column of nine both read as
  // belonging to it rather than hanging off it
  const column = (nodes, x) => {
    if (!nodes.length) return;
    const { height } = stack(nodes, { x, top: 0, measured });
    for (const [n, p] of stack(nodes, { x, top: -height / 2, measured }).placed) {
      pos.set(n.id, p);
      seen.add(n.id);
    }
  };
  // a row that advances by each node's OWN width
  const row = (nodes, y) => {
    const total = nodes.reduce((a, n) => a + nodeWidth(n, measured) + NODE_GAP_X, -NODE_GAP_X);
    let x = -total / 2;
    for (const n of nodes) {
      const w = nodeWidth(n, measured);
      pos.set(n.id, { x: x + w / 2, y });
      seen.add(n.id);
      x += w + NODE_GAP_X;
    }
  };

  column(dead, -R.ring);
  column([...rulings, ...onward], R.ring);
  column(bears, R.far);
  row(kids, R.child);
  row(asked, R.asked + (kids.length ? R.child : 0));
  if (owner.length) {
    pos.set(owner[0].id, { x: 0, y: R.owner });
    seen.add(owner[0].id);
  }
  kinds.forEach((n, i) => {
    pos.set(n.id, { x: 300 + i * (nodeWidth(n, measured) + NODE_GAP_X), y: R.owner });
    seen.add(n.id);
  });

  return { pos, shown: seen };
}

/** The overview: every word, containment as the spine.
 *
 *  Flowed into COLUMNS rather than one tall stack. qubie's 110 words in a
 *  single column fit the screen at 13% — a smear, not an overview — because
 *  the layout was tall and the screen is wide. Groups now pack down a column
 *  and wrap to the next, the way a glossary sets on a page. */
export function overviewLayout(graph, { columnHeight = 1000, measured } = {}) {
  const words = graph.nodes.filter((n) => n.kind === 'word');
  const kids = new Map();
  for (const w of words) {
    if (!w.data.owner) continue;
    if (!kids.has(w.data.owner)) kids.set(w.data.owner, []);
    kids.get(w.data.owner).push(w);
  }
  const known = new Set(words.map((w) => w.label));
  const tops = words.filter((w) => !w.data.owner || !known.has(w.data.owner))
                    .sort((a, b) => a.label.localeCompare(b.label));

  // owners with children first: they are the structure, and burying them under
  // sixty ungrouped words is what made the old overview unreadable
  const grouped = tops.filter((t) => (kids.get(t.label) || []).length);
  const flat = tops.filter((t) => !(kids.get(t.label) || []).length);

  const COL_W = NODE_GAP_X + 2 * (240 + NODE_GAP_X);   // parent column + child column
  const pos = new Map();
  const shown = new Set();
  let col = 0, y = 0;

  const wrap = (needed) => { if (y + needed > columnHeight && y > 0) { col += 1; y = 0; } };

  for (const top of grouped) {
    const mine = (kids.get(top.label) || []).sort((a, b) => a.label.localeCompare(b.label));
    const { height } = stack(mine, { x: 0, top: 0, measured });
    wrap(height + 34);
    const x = col * COL_W;
    for (const [n, p] of stack(mine, { x: x + 240 + NODE_GAP_X, top: y, measured }).placed) {
      pos.set(n.id, p);
      shown.add(n.id);
    }
    pos.set(top.id, { x, y: y + height / 2 });
    shown.add(top.id);
    y += height + 34;
  }

  // the ungrouped tail sets two-up, so a long flat vocabulary does not become a
  // mile-long ribbon nobody scrolls. The row advances by the TALLER of the pair.
  for (let i = 0; i < flat.length; i += 2) {
    const pair = flat.slice(i, i + 2);
    const h = Math.max(...pair.map((n) => nodeHeight(n, measured)));
    wrap(h + 16);
    const x = col * COL_W;
    pair.forEach((n, j) => {
      pos.set(n.id, { x: x + j * (240 + NODE_GAP_X), y: y + h / 2 });
      shown.add(n.id);
    });
    y += h + 16;
  }

  return { pos, shown };
}
