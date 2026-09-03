import { defineConfig } from 'vite';

// The build OUTPUT is committed into the Python package: `monty canvas` must
// work from a uvx install on a machine with no Node.
export default defineConfig({
  base: './',
  build: {
    outDir: '../.monty/canvas/src/montology_canvas/static',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/montology.js',
        chunkFileNames: 'assets/montology-[name].js',
        assetFileNames: 'assets/montology.[ext]',
      },
    },
  },
});
