// One place for what each kind looks like, so a legend cannot drift from the
// canvas it explains.

export const KIND = {
  word:      { color: 'var(--word)',      glyph: '●', name: 'word' },
  term:      { color: 'var(--term)',      glyph: '✕', name: 'retired term' },
  ruling:    { color: 'var(--ruling)',    glyph: '§', name: 'ruling' },
  surface:   { color: 'var(--surface)',   glyph: '▣', name: 'surface' },
  candidate: { color: 'var(--candidate)', glyph: '?', name: 'candidate' },
  doctrine:  { color: 'var(--doctrine)',  glyph: '¶', name: 'doctrine' },
  token:     { color: 'var(--token)',     glyph: '◆', name: 'token' },
};

export const EDGE = {
  contains:   { color: 'var(--dim)',       width: 1.5, dash: null,  label: 'owns' },
  genus:      { color: 'var(--word-custom)', width: 2, dash: null,  label: 'is a kind of' },
  renamed:    { color: 'var(--term)',      width: 2,   dash: null,  label: 'renamed to' },
  overloaded: { color: 'var(--candidate)', width: 2,   dash: null,  label: 'say instead' },
  routes:     { color: 'var(--accent)',    width: 2,   dash: null,  label: 'routes to' },
  rules:      { color: 'var(--ruling)',    width: 1.5, dash: '2 4', label: 'rules on' },
  bears:      { color: 'var(--surface)',   width: 2,   dash: null,  label: 'borne by' },
  seam:       { color: 'var(--line)',      width: 1,   dash: null,  label: 'seam' },
};

/** A ruling that cannot be scoped can never gate. Drawing it like one with
 *  teeth is the canvas lying about which decisions are enforced — so a
 *  toothless edge is drawn as one: faint and broken. */
export function edgeLook(edge) {
  const base = EDGE[edge.kind] || EDGE.seam;
  const toothless = edge.data && edge.data.gates === false;
  return {
    color: base.color,
    width: base.width,
    dash: toothless ? '5 5' : base.dash,
    opacity: toothless ? 0.5 : 1,
    label: edge.label || base.label,
  };
}

/** An elbow path. Orthogonal because the graph is a containment tree and a
 *  tree drawn with bezier curves reads as a network, which it is not.
 *
 *  `lane` separates edges that share both endpoints. qubie has a pair —
 *  `intelligence` is both ROUTED and OVERLOADED to `brain` — and drawn on one
 *  line they read as a single ruling, which is the opposite of true: they are
 *  two decisions, and one of them cannot gate. */
export function elbow(a, b, lane = 0) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const off = lane * 13;
  if (Math.abs(dy) < 4) {
    if (!off) return `M${a.x},${a.y} L${b.x},${b.y}`;
    const m = a.x + dx / 2;
    return `M${a.x},${a.y} L${m - 18},${a.y} Q${m},${a.y} ${m},${a.y + off}`
         + ` Q${m},${b.y + off} ${m + 18},${b.y} L${b.x},${b.y}`;
  }
  if (Math.abs(dx) < 4) return `M${a.x},${a.y} L${b.x},${b.y}`;
  const mid = a.x + dx / 2 + off;
  const r = Math.min(14, Math.abs(dx) / 2, Math.abs(dy) / 2);
  const sy = Math.sign(dy), sx = Math.sign(dx);
  return `M${a.x},${a.y} L${mid - r * sx},${a.y} Q${mid},${a.y} ${mid},${a.y + r * sy}`
       + ` L${mid},${b.y - r * sy} Q${mid},${b.y} ${mid + r * sx},${b.y} L${b.x},${b.y}`;
}

export function index(graph) {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const out = new Map(), inn = new Map();
  for (const e of graph.edges) {
    if (!out.has(e.source)) out.set(e.source, []);
    if (!inn.has(e.target)) inn.set(e.target, []);
    out.get(e.source).push(e);
    inn.get(e.target).push(e);
  }
  return { ...graph, byId, out, inn };
}
