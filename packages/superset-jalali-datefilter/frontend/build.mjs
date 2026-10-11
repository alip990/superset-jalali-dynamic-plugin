import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

import esbuild from 'esbuild';

const here = dirname(fileURLToPath(import.meta.url));
const pkg = JSON.parse(readFileSync(join(here, 'package.json'), 'utf8'));
const outDir = process.env.OUT_DIR || join(here, '..', 'src', 'superset_jalali_datefilter', 'static');
const forbidden = ['__SECRET_INTERNALS_DO_NOT_USE', 'react.production.min', 'SecretInternals'];

mkdirSync(outDir, { recursive: true });
for (const name of readdirSync(outDir)) {
  if (name.endsWith('.js') || name.endsWith('.map') || name === 'manifest.json') {
    rmSync(join(outDir, name));
  }
}

const alias = {
  react: join(here, 'src/shims/react.ts'),
  'react-dom': join(here, 'src/shims/react-dom.ts'),
  '@superset-ui/core': join(here, 'src/shims/superset-ui-core.ts'),
};

async function emit(entry, key) {
  const outfile = join(outDir, `${key}.tmp.js`);
  await esbuild.build({
    entryPoints: [entry],
    outfile,
    bundle: true,
    minify: true,
    sourcemap: true,
    format: 'esm',
    target: 'es2019',
    jsx: 'transform',
    jsxFactory: 'React.createElement',
    jsxFragment: 'React.Fragment',
    define: { __VERSION__: JSON.stringify(pkg.version) },
    alias,
    legalComments: 'none',
  });
  const source = readFileSync(outfile);
  for (const needle of forbidden) {
    if (source.includes(Buffer.from(needle))) {
      throw new Error(`${key} bundle contains a second React (${needle})`);
    }
  }
  const gz = gzipSync(source).length;
  if (key === 'jalali-datefilter' && gz > 60 * 1024) {
    throw new Error(`${key} gzipped size ${gz} exceeds 60 KB`);
  }
  const hash = createHash('sha256').update(source).digest('hex').slice(0, 10);
  const filename = `${key}.${hash}.js`;
  writeFileSync(join(outDir, filename), source);
  const map = readFileSync(`${outfile}.map`);
  writeFileSync(join(outDir, `${filename}.map`), map);
  rmSync(outfile);
  rmSync(`${outfile}.map`);
  console.log(`${filename} gzip=${gz}`);
  return filename;
}

const file = await emit(join(here, 'src/index.ts'), 'jalali-datefilter');
const hello = await emit(join(here, 'src/hello.ts'), 'hello');
writeFileSync(
  join(outDir, 'manifest.json'),
  JSON.stringify({ file, hello, version: pkg.version }, null, 2),
);
