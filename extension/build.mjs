import { build } from 'esbuild';
import { mkdir, copyFile } from 'node:fs/promises';

await mkdir('dist', { recursive: true });
await build({ entryPoints: ['src/background.ts', 'src/content.ts', 'src/popup.ts', 'src/core.ts', 'src/snapshot.ts'], bundle: true, outdir: 'dist', format: 'esm', target: 'chrome120' });
// Content scripts are classic scripts, not ES modules.
await build({ entryPoints: ['src/content.ts'], bundle: true, outfile: 'dist/content.js', format: 'iife', target: 'chrome120' });
for (const name of ['manifest.json', 'popup.html', 'popup.css']) await copyFile(`static/${name}`, `dist/${name}`);
