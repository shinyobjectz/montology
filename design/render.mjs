// GENERATED render harness — monty brand render-setup
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
