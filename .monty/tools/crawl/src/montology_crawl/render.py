"""Rendering: TSX deliverables → shippable artifacts (HTML, PNG).

THE SPLIT: node (invoked, never vendored) turns the component into HTML —
esbuild bundles the TSX with react, react-dom/server renders static markup.
Then the Chromium that crawl4ai ALREADY installed turns HTML into pixels at
the exact frame the filename declares. No puppeteer, no second browser, no
Remotion required for statics. (Video renders stay with the remotion-ads
skill — that is Remotion's own toolchain, invoked on the consumer's side.)

The harness is ENGINE PLUMBING and lives at `.monty/design/` — one npm
install for every brand (a node_modules per brand is the sidecar we
already deleted once). `@brand` binds to `brands/<name>/design/` at render
time. Absent node answers with the repair.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .brand import brands_dir

from montology_core import workspace_root as _workspace_root

# Tests pin design_dir() directly; when None it resolves lazily.
DESIGN_DIR: Path | None = None


def design_dir() -> Path:
    if DESIGN_DIR is not None:
        return DESIGN_DIR
    return _workspace_root() / ".monty" / "design"

_NO_NODE = ("node is not installed. Repair: install Node.js (nodejs.org or "
            "`brew install node`), then rerun `monty brand render-setup <brand>`.")

RENDER_MJS = r'''// GENERATED render harness — monty brand render-setup
// TSX -> static HTML: esbuild bundles the component with react; the
// exported component (first capitalized export) renders with the props
// JSON passed as argv[3]. Fixed-frame screenshots happen on the Python
// side with the crawler's own Chromium.
import * as esbuild from "esbuild";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [, , entry, propsJson, outFile, brandDir] = process.argv;
const props = JSON.parse(propsJson || "{}");

const result = await esbuild.build({
  entryPoints: [entry],
  bundle: true,
  format: "esm",
  platform: "node",
  // the entry lives OUTSIDE this harness (brands/<brand>/deliverables/), so
  // react must resolve from the harness's own node_modules explicitly
  nodePaths: [join(process.cwd(), "node_modules")],
  // THE BRAND BINDING: design mediums import "@brand/tokens" abstractly;
  // the render binds the alias to the current project's folder.
  alias: brandDir ? { "@brand": brandDir } : {},
  jsx: "automatic",
  write: false,
  external: [],
  loader: { ".ts": "tsx", ".tsx": "tsx" },
  absWorkingDir: process.cwd(),
});
const dir = mkdtempSync(join(tmpdir(), "montology-render-"));
const bundled = join(dir, "component.mjs");
writeFileSync(bundled, result.outputFiles[0].contents);

const mod = await import(pathToFileURL(bundled).href);
const name = Object.keys(mod).find((k) => /^[A-Z]/.test(k) && typeof mod[k] === "function");
if (!name) {
  console.error("no exported component found in " + entry);
  process.exit(1);
}
const { createElement } = await import("react");
const { renderToStaticMarkup } = await import("react-dom/server");
const markup = renderToStaticMarkup(createElement(mod[name], props));
const html = `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;padding:0}</style>${markup}`;
writeFileSync(outFile, html);
console.log(`rendered ${name} -> ${outFile} (${html.length} bytes)`);
'''

PACKAGE_JSON = {
    "name": "montology-design",
    "private": True,
    "type": "module",
    "dependencies": {"react": "^19", "react-dom": "^19", "esbuild": "^0.24"},
}


def render_setup(brand: str = "") -> str:
    """ONE shared harness at .monty/design/ — npm install once, every brand."""
    if shutil.which("node") is None or shutil.which("npm") is None:
        return _NO_NODE
    design_dir().mkdir(parents=True, exist_ok=True)
    pkg = design_dir() / "package.json"
    if not pkg.exists():
        pkg.write_text(json.dumps(PACKAGE_JSON, indent=1))
    (design_dir() / "render.mjs").write_text(RENDER_MJS)
    r = subprocess.run(["npm", "install", "--no-fund", "--no-audit"],
                       cwd=design_dir(), capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        return f"npm install failed: {r.stderr[-300:]}"
    return "render harness ready at .monty/design/ (react, react-dom, esbuild — shared by every brand)"


def render(brand: str, component_file: str, props_json: str = "{}",
           scale: int = 2) -> str:
    """component → out/<name>.html, and for fixed-frame files → out/<name>.png
    at the declared WxH (retina by default: scale=2)."""
    root = brands_dir() / brand
    rd = design_dir()
    if not (rd / "node_modules").exists():
        got = render_setup()
        if not got.startswith("render harness"):
            return got
    src = root / component_file
    if not src.exists():
        return f"no such component: brands/{brand}/{component_file}"
    out_dir = root / "design" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_html = out_dir / (src.stem + ".html")

    r = subprocess.run(
        ["node", str(rd / "render.mjs"), str(src.resolve()), props_json,
         str(out_html.resolve()), str((root / "design").resolve())],
        cwd=rd, capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        return f"render failed: {(r.stderr or r.stdout)[-400:]}"
    report = [r.stdout.strip()]

    # CAPTURED components carry the site's classNames; faithfulness needs
    # the site's own CSS. The manifest recorded the stylesheet URLs at
    # audit time — inject them for the preview (evidence tier only; built
    # components style from tokens and get nothing injected).
    if "captured" in component_file:
        mf = root / "manifest.json"
        sheets = json.loads(mf.read_text()).get("stylesheets", []) if mf.exists() else []
        inline = root / "data" / "site-inline.css"
        head = "".join(f'<link rel="stylesheet" href="{u}">' for u in sheets)
        if inline.exists():
            head += f"<style>{inline.read_text()}</style>"
        # the preview reset: the site's JS (stripped) would have revealed
        # lazy content — previews reveal it with CSS instead
        head += ("<style>img,video{opacity:1!important;visibility:visible!important}"
                 "[data-aos],.lazyload,.lazyloaded{opacity:1!important;transform:none!important}</style>")
        out_html.write_text(out_html.read_text().replace(
            '<meta charset="utf-8">', '<meta charset="utf-8">' + head, 1))
        report.append(f"injected {len(sheets)} stylesheet(s) + inline css (captured tier renders faithfully)")

    # EVERYTHING gets pixels: fixed-frame files at their declared WxH,
    # everything else full-page at desktop width — the book is visual.
    m = re.search(r"-(\d{2,4})x(\d{2,4})$", src.stem)
    out_png = out_dir / (src.stem + ".png")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            if m:
                w, h = int(m.group(1)), int(m.group(2))
                page = browser.new_page(viewport={"width": w, "height": h},
                                        device_scale_factor=scale)
                page.goto(out_html.resolve().as_uri())
                page.screenshot(path=str(out_png),
                                clip={"x": 0, "y": 0, "width": w, "height": h})
                shape = f"{w}x{h} @{scale}x"
            else:
                page = browser.new_page(viewport={"width": 1280, "height": 800},
                                        device_scale_factor=scale)
                page.goto(out_html.resolve().as_uri())
                page.screenshot(path=str(out_png), full_page=True)
                shape = f"full page at 1280 @{scale}x"
            browser.close()
        report.append(f"screenshot {out_png.name} ({shape}, "
                      f"{out_png.stat().st_size // 1024} KB)")
    except Exception as e:  # noqa: BLE001
        report.append(f"screenshot failed ({type(e).__name__}: {e}) — the HTML is still good; "
                      "run `monty crawl setup` if Chromium is missing")
    return "\n".join(report)
