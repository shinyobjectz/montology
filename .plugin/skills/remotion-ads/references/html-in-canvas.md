---
title: HTML in Canvas
description: Render live HTML/DOM into a canvas inside a Remotion composition, with optional WebGL2 fragment shaders for per-frame visual effects
section: composition
priority: medium
tags: [html-in-canvas, webgl, shader, dom, effect]
---

# HTML in Canvas

Remotion 4.0.455+ ships an experimental `<HtmlInCanvas>` component that renders
arbitrary DOM into a canvas every frame. Combined with a 2D context filter or
a WebGL2 fragment shader, you can apply effects (progressive blur, vintage
film, chromatic aberration, vignette, …) to live HTML content that would
otherwise be impossible with CSS alone.

This is most useful for:

- Animated post-process effects on real DOM (rich type, gradients, layout)
- Capturing a website into a Reel with a phone-frame mockup + scroll animation
- Cinematic transitions where the HTML content also animates per frame
- Browser-window mockups in product demos

> **Reference implementation:** the official Remotion examples repo at
> `github.com/remotion-dev/html-in-canvas` ships several demo compositions
> (`ArticleHighlight`, `Vintage`, etc.) — recommended starting point.

---

## Status & Compatibility

- **Remotion ≥ 4.0.455** required.
- API surface relies on **experimental Chrome features**:
  - `ctx.drawElementImage(elementImage, x, y)` (CanvasRenderingContext2D)
  - `gl.texElementImage2D(target, level, internalformat, format, type, source)` (WebGL2)
- These are gated behind `chrome://flags/#canvas-draw-element` in stock Chrome
  (Canary 149+). **Remotion's headless Chromium already has the flag enabled
  internally**, so server-side renders work without any user setup.
- The Chrome team can change or remove the API. Pin a Remotion version known to
  work and re-test before upgrading.
- Cannot be used inside `@remotion/web-renderer` (client-side bundle).
- Nesting `<HtmlInCanvas>` inside another `<HtmlInCanvas>` is not supported.

---

## Imports

```tsx
import {
  HtmlInCanvas,
  type HtmlInCanvasOnInit,
  type HtmlInCanvasOnPaint,
} from "remotion";
```

---

## Component API

```tsx
<HtmlInCanvas
  width={width}
  height={height}
  onInit={onInit}      // optional; called once per mount, returns cleanup
  onPaint={onPaint}    // called every frame
>
  {/* Any DOM tree — fonts, gradients, box-shadows, transforms, Img, Video */}
</HtmlInCanvas>
```

### Callback signatures

```ts
type HtmlInCanvasOnPaint = (payload: {
  canvas: HTMLCanvasElement;
  element: HTMLElement;
  elementImage: CanvasImageSource;
}) => void;

type HtmlInCanvasOnInit = (payload: {
  canvas: HTMLCanvasElement;
}) => void | (() => void);
```

`onPaint` runs every render frame. `elementImage` is a special source the
experimental Chrome API understands — pass it to `ctx.drawElementImage` or
`gl.texElementImage2D`. **It is not a regular `HTMLImageElement` — `ctx.drawImage`
will throw.**

`onInit` is the place to allocate GPU resources (WebGL program, textures, VAO);
return a cleanup function that frees them.

---

## TypeScript Workaround

`drawElementImage` and `texElementImage2D` are not yet in `@types/dom` /
`@types/webgl2`. Cast the call site to silence the error:

```ts
(ctx as unknown as {
  drawElementImage: (img: unknown, x: number, y: number) => void;
}).drawElementImage(elementImage, 0, 0);
```

```ts
(gl as unknown as {
  texElementImage2D: (
    target: number,
    level: number,
    internalformat: number,
    format: number,
    type: number,
    source: unknown
  ) => void;
}).texElementImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, elementImage);
```

---

## Pattern 1 — Plain 2D Context (Simple Effects)

Best for blur reveals, single drop-shadow, or stitching DOM into a procedurally
drawn background. No WebGL needed.

```tsx
import {
  AbsoluteFill,
  HtmlInCanvas,
  type HtmlInCanvasOnPaint,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const Card: React.FC = () => (
  <div style={{
    width: 720, height: 880, padding: 60, background: "#fff",
    borderRadius: 36, fontFamily: "Inter, system-ui, sans-serif",
  }}>
    {/* Anything you can render with HTML/CSS works here */}
  </div>
);

export const Demo: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const blurAmount = interpolate(frame, [0, 28], [32, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const onPaint: HtmlInCanvasOnPaint = ({ canvas, elementImage }) => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.reset();

    // Draw a procedural background straight to the canvas.
    const bg = ctx.createLinearGradient(0, 0, 0, canvas.height);
    bg.addColorStop(0, "#0F1B2D");
    bg.addColorStop(1, "#3B6B9A");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply per-frame filter to the live HTML snapshot.
    ctx.filter = `blur(${blurAmount}px)`;
    (ctx as unknown as {
      drawElementImage: (img: unknown, x: number, y: number) => void;
    }).drawElementImage(elementImage, 100, 100);
  };

  return (
    <AbsoluteFill>
      <HtmlInCanvas width={width} height={height} onPaint={onPaint}>
        <Card />
      </HtmlInCanvas>
    </AbsoluteFill>
  );
};
```

**Key tools available on the 2D context:**

| Tool | Use |
|------|-----|
| `ctx.filter = 'blur(Npx)'` | Per-frame blur amount |
| `ctx.fillStyle` / `ctx.createLinearGradient` | Procedural backdrops |
| `ctx.translate / scale / rotate` | Per-frame transform of the HTML snapshot |
| `ctx.globalAlpha` | Fade in/out |
| `ctx.globalCompositeOperation` | Blend modes (overlay, multiply, …) |

---

## Pattern 2 — WebGL2 Fragment Shader (Heavy Effects)

For Gaussian blur, chromatic aberration, vignette, grain, dust, scratches —
anything that needs per-pixel math — use a fragment shader. The DOM snapshot
is uploaded as a 2D texture each frame via `texElementImage2D`.

### Shape of the GL module

A typical `gl.ts` exports `initGl` and `paintGl`. `initGl` is called from
`HtmlInCanvas` `onInit`, `paintGl` is called from `onPaint`.

```ts
// gl.ts
import type { HtmlInCanvasOnInit, HtmlInCanvasOnPaint } from "remotion";

type ElementImage = Parameters<HtmlInCanvasOnPaint>[0]["elementImage"];
type Canvas = Parameters<HtmlInCanvasOnInit>[0]["canvas"];

export type GlState = {
  gl: WebGL2RenderingContext;
  program: WebGLProgram;
  texture: WebGLTexture;
  vao: WebGLVertexArrayObject;
  /* ...uniform locations */
};

const VS = `#version 300 es
in vec2 a_pos; in vec2 a_uv; out vec2 v_uv;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); v_uv = a_uv; }`;

const FS = `#version 300 es
precision highp float;
uniform sampler2D u_tex;
in vec2 v_uv;
out vec4 o;
void main() {
  // ...your effect here
  o = texture(u_tex, v_uv);
}`;

const QUAD = new Float32Array([
  -1, -1, 0, 0,   1, -1, 1, 0,   -1, 1, 0, 1,
   1, -1, 1, 0,  -1,  1, 0, 1,    1, 1, 1, 1,
]);

export const initGl = (canvas: Canvas) => {
  const gl = canvas.getContext("webgl2", {
    alpha: true, premultipliedAlpha: true, antialias: false,
  }) as WebGL2RenderingContext | null;
  if (!gl) throw new Error("WebGL2 unavailable");

  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
  // ...compile + link program, allocate texture, VAO, buffer
  // (see Remotion examples repo for complete reference impl)

  return { gpu /* ...GlState */, cleanup: () => { /* delete program/texture/vao/buffer */ } };
};

export const paintGl = (gpu: GlState, elementImage: ElementImage, params: { /* uniforms */ }) => {
  const { gl } = gpu;
  gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
  gl.clear(gl.COLOR_BUFFER_BIT);
  gl.useProgram(gpu.program);

  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, gpu.texture);

  // Upload the live DOM snapshot as a texture (every frame).
  (gl as unknown as {
    texElementImage2D: (
      t: number, l: number, ifmt: number, fmt: number, type: number, src: unknown
    ) => void;
  }).texElementImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, elementImage);

  // ...set uniforms, bind VAO, drawArrays
};
```

### Wiring it into a composition

```tsx
import { useCallback, useRef } from "react";
import { HtmlInCanvas, type HtmlInCanvasOnInit, type HtmlInCanvasOnPaint } from "remotion";
import { initGl, paintGl, type GlState } from "./gl";

export const Composition: React.FC = () => {
  const gpuRef = useRef<GlState | null>(null);

  const onInit: HtmlInCanvasOnInit = useCallback(({ canvas }) => {
    const { gpu, cleanup } = initGl(canvas);
    gpuRef.current = gpu;
    return () => { cleanup(); gpuRef.current = null; };
  }, []);

  const onPaint: HtmlInCanvasOnPaint = useCallback(({ elementImage }) => {
    if (gpuRef.current) paintGl(gpuRef.current, elementImage, /* uniforms */ {});
  }, []);

  return (
    <HtmlInCanvas width={1920} height={1080} onInit={onInit} onPaint={onPaint}>
      {/* Your DOM tree */}
    </HtmlInCanvas>
  );
};
```

---

## Effect Recipes

The Remotion examples repo (`github.com/remotion-dev/html-in-canvas/tree/main/src`)
has full reference shaders for these. Common building blocks:

### Progressive vertical blur (sharp band, blurry edges)

```glsl
float edgeY = abs(v_uv.y - 0.5) * 2.0;          // 0 at center, 1 at top/bottom
float blurMix = pow(smoothstep(0.035, 0.62, edgeY), 1.06);
float sigmaPx = blurMix * 4.25 + 0.05;          // 9×9 Gaussian kernel
// ...sample neighborhood with gauss1(x, sigmaPx) weights
vec3 color = mix(sharp.rgb, blurred, blurMix);
```

### Chromatic aberration (rim leak)

```glsl
vec2 fromCenter = uv - 0.5;
float r = length(fromCenter);
vec2 dir = r > 0.0001 ? normalize(fromCenter) : vec2(0.0);
float ca = 0.0024 * pow(r * 1.4, 1.6);          // edge-weighted
color.r = texture(u_tex, uv + dir * ca).r;
color.g = texture(u_tex, uv).g;
color.b = texture(u_tex, uv - dir * ca).b;
```

### Per-pixel grain quantized to 24fps

```glsl
float frameIdx = floor(u_time * 24.0);          // discrete film steps
float g = hash(gl_FragCoord.xy + vec2(frameIdx * 17.31, frameIdx * 7.91));
color += (g - 0.5) * u_grain;
```

### Gate weave (subtle frame jitter)

```glsl
vec2 weave = vec2(
  sin(u_time * 11.0) * 0.0015 + sin(u_time * 3.7) * 0.0009,
  cos(u_time *  8.3) * 0.0013 + cos(u_time * 2.4) * 0.0007
);
uv += weave;                                     // sample-coord offset
```

### Vignette + exposure flicker

```glsl
float vig = smoothstep(1.05, 0.30, r * 1.25);
color *= mix(1.0, vig, u_vignette);
float flicker = 1.0 + 0.035 * sin(u_time * 7.0) + 0.018 * sin(u_time * 19.0 + 1.3);
color *= flicker;
```

---

## Pattern 3 — Page-to-Video (Captured Site Tour)

To make a Reel that scrolls through an existing website, capture the page once
and animate `translateY` on the screenshot inside a phone-frame mockup. This
does **not** require `HtmlInCanvas` at all — a regular `<Img>` and `transform`
is enough. Listed here because it's a frequent companion pattern.

### Step 1 — Capture with Playwright

```js
// scripts/capture-page.mjs
import { chromium } from "playwright";
import fs from "node:fs";

const URL = process.env.URL || "http://localhost:4000";
const OUT = "public/tour/landing-fullpage.png";

fs.mkdirSync("public/tour", { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 414, height: 896 }, deviceScaleFactor: 2, isMobile: true,
});
const page = await ctx.newPage();
await page.goto(URL, { waitUntil: "networkidle" });

// Trigger lazy-loaded images / IntersectionObservers.
await page.evaluate(async () => {
  const total = document.documentElement.scrollHeight;
  for (let y = 0; y <= total; y += 400) {
    window.scrollTo(0, y);
    await new Promise((r) => setTimeout(r, 80));
  }
  window.scrollTo(0, 0);
});
await page.waitForTimeout(2500);

await page.screenshot({ path: OUT, fullPage: true });

// Extract real <section> positions so the tour can land on them precisely.
const stops = await page.evaluate(() => {
  const fullH = document.documentElement.scrollHeight;
  return Array.from(document.querySelectorAll("section")).map((el, i) => {
    const r = el.getBoundingClientRect();
    const heading = el.querySelector("h1, h2");
    return {
      index: i,
      label: (heading?.textContent ?? `Section ${i + 1}`).trim().slice(0, 80),
      scrollPercent: (r.top + window.scrollY) / fullH,
    };
  });
});
fs.writeFileSync("public/tour/stops.json", JSON.stringify({ stops }, null, 2));

await browser.close();
```

### Step 2 — Stop-and-go scroll timeline

Don't use a continuous `interpolate(frame, [0, durationInFrames], [0, 1])` —
it feels monotonous. Instead, build a piecewise timeline that **dwells** at
each section and travels quickly between them.

```ts
const STOPS = [
  { scroll: 0.000, caption: "Hero",     dwell: 36 },
  { scroll: 0.085, caption: "Trust",    dwell: 30 },
  { scroll: 0.357, caption: "Reviews",  dwell: 28 },
  { scroll: 0.657, caption: "Stats",    dwell: 28 },
  { scroll: 1.000, caption: "CTA",      dwell: 36 },
] as const;

const TRAVEL = 14; // frames to glide between stops

// Build keyframe arrays for interpolate()
const inputs: number[] = [];
const outputs: number[] = [];
const captionStart: number[] = [];
let t = 0;
for (let i = 0; i < STOPS.length; i++) {
  captionStart.push(t);
  inputs.push(t);            outputs.push(STOPS[i].scroll);
  t += STOPS[i].dwell;
  inputs.push(t);            outputs.push(STOPS[i].scroll);
  if (i < STOPS.length - 1) t += TRAVEL;
}

const scrollProgress = interpolate(frame, inputs, outputs, {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
  easing: Easing.inOut(Easing.cubic),
});
```

Use the real section positions extracted by your capture script — eyeballing
percentages produces stops that land between sections.

### Step 3 — Phone mockup with translateY

```tsx
const SHOT_W = 414;
const SHOT_H = /* extracted from capture */;
const PHONE_W = 640;
const PHONE_H = (PHONE_W * 896) / 414;
const scaledH = (SHOT_H * PHONE_W) / SHOT_W;
const headroomPx = PHONE_H * 0.05;
const sectionTopPx = scrollProgress * scaledH;
const maxScrollPx = scaledH - PHONE_H;
const translateY = Math.max(-maxScrollPx, Math.min(0, -(sectionTopPx - headroomPx)));

<div style={{ width: PHONE_W, height: PHONE_H, overflow: "hidden", borderRadius: 40 }}>
  <Img
    src={staticFile("tour/landing-fullpage.png")}
    style={{ width: PHONE_W, height: scaledH, transform: `translateY(${translateY}px)` }}
  />
</div>
```

`scrollProgress = sectionTop / fullPageHeight` — this is the *real fractional
position* of a section, not "0=top, 1=fully scrolled". The clamp + headroom
keep the section heading slightly below the phone notch.

---

## Render Commands

```bash
# Plain 2D context — no special flags needed
npx remotion render Composition out.mp4 --codec=h264 --crf=18

# WebGL2 — needs ANGLE for the headless GL stack
npx remotion render Composition out.mp4 --codec=h264 --crf=18 --gl=angle
```

---

## Gotchas

- **CSS animations / framer-motion inside `<HtmlInCanvas>` do not animate.**
  The whole DOM is rasterized to an `elementImage` once per frame from the
  *current* React tree. To animate, drive state from `useCurrentFrame()` and
  re-render — same pattern as any Remotion composition.

- **`ctx.drawImage(elementImage, …)` throws.** Use `ctx.drawElementImage`. The
  type system won't help — the cast above is necessary.

- **Multiple `TransitionSeries.Transition` wrapping `<HtmlInCanvas>` content
  can produce blank frames** on the second/third sequence. The exact cause is
  unclear (likely a snapshot pipeline interaction), but working around with
  fewer sequences or a single transition is reliable. Test with `npx remotion
  studio` first.

- **WebGL2 + parallel render workers can crash with `Page crashed!`** on macOS.
  Symptom: `TargetCloseError` after a few frames. Fix: render with
  `--concurrency=1`. Slower but stable. Likely VRAM contention from the
  per-frame `texElementImage2D` upload.

- **Remotion's headless Chromium has the experimental flag enabled** even
  though stock Chrome requires `chrome://flags/#canvas-draw-element`. Local
  studio preview also works. End users opening the bundled output don't need
  the flag — they're watching a rasterized MP4.

- **Cleanup in `onInit` matters.** Return a disposer that deletes the program,
  texture, VAO, and buffer. Otherwise hot-reload during studio dev leaks GPU
  memory.

- **Premultiplied alpha + `gl.UNPACK_FLIP_Y_WEBGL = true`** matches what
  `texElementImage2D` produces. Forgetting the Y-flip renders the page
  upside-down.

---

## When NOT to Use HtmlInCanvas

- For straight scrolling-screenshot product tours, plain `<Img>` + `translateY`
  is simpler and faster (Pattern 3 above).
- For static graphics that don't need per-frame post-processing, just use
  Remotion's normal compositing.
- For rendering text with a single shadow or gradient — CSS does that already.

Use `HtmlInCanvas` when you specifically need a per-frame canvas-side effect
(blur, shader, procedural compositing) on top of live HTML.

---

## Reference Examples

- **`ArticleHighlight`** — progressive vertical blur + animated highlighter
  sweep with `mix-blend-mode: multiply` over a styled article.
  https://github.com/remotion-dev/html-in-canvas/tree/main/src/ArticleHighlight

- **`Vintage`** — full vintage-film treatment (gate weave, chromatic
  aberration, grain, scratches, dust, light leaks, vignette, flicker) over
  slide-transitioned title cards.
  https://github.com/remotion-dev/html-in-canvas/tree/main/src/Vintage

Both ship a `gl.ts` with the WebGL2 setup and a `index.tsx` with the
composition wiring. Treat them as canonical reference implementations.
