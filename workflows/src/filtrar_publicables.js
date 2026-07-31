// Nodo Code de n8n — "Filtrar publicables"
// Deja pasar SOLO los posts aprobados por una persona cuya fecha programada
// ya llegó. Es la implementación de la política de revisión humana dentro
// del workflow (espejo de ColaAprobacion.listos_para_publicar).

const ahora = Date.now();

return $input.all().filter((item) => {
  const f = item.json;

  // Regla de oro: sin aprobación humana explícita, no se publica.
  if (String(f.estado || '').toLowerCase() !== 'aprobado') return false;

  // Debe constar quién aprobó (trazabilidad).
  if (!String(f.revisor || '').trim()) return false;

  // Respeta la fecha programada.
  if (f.fecha_programada) {
    const programada = Date.parse(f.fecha_programada);
    if (!isNaN(programada) && ahora < programada) return false;
  }

  return true;
}).map((item) => ({
  json: {
    ...item.json,
    publicado_en: new Date().toISOString(),
  },
}));
