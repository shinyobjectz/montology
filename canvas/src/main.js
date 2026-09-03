import './style.css';

function waitForWebvowl(timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    (function poll() {
      if (globalThis.webvowl?.graph) return resolve(globalThis.webvowl);
      if (Date.now() - start > timeoutMs) {
        return reject(new Error('WebVOWL did not load'));
      }
      requestAnimationFrame(poll);
    })();
  });
}

/** WebVOWL expects optional sidebar/loading modules; stub the bits we omit. */
function stubWebvowlChrome(graph) {
  const noop = () => {};
  const opts = graph.options();
  if (!opts.leftSidebar()) {
    opts.leftSidebar({
      isSidebarVisible: () => false,
      getSidebarVisibility: () => 0,
      showSidebar: noop,
      hideCollapseButton: noop,
    });
  }
}

/** Montology is read-only — disable WebVOWL property draggers (editor mode is off by default). */
function disableEditor(graph) {
  if (graph.options().drawPropertyDraggerOnHover) {
    graph.options().drawPropertyDraggerOnHover(false);
  }
}

function revealGraph() {
  const inner = document.querySelector('#graph .vowlGraph > g');
  if (inner) inner.style.opacity = '1';
}

/** Without WebVOWL's progress bar the graph stays hidden and force layout may not tick. */
function settleLayout(graph) {
  revealGraph();
  for (let i = 0; i < 40; i += 1) graph.lazyRefresh();
  try {
    graph.forceRelocationEvent();
  } catch {
    graph.reset();
  }
}

async function boot() {
  const graphEl = document.getElementById('graph');
  const subtitle = document.getElementById('subtitle');
  const errorEl = document.getElementById('error');

  try {
    const webvowl = await waitForWebvowl();

    const res = await fetch('./api/ontology.vowl.json');
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error ?? res.statusText);
    }
    const payload = await res.json();
    subtitle.textContent = payload.header?.title?.undefined
      ?? `${payload.metrics?.classCount ?? 0} concepts`;

    const graph = webvowl.graph('#graph');
    stubWebvowlChrome(graph);
    disableEditor(graph);
    graph.options()
      .width(graphEl.clientWidth || window.innerWidth)
      .height(graphEl.clientHeight || window.innerHeight - 48)
      .data(payload);

    // start() creates the SVG shell; load() parses the ontology into it.
    graph.start();
    graph.load();
    settleLayout(graph);
  } catch (e) {
    errorEl.hidden = false;
    errorEl.textContent = String(e);
    subtitle.textContent = 'could not load the ontology';
    console.error(e);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
