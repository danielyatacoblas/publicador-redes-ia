// Ejecuta el nodo Code "Filtrar publicables" fuera de n8n, simulando sus globals.
// Uso: node tests/correr_filtro_js.mjs '<json_array_de_items>'
// Devuelve por stdout los id_cola que el filtro dejaría publicar.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const jsCode = readFileSync(join(ROOT, 'workflows', 'src', 'filtrar_publicables.js'), 'utf8');
const entrada = JSON.parse(process.argv[2] || '[]');

const $input = { all: () => entrada.map((json) => ({ json })) };
const ejecutar = new Function('$input', jsCode);
const salida = ejecutar($input);

process.stdout.write(JSON.stringify(salida.map((s) => s.json.id_cola)));
