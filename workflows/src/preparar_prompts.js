// Nodo Code de n8n — "Preparar prompts por red"
// Toma cada fila del calendario y la expande a un item por red social,
// con el prompt ya armado según las reglas de esa red.
// Espejo de src/generador.py (REDES + _prompt_para).

const REDES = {
  instagram: { nombre: 'Instagram', max: 2200, emojis: true, tono: 'cercano e inspirador', cta: 'Escríbenos por DM 📩' },
  facebook: { nombre: 'Facebook', max: 1500, emojis: true, tono: 'informativo y cálido', cta: 'Más información en el enlace de nuestra bio' },
  linkedin: { nombre: 'LinkedIn', max: 1800, emojis: false, tono: 'profesional y de impacto', cta: 'Conversemos sobre alianzas' },
  tiktok: { nombre: 'TikTok', max: 300, emojis: true, tono: 'directo y juvenil', cta: 'Link en bio 🔗' },
};

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
  'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

function fechaLegible(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  if (!m) return iso || '';
  return `${parseInt(m[3], 10)} de ${MESES[parseInt(m[2], 10) - 1]}`;
}

function construirPrompt(fila, redKey) {
  const r = REDES[redKey];
  return [
    'Eres el community manager del Club STEM, una organización peruana que',
    'acerca la ciencia y la tecnología a niñas y niños.',
    '',
    `Escribe un post para ${r.nombre} sobre este contenido:`,
    `- Tipo: ${fila.tipo}`,
    `- Título: ${fila.titulo || ''}`,
    `- Detalle: ${fila.detalle || ''}`,
    `- Fecha: ${fechaLegible(fila.fecha)}`,
    `- Lugar: ${fila.lugar || ''}`,
    fila.cupos ? `- Cupos: ${fila.cupos}` : '',
    '',
    'Reglas obligatorias:',
    `- Tono ${r.tono}.`,
    `- Máximo ${r.max} caracteres en total.`,
    `- ${r.emojis ? 'Usa emojis con moderación.' : 'NO uses emojis.'}`,
    '- Español de Perú, claro y sin tecnicismos innecesarios.',
    '- No inventes datos que no estén arriba (fechas, cifras, nombres).',
    '- No prometas resultados educativos garantizados.',
    '',
    'Devuelve SOLO el texto del post, sin hashtags ni comillas.',
  ].filter(Boolean).join('\n');
}

const salida = [];

for (const item of $input.all()) {
  const fila = item.json;
  const redes = String(fila.redes || '').split(',').map((r) => r.trim().toLowerCase()).filter(Boolean);

  for (const red of redes) {
    if (!REDES[red]) continue;   // red no soportada: se ignora sin romper el flujo
    salida.push({
      json: {
        id_contenido: fila.id,
        id_cola: `${fila.id}:${red}`,
        red,
        tipo: fila.tipo,
        titulo: fila.titulo,
        fecha_programada: fila.fecha,
        max_caracteres: REDES[red].max,
        cta: REDES[red].cta,
        prompt: construirPrompt(fila, red),
        estado: 'pendiente',
        origen: 'claude',
      },
    });
  }
}

return salida;
