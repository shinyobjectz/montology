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
  question:  { color: 'var(--candidate)', glyph: '?', name: 'question' },
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
  const unnamedVerb = edge.kind === 'act' && edge.data && edge.data.defined === false;
  return {
    color: base.color,
    width: base.width,
    dash: toothless || unnamedVerb ? '5 5' : base.dash,
    opacity: toothless ? 0.5 : unnamedVerb ? 0.7 : 1,
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
export const LANE = 24;   // wide enough that five parallel acts read as five

export function elbow(a, b, lane = 0) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const off = lane * LANE;
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


// ── how big a node actually is ──────────────────────────────────────────────
//
// The layouts stacked at a fixed pitch, which is only correct if every node is
// the same height — and they are not. `learning-from-demonstration` wraps to
// four lines and `gap` to one, so a fixed pitch drew long names through their
// neighbours.
//
// Estimating the height from the label was the first attempt and it kept being
// wrong in ways that needed another guess: `deliberative-layer` and
// `guided-walkthrough` are both eighteen characters with one hyphen and render
// 60px and 75px, because CSS breaks at hyphens on its own terms. So the nodes
// are MEASURED once after they mount and the layout re-flows from what they
// actually are. The estimate below is only the first frame, before anything has
// been rendered to measure — and it rounds up, because an over-estimate costs a
// little space and an under-estimate costs a collision.

export const NODE_W = 240;
export const NODE_GAP_X = 34;
const LINE = 17;
const CHROME = 28;
const MIN_H = 45;

function estimate(node) {
  const label = node.label ?? '';
  const perLine = node.kind === 'question' ? 30 : 20;
  // a hyphen is a break opportunity CSS will take, so each one can cost a line
  const lines = Math.max(
    Math.ceil(label.length / perLine),
    Math.min(4, (label.match(/-/g) || []).length + 1),
  );
  const d = node.data ?? {};
  const extra = (d.proposed ? LINE : 0)
    + (d.collides || d.excepted || d.count || d.suggested ? LINE : 0);
  return Math.max(MIN_H, CHROME + lines * LINE + extra);
}

/** The height to lay this node out at: what it measured, else what it should be. */
export function nodeHeight(node, measured) {
  return measured?.[node.id]?.h ?? estimate(node);
}

export function nodeWidth(node, measured) {
  return measured?.[node.id]?.w ?? (node.kind === 'question' ? 330 : NODE_W);
}

/** Stack nodes down a column so no two can touch, whatever their heights. */
export function stack(nodes, { x, top = 0, gap = 16, measured }) {
  const placed = [];
  let y = top;
  for (const n of nodes) {
    const h = nodeHeight(n, measured);
    placed.push([n, { x, y: y + h / 2 }]);   // nodes are centred on their position
    y += h + gap;
  }
  return { placed, height: Math.max(0, y - top - gap) };
}
