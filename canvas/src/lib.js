/** Index the graph once so every lookup is a map hit rather than a scan. */
export function index(graph) {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const out = new Map();
  const inn = new Map();
  for (const e of graph.edges) {
    if (!out.has(e.source)) out.set(e.source, []);
    if (!inn.has(e.target)) inn.set(e.target, []);
    out.get(e.source).push(e);
    inn.get(e.target).push(e);
  }
  const words = graph.nodes.filter((n) => n.kind === 'word');
  const known = new Set(words.map((w) => w.label));

  // Areas are words that own other words. They are the closest thing a
  // vocabulary has to chapters, and qubie's twelve are its architecture.
  const kids = new Map();
  for (const w of words) {
    const o = w.data.owner;
    if (!o || !known.has(o)) continue;
    if (!kids.has(o)) kids.set(o, []);
    kids.get(o).push(w);
  }
  const byLabel = (a, b) => a.label.localeCompare(b.label);
  const areas = words
    .filter((w) => kids.has(w.label))
    .sort((a, b) => kids.get(b.label).length - kids.get(a.label).length)
    .map((lead) => ({ lead, words: kids.get(lead.label).sort(byLabel) }));
  const held = new Set(areas.flatMap((a) => [a.lead.label, ...a.words.map((w) => w.label)]));
  const loose = words.filter((w) => !held.has(w.label)).sort(byLabel);

  return { ...graph, byId, out, inn, words, areas, loose };
}

/** Everything said about one word, gathered — because a reader should never
 *  have to hunt across a page to learn what was decided. */
export function about(node, g) {
  const o = { was: [], instead: [], ruled: [], does: [], doneBy: [], holds: [],
              inside: null, genus: [], answers: [] };
  for (const e of g.inn.get(node.id) ?? []) {
    const other = g.byId.get(e.source);
    if (!other) continue;
    if (e.kind === 'renamed') o.was.push({ other, e });
    else if (e.kind === 'overloaded' || e.kind === 'routes') o.instead.push({ other, e });
    else if (e.kind === 'rules') o.ruled.push(other);
    else if (e.kind === 'relation' || e.kind === 'act') o.doneBy.push({ other, e });
    else if (e.kind === 'contains') o.inside = other;
    else if (e.kind === 'answers') o.answers.push(other);
  }
  for (const e of g.out.get(node.id) ?? []) {
    const other = g.byId.get(e.target);
    if (!other) continue;
    if (e.kind === 'contains') o.holds.push(other);
    else if (e.kind === 'relation' || e.kind === 'act') o.does.push({ other, e });
    else if (e.kind === 'genus') o.genus.push(other);
  }
  return o;
}

/** A colour per verb, so one relation can be followed by eye. The hue means
 *  "this verb" and nothing more; the saturation carries whether it is a word. */
export function verbColor(verb, defined) {
  let h = 0;
  const v = (verb || '').toLowerCase();
  for (let i = 0; i < v.length; i++) h = (h * 31 + v.charCodeAt(i)) % 360;
  const dark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  return `hsl(${20 + (h % 320)} ${defined ? 72 : 42}% ${dark ? (defined ? 70 : 58) : (defined ? 38 : 48)}%)`;
}

export const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
