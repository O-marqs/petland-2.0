import { readFile } from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';
const schema = new URL('../openapi.json', import.meta.url);
const target = new URL('../src/schema.d.ts', import.meta.url);
const generated = astToString(await openapiTS(schema));
const current = await readFile(target, 'utf8');
// CLI adds its generated-file banner; compare the actual declarations too.
const strip = (text) => text.replace(/^\/\*\*[\s\S]*?\*\/\s*/, '').replaceAll('\r\n', '\n').trim();
if (strip(generated) !== strip(current)) {
  throw new Error('Generated API types are stale. Run pnpm contracts:generate.');
}
console.log('Generated API types match OpenAPI.');
