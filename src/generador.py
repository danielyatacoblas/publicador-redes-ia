"""Generación de borradores de contenido por red social.

Dos motores intercambiables:
  - "plantillas" (por defecto): 100 % offline y determinista. Permite probar
    todo el flujo sin API key ni costo.
  - "claude": usa la API de Anthropic si hay ANTHROPIC_API_KEY en el entorno.

Ambos respetan las mismas reglas por red (largo, tono, hashtags, CTA) que
viven en REDES, para que el resultado sea comparable y testeable.
"""
from __future__ import annotations

import os
import re
import textwrap
from dataclasses import dataclass, field

# ── Reglas por red social ───────────────────────────────────────────────────

@dataclass(frozen=True)
class ReglaRed:
    nombre: str
    max_caracteres: int
    hashtags: int          # cantidad recomendada
    emojis: bool
    tono: str
    cta_por_defecto: str


REDES: dict[str, ReglaRed] = {
    "instagram": ReglaRed("Instagram", 2200, 8, True, "cercano e inspirador",
                          "Escríbenos por DM 📩"),
    "facebook": ReglaRed("Facebook", 1500, 4, True, "informativo y cálido",
                         "Más información en el enlace de nuestra bio"),
    "linkedin": ReglaRed("LinkedIn", 1800, 3, False, "profesional y de impacto",
                         "Conversemos sobre alianzas"),
    "tiktok": ReglaRed("TikTok", 300, 5, True, "directo y juvenil",
                       "Link en bio 🔗"),
}

TIPOS_CONTENIDO = ("convocatoria", "testimonio", "tip_stem", "evento", "logro")


# ── Estructura del contenido ────────────────────────────────────────────────

@dataclass
class Borrador:
    id_contenido: str
    red: str
    tipo: str
    titulo: str
    texto: str
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""
    origen: str = "plantillas"      # plantillas | claude
    fecha_programada: str = ""

    @property
    def texto_completo(self) -> str:
        partes = [self.texto.strip()]
        if self.cta:
            partes.append(self.cta)
        if self.hashtags:
            partes.append(" ".join(f"#{h}" for h in self.hashtags))
        return "\n\n".join(partes)

    @property
    def largo(self) -> int:
        return len(self.texto_completo)


# ── Banco de hashtags por tipo (curado, no aleatorio) ───────────────────────

_HASHTAGS = {
    "base": ["ClubSTEM", "EducacionSTEM", "Peru"],
    "convocatoria": ["Inscripciones", "TalleresSTEM", "Robotica", "Programacion",
                     "AprendeHaciendo"],
    "testimonio": ["HistoriasQueInspiran", "Testimonio", "OrgulloSTEM",
                   "Comunidad"],
    "tip_stem": ["TipSTEM", "CienciaEnCasa", "AprendeJugando", "Curiosidad",
                 "Experimentos"],
    "evento": ["Evento", "FeriaCientifica", "NoTeLoPierdas", "Agenda"],
    "logro": ["Logro", "Gracias", "Impacto", "JuntosSumamos"],
}


def _hashtags_para(tipo: str, cantidad: int) -> list[str]:
    pool = _HASHTAGS["base"] + _HASHTAGS.get(tipo, [])
    return pool[:max(0, cantidad)]


# ── Motor de plantillas (offline, determinista) ─────────────────────────────

_PLANTILLAS = {
    "convocatoria": {
        "instagram": ("🚀 ¡Abrimos inscripciones para {titulo}!\n\n"
                      "{detalle}\n\n"
                      "📅 {fecha_legible}   📍 {lugar}\n"
                      "Cupos limitados: {cupos} niñas y niños."),
        "facebook": ("Ya están abiertas las inscripciones para {titulo}.\n\n"
                     "{detalle}\n\n"
                     "Fecha: {fecha_legible}\nLugar: {lugar}\n"
                     "Cupos disponibles: {cupos}."),
        "linkedin": ("Abrimos convocatoria para {titulo}.\n\n"
                     "{detalle}\n\n"
                     "Este programa forma parte de nuestro compromiso con el "
                     "acceso equitativo a la educación STEM en el Perú."),
        "tiktok": ("¿{titulo}? 👀 Sí, y es gratis.\n{detalle_corto}"),
    },
    "testimonio": {
        "instagram": ("💬 «{detalle}»\n\n"
                      "— {titulo}\n\n"
                      "Historias como esta son el motivo de todo lo que hacemos."),
        "facebook": ("Hoy queremos compartir la historia de {titulo}.\n\n"
                     "«{detalle}»\n\n"
                     "Gracias por confiar en el Club STEM."),
        "linkedin": ("Historias de impacto: {titulo}.\n\n"
                     "«{detalle}»\n\n"
                     "Medir el impacto también es escuchar a quienes participan."),
        "tiktok": ("«{detalle_corto}» — {titulo} 💚"),
    },
    "tip_stem": {
        "instagram": ("🔬 Tip STEM de la semana: {titulo}\n\n{detalle}\n\n"
                      "Guarda este post para probarlo en casa 👇"),
        "facebook": ("Tip STEM para hacer en casa: {titulo}\n\n{detalle}\n\n"
                     "¿Lo probaste? Cuéntanos cómo te fue en los comentarios."),
        "linkedin": ("Divulgación STEM: {titulo}\n\n{detalle}\n\n"
                     "Acercar la ciencia al hogar multiplica el aprendizaje."),
        "tiktok": ("{titulo} en 15 segundos ⚡\n{detalle_corto}"),
    },
    "evento": {
        "instagram": ("📣 {titulo}\n\n{detalle}\n\n📅 {fecha_legible}  📍 {lugar}\n"
                      "¡Te esperamos!"),
        "facebook": ("{titulo}\n\n{detalle}\n\n🗓️ {fecha_legible}\n📍 {lugar}\n"
                     "Entrada libre, cupos por orden de llegada."),
        "linkedin": ("Invitación: {titulo}.\n\n{detalle}\n\n"
                     "Fecha: {fecha_legible} | Lugar: {lugar}."),
        "tiktok": ("{titulo} 🎉 {fecha_legible}\n{detalle_corto}"),
    },
    "logro": {
        "instagram": ("🎉 {titulo}\n\n{detalle}\n\n"
                      "Gracias a cada familia, voluntario y aliado que lo hizo posible."),
        "facebook": ("{titulo}\n\n{detalle}\n\n"
                     "Este logro es de toda la comunidad del Club STEM. ¡Gracias!"),
        "linkedin": ("{titulo}\n\n{detalle}\n\n"
                     "Agradecemos a las organizaciones aliadas que hacen posible "
                     "este impacto."),
        "tiktok": ("{titulo} 🏆\n{detalle_corto}"),
    },
}

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_legible(iso: str) -> str:
    """'2026-08-14' → '14 de agosto'."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return iso or ""
    _, mes, dia = m.groups()
    return f"{int(dia)} de {_MESES[int(mes) - 1]}"


def _recortar(texto: str, limite: int) -> str:
    """Recorta al límite prefiriendo cerrar en una frase completa.

    Si hay un final de oración dentro del último 40 % del texto permitido,
    corta ahí (queda natural). Si no, corta por palabra y marca con '…'.
    """
    texto = texto.strip()
    if len(texto) <= limite:
        return texto
    recorte = texto[:limite]
    fin_frase = max(recorte.rfind(". "), recorte.rfind("! "), recorte.rfind("? "),
                    recorte.rfind("."), recorte.rfind("!"), recorte.rfind("?"))
    if fin_frase >= limite * 0.6:
        return recorte[:fin_frase + 1].strip()
    return recorte[:limite - 1].rsplit(" ", 1)[0].rstrip(",;: ") + "…"


def generar_con_plantillas(item: dict, red: str) -> Borrador:
    regla = REDES[red]
    tipo = item["tipo"]
    plantilla = _PLANTILLAS[tipo][red]
    detalle = item.get("detalle", "")
    ctx = {
        "titulo": item.get("titulo", ""),
        "detalle": detalle,
        "detalle_corto": _recortar(detalle, 90),
        "fecha_legible": fecha_legible(item.get("fecha", "")),
        "lugar": item.get("lugar", "Sede del Club STEM"),
        "cupos": item.get("cupos", 20),
    }
    texto = textwrap.dedent(plantilla.format(**ctx)).strip()
    if not regla.emojis:
        texto = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", texto).strip()
        texto = re.sub(r"[ \t]{2,}", " ", texto)

    hashtags = _hashtags_para(tipo, regla.hashtags)
    cta = item.get("cta") or regla.cta_por_defecto
    if not regla.emojis:
        cta = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", "", cta).strip()

    b = Borrador(id_contenido=item["id"], red=red, tipo=tipo,
                 titulo=item.get("titulo", ""), texto=texto,
                 hashtags=hashtags, cta=cta, origen="plantillas",
                 fecha_programada=item.get("fecha", ""))
    # respeta el límite de la red recortando el cuerpo, no el CTA ni hashtags
    exceso = b.largo - regla.max_caracteres
    if exceso > 0:
        b.texto = _recortar(b.texto, max(20, len(b.texto) - exceso))
    return b


# ── Motor Claude (opcional) ─────────────────────────────────────────────────

def _prompt_para(item: dict, red: str) -> str:
    regla = REDES[red]
    return textwrap.dedent(f"""
        Eres el community manager del Club STEM, una organización peruana que
        acerca la ciencia y la tecnología a niñas y niños.

        Escribe un post para {regla.nombre} sobre este contenido:
        - Tipo: {item['tipo']}
        - Título: {item.get('titulo', '')}
        - Detalle: {item.get('detalle', '')}
        - Fecha: {fecha_legible(item.get('fecha', ''))}
        - Lugar: {item.get('lugar', '')}

        Reglas obligatorias:
        - Tono {regla.tono}.
        - Máximo {regla.max_caracteres} caracteres en total.
        - {'Usa emojis con moderación.' if regla.emojis else 'NO uses emojis.'}
        - Español de Perú, claro y sin tecnicismos innecesarios.
        - No inventes datos que no estén arriba (fechas, cifras, nombres).

        Devuelve SOLO el texto del post, sin hashtags ni comillas.
    """).strip()


def generar_con_claude(item: dict, red: str, modelo: str = "claude-sonnet-5") -> Borrador:
    """Genera con la API de Anthropic. Requiere ANTHROPIC_API_KEY."""
    from anthropic import Anthropic   # import perezoso: no es dependencia obligatoria

    regla = REDES[red]
    cliente = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = cliente.messages.create(
        model=modelo,
        max_tokens=800,
        messages=[{"role": "user", "content": _prompt_para(item, red)}],
    )
    texto = "".join(bloque.text for bloque in resp.content
                    if getattr(bloque, "type", "") == "text").strip()
    return Borrador(id_contenido=item["id"], red=red, tipo=item["tipo"],
                    titulo=item.get("titulo", ""), texto=texto,
                    hashtags=_hashtags_para(item["tipo"], regla.hashtags),
                    cta=item.get("cta") or regla.cta_por_defecto,
                    origen="claude", fecha_programada=item.get("fecha", ""))


# ── API pública ─────────────────────────────────────────────────────────────

def generar_borradores(item: dict, redes: list[str] | None = None,
                       motor: str = "plantillas") -> list[Borrador]:
    """Genera un borrador por cada red pedida para un item del calendario."""
    redes = redes or item.get("redes") or list(REDES)
    salida = []
    for red in redes:
        red = red.strip().lower()
        if red not in REDES:
            raise ValueError(f"red no soportada: {red}")
        if motor == "claude":
            salida.append(generar_con_claude(item, red))
        else:
            salida.append(generar_con_plantillas(item, red))
    return salida


def validar_borrador(b: Borrador) -> tuple[bool, list[str]]:
    """Reglas duras antes de que un post entre a la cola de aprobación."""
    regla = REDES[b.red]
    problemas = []
    if not b.texto.strip():
        problemas.append("texto vacío")
    if b.largo > regla.max_caracteres:
        problemas.append(f"excede {regla.max_caracteres} caracteres ({b.largo})")
    if not regla.emojis and re.search(r"[\U0001F300-\U0001FAFF]", b.texto_completo):
        problemas.append("contiene emojis y la red no los admite")
    if "{" in b.texto or "}" in b.texto:
        problemas.append("quedaron variables de plantilla sin reemplazar")
    return (not problemas), problemas
