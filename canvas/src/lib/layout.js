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

/** The overview, at three depths. The default is the shallowest, on purpose.
 *
 *  Drawing all 192 of qubie's nodes produced a hairball that taught nobody
 *  anything. Laying it out perfectly did not help: 118 nodes at 34% zoom is not
 *  a comprehension aid however tidy it is. The problem was never the layout, it
 *  was answering "show me the ontology" with "here is all of it".
 *
 *  This is montology's own disclosure doctrine, which the words skill follows
 *  and this view did not: the resident surface is a ROUTING TABLE, not the
 *  vocabulary. So —
 *
 *    areas       the words that OWN other words, and what they own. qubie: 12
 *                areas over 45 words, and they are the architecture — engram,
 *                orchestration, inference, core-loop, surface, brain. This is
 *                what someone opening the repo needs first.
 *    core        + the flat words that are in some relation.
 *    everything  + the 35 that connect to nothing.
 *
 *  What each depth leaves out is COUNTED and said in the header. A view that
 *  hides things silently is worse than one that shows too much.
 */
export function overviewLayout(graph, { columnHeight = 1050, measured, mode = 'areas' } = {}) {
  // `graph` mode is the ontology in the sense everyone else means it: nouns,
  // and edges that are verbs. Only words that are IN a relation, so the view is
  // the graph and nothing else.
  if (mode === 'graph') return relationLayout(graph, measured);
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

  // "in a relation" means something other than merely living somewhere:
  // containment is the skeleton and every child has one, so counting it would
  // call the whole vocabulary connected.
  const related = new Set();
  for (const e of graph.edges) {
    if (e.kind === 'contains') continue;
    related.add(e.source);
    related.add(e.target);
  }

  const grouped = tops.filter((t) => (kids.get(t.label) || []).length);
  const allFlat = tops.filter((t) => !(kids.get(t.label) || []).length);
  const flat = mode === 'areas' ? []
    : mode === 'core' ? allFlat.filter((w) => related.has(w.id))
    : allFlat;
  const quiet = allFlat.length - flat.length;

  const COL_W = NODE_GAP_X + 3 * (240 + NODE_GAP_X);
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

  for (const w of flat) {
    const h = nodeHeight(w, measured);
    wrap(h + 16);
    place(w, col * COL_W + SAT, y + h / 2);
    y += h + 16;
  }

  // Satellites hang to the LEFT of what they are about — the same reading the
  // focused view uses. Occupancy is tracked per COLUMN and not per anchor,
  // which is what went wrong before: two anchors at nearby heights each kept
  // their own tidy offset and both wrote into the same strip of screen.
  const anchorOf = (node) => {
    for (const e of graph.out.get(node.id) ?? []) if (pos.has(e.target)) return e.target;
    for (const e of graph.inn.get(node.id) ?? []) if (pos.has(e.source)) return e.source;
    return null;
  };
  // Seeded with everything already placed. Tracking only the satellites was the
  // last bug here: a satellite goes one column left of its anchor, that column
  // can already hold WORDS, and a map that has never heard of them will hand
  // out a slot straight on top of one.
  const columns = new Map();          // x -> [[top, bottom], …] already taken
  for (const [id, at] of pos) {
    const node = graph.byId.get(id);
    const h = nodeHeight(node, measured);
    const taken = columns.get(at.x) ?? [];
    taken.push([at.y - h / 2, at.y + h / 2]);
    columns.set(at.x, taken);
  }
  for (const taken of columns.values()) taken.sort((p, q) => p[0] - q[0]);
  const claim = (x, want, h) => {
    const taken = columns.get(x) ?? [];
    let top = want - h / 2;
    let moved = true;
    while (moved) {
      moved = false;
      for (const [a, b] of taken) {
        if (top < b + 10 && top + h > a - 10) { top = b + 10; moved = true; }
      }
    }
    taken.push([top, top + h]);
    taken.sort((p, q) => p[0] - q[0]);
    columns.set(x, taken);
    return top + h / 2;
  };

  for (const node of graph.nodes) {
    if (pos.has(node.id) || node.kind === 'word') continue;
    const anchor = anchorOf(node);
    if (!anchor) continue;
    const at = pos.get(anchor);
    const x = at.x - SAT;
    place(node, x, claim(x, at.y, nodeHeight(node, measured)));
  }

  return { pos, shown, quiet };
}


/** Nouns, and verbs between them. The view everyone means by "an ontology".
 *
 *  Laid out in rings around the busiest subject rather than in columns: this
 *  graph is a real network — small, but a network — and columns are for trees.
 */
function relationLayout(graph, measured) {
  const rel = graph.edges.filter((e) => e.kind === 'relation' || e.kind === 'act');
  const degree = new Map();
  for (const e of rel) {
    degree.set(e.source, (degree.get(e.source) ?? 0) + 1);
    degree.set(e.target, (degree.get(e.target) ?? 0) + 1);
  }
  const ids = [...degree.keys()].sort((a, b) => degree.get(b) - degree.get(a));
  const pos = new Map();
  const shown = new Set();
  if (!ids.length) return { pos, shown, quiet: 0, empty: true };

  // busiest in the middle, the rest on rings around it — placed by rule, so
  // the same graph draws the same way every time
  const R = [0, 420, 760, 1080];
  let i = 0;
  for (let ring = 0; ring < R.length && i < ids.length; ring++) {
    const room = ring === 0 ? 1 : Math.max(6, Math.floor((2 * Math.PI * R[ring]) / 300));
    const here = ids.slice(i, i + room);
    here.forEach((id, k) => {
      const a = (2 * Math.PI * k) / here.length - Math.PI / 2;
      pos.set(id, ring === 0 ? { x: 0, y: 0 }
                             : { x: Math.round(Math.cos(a) * R[ring]),
                                 y: Math.round(Math.sin(a) * R[ring] * 0.72) });
      shown.add(id);
    });
    i += here.length;
  }
  const words = graph.nodes.filter((n) => n.kind === 'word').length;
  return { pos, shown, quiet: words - shown.size };
}
