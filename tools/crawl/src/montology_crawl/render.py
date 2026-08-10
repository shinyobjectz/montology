"""Rendering: TSX deliverables → shippable artifacts (HTML, PNG).

THE SPLIT: node (invoked, never vendored) turns the component into HTML —
esbuild bundles the TSX with react, react-dom/server renders static markup.
Then the Chromium that crawl4ai ALREADY installed turns HTML into pixels at
the exact frame the filename declares. No puppeteer, no second browser, no
Remotion required for statics. (Video renders stay with the remotion-ads
skill — that is Remotion's own toolchain, invoked on the consumer's side.)

`render_setup` writes a per-brand harness (package.json + render.mjs);
first render runs `npm install` once. Absent node answers with the repair.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .brand import BRANDS_DIR

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

const [, , entry, propsJson, outFile] = process.argv;
const props = JSON.parse(propsJson || "{}");

const result = await esbuild.build({
  entryPoints: [entry],
  bundle: true,
  format: "esm",
  platform: "node",
  // the entry lives OUTSIDE this harness (brands/<brand>/deliverables/), so
  // react must resolve from the harness's own node_modules explicitly
  nodePaths: [join(process.cwd(), "node_modules")],
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
    "name": "montology-render-harness",
    "private": True,
    "type": "module",
    "dependencies": {"react": "^19", "react-dom": "^19", "esbuild": "^0.24"},
}


def render_setup(brand: str) -> str:
    """The per-brand harness: render/package.json + render.mjs, npm install."""
    if shutil.which("node") is None or shutil.which("npm") is None:
        return _NO_NODE
    root = BRANDS_DIR / brand
    if not root.exists():
        return f"no library at brands/{brand} — scaffold first"
    rd = root / "render"
    rd.mkdir(exist_ok=True)
    (rd / "package.json").write_text(json.dumps(PACKAGE_JSON, indent=1))
    (rd / "render.mjs").write_text(RENDER_MJS)
    r = subprocess.run(["npm", "install", "--no-fund", "--no-audit"],
                       cwd=rd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        return f"npm install failed: {r.stderr[-300:]}"
    return f"render harness ready at brands/{brand}/render/ (react, react-dom, esbuild)"


def render(brand: str, component_file: str, props_json: str = "{}",
           scale: int = 2) -> str:
    """component → out/<name>.html, and for fixed-frame files → out/<name>.png
    at the declared WxH (retina by default: scale=2)."""
    root = BRANDS_DIR / brand
    rd = root / "render"
    if not (rd / "node_modules").exists():
        got = render_setup(brand)
        if not got.startswith("render harness"):
            return got
    src = root / component_file
    if not src.exists():
        return f"no such component: brands/{brand}/{component_file}"
    out_dir = root / "out"
    out_dir.mkdir(exist_ok=True)
    out_html = out_dir / (src.stem + ".html")

    r = subprocess.run(
        ["node", str(rd / "render.mjs"), str(src.resolve()), props_json, str(out_html.resolve())],
        cwd=rd, capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        return f"render failed: {(r.stderr or r.stdout)[-400:]}"
    report = [r.stdout.strip()]

    m = re.search(r"-(\d{2,4})x(\d{2,4})$", src.stem)
    if m:  # fixed frame -> pixels, with the crawler's own Chromium
        w, h = int(m.group(1)), int(m.group(2))
        out_png = out_dir / (src.stem + ".png")
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": w, "height": h},
                                        device_scale_factor=scale)
                page.goto(out_html.resolve().as_uri())
                page.screenshot(path=str(out_png), clip={"x": 0, "y": 0, "width": w, "height": h})
                browser.close()
            report.append(f"screenshot {out_png.name} ({w}x{h} @{scale}x, "
                          f"{out_png.stat().st_size // 1024} KB)")
        except Exception as e:  # noqa: BLE001
            report.append(f"screenshot failed ({type(e).__name__}: {e}) — the HTML is still good; "
                          "run `monty crawl setup` if Chromium is missing")
    return "\n".join(report)
