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
//        what ACTS on it           ←            →   what it ACTS ON, what bears it
//                                        ↓ the words it owns
//                                   ↓ the questions it answers
//
// Left is what comes in, right is what goes out, up is what it is, down is what
// it holds. An act is code-side, like a bearing, so it sits with the outer
// columns rather than in the middle where the vocabulary's own relations are.
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
  const actors = take(ins.filter((e) => e.kind === 'act'), 'in');
  const acted = take(outs.filter((e) => e.kind === 'act'), 'out');
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
  column(actors, -R.far);
  column([...rulings, ...onward], R.ring);
  column([...bears, ...acted], R.far);
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

/** The overview: the whole graph, not just the spine.
 *
 *  This placed ONLY words, so every term, ruling and question went unpositioned
 *  and every edge touching one was filtered out — qubie drew 36 containment
 *  edges out of 93 and read as a tree, because two thirds of the graph was
 *  invisible. A retired name is placed beside the word it points at and a
 *  ruling beside the word it rules, so the relation is short, local and
 *  legible instead of a line across the screen.
 *
 *  Groups pack down a column and wrap to the next, the way a glossary sets on
 *  a page: 110 words in one tall stack fit the screen at 13%, which is a smear.
 */
export function overviewLayout(graph, { columnHeight = 1050, measured } = {}) {
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

  const grouped = tops.filter((t) => (kids.get(t.label) || []).length);
  const flat = tops.filter((t) => !(kids.get(t.label) || []).length);

  const COL_W = NODE_GAP_X + 3 * (240 + NODE_GAP_X);   // satellites · parent · children
  const SAT = 240 + NODE_GAP_X;
  const pos = new Map();
  const shown = new Set();
  let col = 0, y = 0;

  const wrap = (needed) => { if (y + needed > columnHeight && y > 0) { col += 1; y = 0; } };
  const place = (node, x, yy) => { pos.set(node.id, { x, y: yy }); shown.add(node.id); };

  for (const top of grouped) {
    const mine = (kids.get(top.label) || []).sort((a, b) => a.label.localeCompare(b.label));
    const { height } = stack(mine, { x: 0, top: 0, measured });
    wrap(height + 34);
    const x = col * COL_W;
    for (const [n, p] of stack(mine, { x: x + SAT * 2, top: y, measured }).placed) {
      pos.set(n.id, p);
      shown.add(n.id);
    }
    place(top, x + SAT, y + height / 2);
    y += height + 34;
  }

  for (let i = 0; i < flat.length; i += 2) {
    const pair = flat.slice(i, i + 2);
    const h = Math.max(...pair.map((n) => nodeHeight(n, measured)));
    wrap(h + 16);
    const x = col * COL_W;
    pair.forEach((n, j) => place(n, x + SAT + j * SAT, y + h / 2));
    y += h + 16;
  }

  // Now the rest of the graph, hung off whatever it is about. A dead name sits
  // to the LEFT of the word it became, a ruling to the left of the word it
  // rules — the same reading the focused view uses, kept consistent so the two
  // views teach the same thing.
  const anchored = (node) => {
    for (const e of graph.out.get(node.id) ?? []) if (pos.has(e.target)) return pos.get(e.target);
    for (const e of graph.inn.get(node.id) ?? []) if (pos.has(e.source)) return pos.get(e.source);
    return null;
  };
  const taken = new Map();
  for (const node of graph.nodes) {
    if (pos.has(node.id) || node.kind === 'word') continue;
    const at = anchored(node);
    if (!at) continue;                      // nothing to hang it on: leave it out
    const slot = `${Math.round(at.x)}:${Math.round(at.y)}`;
    const nth = taken.get(slot) ?? 0;
    taken.set(slot, nth + 1);
    place(node, at.x - SAT, at.y + nth * (nodeHeight(node, measured) + 10));
  }

  return { pos, shown };
}
