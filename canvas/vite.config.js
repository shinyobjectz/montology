import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The build OUTPUT is committed into the Python package: `monty canvas` must
// work from a uvx install on a machine with no Node. The bundle is generated
// material and gated like every other generated file here.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../.monty/canvas/src/montology_canvas/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/canvas.js',
        chunkFileNames: 'assets/canvas-[name].js',
        assetFileNames: 'assets/canvas.[ext]',
      },
    },
  },
});
