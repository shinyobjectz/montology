import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// The build OUTPUT is committed into the Python package: `monty canvas` must
// work from a uvx install on a machine with no Node. The bundle is generated
// material and is gated like every other generated file here — see the
// canvas provenance law in montology_gen.laws.
export default defineConfig({
  plugins: [svelte()],
  base: './',
  build: {
    outDir: '../.monty/canvas/src/montology_canvas/static',
    emptyOutDir: true,
    // One file each, so the served page is two requests and the committed
    // diff reads as "the bundle moved" rather than as churn in hashed names.
    rollupOptions: {
      output: {
        entryFileNames: 'assets/canvas.js',
        chunkFileNames: 'assets/canvas-[name].js',
        assetFileNames: 'assets/canvas.[ext]',
      },
    },
  },
});
