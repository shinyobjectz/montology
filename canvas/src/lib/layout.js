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

const R = { owner: -150, child: 170, ring: 330, far: 620, asked: 330 };
const GAP = 74;

/** Stack n items centred on y=0, in a fixed order, at a fixed pitch. */
function column(items, x, gap = GAP) {
  const start = -((items.length - 1) * gap) / 2;
  return items.map((n, i) => [n, { x, y: start + i * gap }]);
}

export function focusLayout(graph, focusId) {
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

  // the word this one lives inside — above, because containment is read down
  const owner = take(ins.filter((e) => e.kind === 'contains'), 'in');
  // the words it owns — below
  const kids = take(outs.filter((e) => e.kind === 'contains'), 'out');
  // dead names pointing in — left. This is the vocabulary's history.
  const dead = take(ins.filter((e) => ['renamed', 'overloaded', 'routes'].includes(e.kind)), 'in');
  // decisions taken about it — right
  const rulings = take(ins.filter((e) => e.kind === 'rules'), 'in');
  // what implements it, and where the name is redirected onward — far right
  const bears = take(outs.filter((e) => e.kind === 'bears'), 'out');
  const onward = take(outs.filter((e) => ['renamed', 'overloaded', 'routes'].includes(e.kind)), 'out');
  // what it is a kind of — up, beside the owner, because both are "above" it
  // and the whole point of the genus is that it is NOT the owner
  const kinds = take(outs.filter((e) => e.kind === 'genus'), 'out');
  // what motivated it. A word answering no question is the finding here, and
  // an empty space below a word says that better than a count elsewhere.
  const asked = take(ins.filter((e) => e.kind === 'answers'), 'in');

  const place = (items, x, gap) => {
    for (const [n, p] of column(items, x, gap)) { pos.set(n.id, p); seen.add(n.id); }
  };
  place(owner, 0, GAP);
  if (owner.length) pos.set(owner[0].id, { x: 0, y: R.owner });
  place(kids, 0, 0);
  kids.forEach((n, i) => pos.set(n.id, {
    x: -((kids.length - 1) * 190) / 2 + i * 190, y: R.child,
  }));
  kinds.forEach((n, i) => { pos.set(n.id, { x: 250 + i * 210, y: R.owner }); seen.add(n.id); });
  asked.forEach((n, i) => { pos.set(n.id, { x: -260 + i * 300, y: R.asked }); seen.add(n.id); });
  place(dead, -R.ring, 56);
  place([...rulings, ...onward], R.ring, 82);
  place(bears, R.far, 70);

  return { pos, shown: seen };
}

/** The overview: every word, containment as the spine. Used when nothing is
 *  focused yet — the one time showing everything is the right answer, because
 *  "how big is this vocabulary and how is it grouped" is a real question. */
export function overviewLayout(graph) {
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

  const pos = new Map();
  const shown = new Set();
  let y = 0;
  for (const top of tops) {
    const mine = (kids.get(top.label) || []).sort((a, b) => a.label.localeCompare(b.label));
    const start = y;
    mine.forEach((k, i) => { pos.set(k.id, { x: 300, y: start + i * 56 }); shown.add(k.id); });
    pos.set(top.id, { x: 0, y: mine.length ? start + ((mine.length - 1) * 56) / 2 : start });
    shown.add(top.id);
    y = start + Math.max(1, mine.length) * 56 + 18;
  }
  return { pos, shown };
}
