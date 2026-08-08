# -*- coding: utf-8 -*-
"""Dibuja `docs/flujo.svg`: del calendario a la publicación, con la persona en medio.

    python scripts/simular_publicacion.py    # primero, deja los CSV
    python scripts/diagrama.py

Las cifras de las tarjetas **se leen de `data/*.csv`**, que es lo que produce la
simulación. No están escritas a mano: si cambia el calendario o la política de
revisión, se corren los dos y el dibujo se corrige solo. Un diagrama que dice
una cantidad que ya no es cierta es peor que no tener diagrama.

Se genera en SVG y no en Mermaid porque hace falta controlar el tamaño de cada
tarjeta para meter varias cifras dentro, y porque un SVG se abre a pantalla
completa y sirve igual para el README que para la web del portafolio.
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
DATOS = RAIZ / "data"

W, H = 2000, 1180
COL = ["#e2e8f0", "#ede9fe", "#fee2e2", "#dbeafe", "#dcfce7"]

TITULO = "Publicador de redes con IA · la IA redacta, una persona aprueba"
BAJADA = ("Automatizar del todo no sirve: publicar sin revisar, en nombre de "
          "una organización que trabaja con menores, es inaceptable. Las cifras "
          "salen de data/*.csv, que produce la simulación.")
PIE = ("El paso que no se puede quitar es el del medio. Sin él esto sería un "
       "bot; con él es una herramienta que un equipo de comunicaciones puede "
       "usar sin miedo.")

CARRILES = [
    ("Entrada", "Lo que ya se planifica"),
    ("Redacción", "Un borrador por red"),
    ("Criterio humano", "El paso que no se salta"),
    ("Publicación", "Cuando toca y donde toca"),
    ("Valor", "Qué gana el equipo"),
]


def _t(x, y, txt, size=12, peso="400", color="#0f172a", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{peso}" '
            f'fill="{color}" text-anchor="{anchor}">{escape(str(txt))}</text>')


def _partir(texto: str, ancho: int) -> list:
    lineas, actual = [], ""
    for p in texto.split():
        if len(actual) + len(p) + 1 > ancho:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def tarjeta(x, y, w, h, titulo, lineas, etiqueta, color, cifras=None):
    """La etiqueta va ARRIBA del título: a su derecha se solapan en cuanto el
    título pasa de tres palabras, y eso no se ve hasta renderizar."""
    p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
         f'fill="#ffffff" stroke="#94a3b8" stroke-width="2" '
         f'filter="url(#shadow)"/>']
    yy = y + 26
    if etiqueta:
        ew = 12 + len(etiqueta) * 6.4
        p.append(f'<rect x="{x + 16}" y="{y + 12}" width="{ew}" height="20" '
                 f'rx="10" fill="{color}"/>')
        p.append(_t(x + 16 + ew / 2, y + 26, etiqueta, 9.5, "700",
                    "#0f172a", "middle"))
        yy = y + 54
    for ln in _partir(titulo, int((w - 32) / 8.1)):
        p.append(_t(x + 16, yy, ln, 14.5, "700"))
        yy += 19
    yy += 6
    for ln in lineas:
        p.append(_t(x + 16, yy, ln, 11, "400", "#475569"))
        yy += 16
    if cifras:
        yy += 4
        p.append(f'<line x1="{x + 16}" y1="{yy - 12}" x2="{x + w - 16}" '
                 f'y2="{yy - 12}" stroke="#e2e8f0" stroke-width="1.5"/>')
        for et, val, tono in cifras:
            p.append(_t(x + 16, yy + 4, et, 9.5, "600", "#64748b"))
            p.append(_t(x + w - 16, yy + 4, val, 12, "700", tono, "end"))
            yy += 19
    return "".join(p)


def flecha(x1, y1, x2, y2, texto="", punteada=False, color="#334155"):
    mx = (x1 + x2) / 2
    guion = ' stroke-dasharray="8 7"' if punteada else ""
    s = (f'<path d="M {x1} {y1} H {mx} V {y2} H {x2}" fill="none" '
         f'stroke="{color}" stroke-width="2.2"{guion} '
         f'marker-end="url(#arrow)"/>')
    if texto:
        s += (f'<text x="{mx}" y="{min(y1, y2) - 10}" font-size="11" '
              f'font-weight="600" fill="{color}" text-anchor="middle" '
              f'stroke="#ffffff" stroke-width="5" paint-order="stroke">'
              f'{escape(texto)}</text>')
    return s


def _leer(nombre: str) -> list:
    f = DATOS / nombre
    if not f.exists():
        return []
    with f.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def cifras() -> dict:
    """Lo que de verdad hay en los CSV que dejó la simulación."""
    cal = _leer("calendario.csv")
    bor = _leer("borradores.csv")
    pub = _leer("publicados.csv")
    met = _leer("metricas.csv")

    # `estado` solo distingue publicado de rechazado; lo que separa «aprobado
    # tal cual» de «editado y aprobado» es `origen`: humano significa que una
    # persona metió mano en el texto antes de dejarlo pasar.
    rechazados = sum(1 for b in bor if b.get("estado") == "rechazado")
    editados = sum(1 for b in bor
                   if b.get("estado") == "publicado"
                   and b.get("origen") == "humano")
    aprobados = sum(1 for b in bor
                    if b.get("estado") == "publicado"
                    and b.get("origen") != "humano")
    estados = Counter({"aprobado": aprobados, "editado": editados,
                       "rechazado": rechazados})
    redes = sorted({b.get("red", "") for b in bor if b.get("red")})
    reintentos = sum(1 for p in pub if (p.get("intentos") or "1") not in ("1", ""))

    tasas = {}
    for m in met:
        origen = m.get("origen") or "?"
        try:
            tasas.setdefault(origen, []).append(float(m["tasa_interaccion"]))
        except (KeyError, TypeError, ValueError):
            pass
    medias = {k: sum(v) / len(v) for k, v in tasas.items() if v}

    return {
        "contenidos": len(cal),
        "borradores": len(bor),
        "redes": len(redes),
        "aprobados": estados.get("aprobado", 0),
        "editados": estados.get("editado", 0),
        "rechazados": estados.get("rechazado", 0),
        "publicados": len(pub),
        "reintentos": reintentos,
        "medias": medias,
    }


def main() -> int:
    c = cifras()
    if not c["borradores"]:
        print("  No hay datos. Corre antes: "
              "python scripts/simular_publicacion.py")
        return 1

    revisados = c["aprobados"] + c["editados"] + c["rechazados"]
    pct = (lambda n: f"{n * 100 // revisados} %" if revisados else "—")

    cx = [60, 460, 860, 1240, 1620]
    cw = [360, 360, 340, 340, 320]

    piezas = ['<rect width="100%" height="100%" fill="#f8fafc"/>',
              _t(48, 52, TITULO, 29, "700")]
    for i, ln in enumerate(_partir(BAJADA, 118)):
        piezas.append(_t(48, 82 + i * 20, ln, 14, "400", "#475569"))

    top, alto = 150, 900
    for i, (nombre, sub) in enumerate(CARRILES):
        piezas.append(f'<rect x="{cx[i]}" y="{top}" width="{cw[i]}" '
                      f'height="{alto}" rx="18" fill="{COL[i]}" '
                      f'fill-opacity="0.5" stroke="#94a3b8" '
                      f'stroke-width="1.5"/>')
        piezas.append(_t(cx[i] + 16, top + 28, nombre.upper(), 13, "700",
                         "#334155"))
        piezas.append(_t(cx[i] + 16, top + 46, sub, 10.5, "400", "#64748b"))

    # ── flechas (antes que las tarjetas, para que queden debajo) ───────────
    piezas.append(flecha(cx[0] + cw[0] - 20, 330, cx[1] + 20, 330,
                         "cada día 08:00"))
    piezas.append(flecha(cx[1] + cw[1] - 20, 330, cx[2] + 20, 400,
                         f"{c['borradores']} borradores"))
    piezas.append(flecha(cx[2] + cw[2] - 20, 360, cx[3] + 20, 330,
                         "aprobado"))
    piezas.append(flecha(cx[2] + cw[2] - 20, 460, cx[3] + 20, 640,
                         "rechazado", punteada=True, color="#b91c1c"))
    piezas.append(flecha(cx[3] + cw[3] - 20, 330, cx[4] + 20, 300, ""))
    piezas.append(flecha(cx[3] + cw[3] - 20, 640, cx[4] + 20, 540, ""))
    piezas.append(flecha(cx[3] + cw[3] - 20, 860, cx[4] + 20, 780, ""))
    # las métricas vuelven al calendario: es un ciclo, no una línea recta
    piezas.append(
        f'<path d="M {cx[3] + 150} 940 V 1010 H {cx[0] + 150} V 800" '
        f'fill="none" stroke="#0891b2" stroke-width="2.2" '
        f'stroke-dasharray="8 7" marker-end="url(#arrow)"/>'
        + _t((cx[0] + cx[3]) / 2 + 150, 1002,
             "las métricas vuelven al calendario: qué tipo de post funciona",
             11.5, "600", "#0891b2", "middle"))

    # ── entrada ────────────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[0] + 20, 250, cw[0] - 40, 175,
        "Calendario de contenido",
        ["Lo que el equipo ya planifica en una",
         "hoja: talleres, testimonios, tips.",
         "No hay herramienta nueva que",
         "aprender."],
        "YA EXISTE", "#e2e8f0",
        [("contenidos programados", str(c["contenidos"]), "#334155")]))
    piezas.append(tarjeta(
        cx[0] + 20, 620, cw[0] - 40, 180,
        "Plantillas de prompt versionadas",
        ["Una por tipo de contenido, en",
         "prompts/. Cambiar el tono es",
         "editar un archivo de texto, no",
         "tocar el flujo."],
        "EN GIT", "#dbeafe",
        [("tipos de contenido", "3", "#1e40af")]))

    # ── redacción ──────────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[1] + 20, 240, cw[1] - 40, 250,
        "Claude redacta por red",
        ["Cada red tiene su largo, su tono y",
         "sus hashtags. Un mismo taller no se",
         "cuenta igual en LinkedIn que en",
         "TikTok."],
        "IA", "#ede9fe",
        [("redes distintas", str(c["redes"]), "#5b21b6"),
         ("borradores generados", str(c["borradores"]), "#5b21b6"),
         ("por contenido",
          f"{c['borradores'] / max(1, c['contenidos']):.1f}", "#5b21b6")]))
    piezas.append(tarjeta(
        cx[1] + 20, 570, cw[1] - 40, 225,
        "Validación antes de la cola",
        ["Largo por red, hashtags, enlaces.",
         "Un borrador que no cumple no llega",
         "a molestar a una persona: se",
         "descarta antes."],
        "AUTOMÁTICO", "#dcfce7",
        [("si la IA no está", "plantillas", "#166534"),
         ("el flujo", "no se cae", "#166534")]))

    # ── criterio humano ────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[2] + 20, 300, cw[2] - 40, 300,
        "Una persona aprueba, edita o rechaza",
        ["Nada sale al aire sin que alguien lo",
         "mire. No es un paso opcional que se",
         "pueda saltar con prisa: sin",
         "aprobación no hay publicación.",
         "",
         "El rechazo guarda el motivo, y eso",
         "es lo que mejora los prompts."],
        "OBLIGATORIO", "#fee2e2",
        [("aprobados directo",
          f"{c['aprobados']}  ({pct(c['aprobados'])})", "#166534"),
         ("editados y aprobados",
          f"{c['editados']}  ({pct(c['editados'])})", "#92400e"),
         ("rechazados",
          f"{c['rechazados']}  ({pct(c['rechazados'])})", "#b91c1c")]))

    # ── publicación ────────────────────────────────────────────────────────
    piezas.append(tarjeta(
        cx[3] + 20, 250, cw[3] - 40, 165,
        "Publica en su fecha",
        ["Aprobado no es publicado: espera a",
         "la fecha del calendario."],
        "", "",
        [("publicados", str(c["publicados"]), "#166534")]))
    piezas.append(tarjeta(
        cx[3] + 20, 480, cw[3] - 40, 180,
        "Si la API falla, reintenta",
        ["Un error de red no puede perder un",
         "post aprobado. Se marca, se",
         "reintenta y se avisa."],
        "", "",
        [("necesitaron reintento", str(c["reintentos"]), "#92400e"),
         ("perdidos", "0", "#166534")]))
    piezas.append(tarjeta(
        cx[3] + 20, 780, cw[3] - 40, 165,
        "Métricas 24 h después",
        ["Alcance e interacción de cada post,",
         "por red y por origen del texto."],
        "", "",
        [(k, f"{v:.2f} %", "#0891b2") for k, v in
         sorted(c["medias"].items())][:2]))

    # ── valor ──────────────────────────────────────────────────────────────
    for y, tit, ls in (
        (220, "Horas que no se pierden",
         ["Adaptar a mano cada pieza a cuatro", "redes consumía la semana."]),
        (460, "Nada sale sin revisar",
         ["Trabajando con menores, esto no", "es un detalle: es el requisito."]),
        (700, "Se sabe qué funciona",
         ["Y con qué texto. La siguiente", "campaña parte de datos."]),
    ):
        piezas.append(tarjeta(cx[4] + 20, y, cw[4] - 40, 175, tit, ls,
                              "VALOR", "#dcfce7"))

    piezas.append(f'<rect x="48" y="1090" width="{W - 96}" height="52" '
                  f'rx="12" fill="#e2e8f0"/>')
    piezas.append(_t(70, 1122, PIE, 13.5, "700"))

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d" '
           f'font-family="Segoe UI, Arial, sans-serif">'
           f'<title id="t">{escape(TITULO)}</title>'
           f'<desc id="d">{escape(BAJADA)}</desc>'
           '<defs>'
           '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">'
           '<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0f172a" '
           'flood-opacity="0.14"/></filter>'
           '<marker id="arrow" markerWidth="9" markerHeight="9" refX="7" '
           'refY="4.5" orient="auto"><path d="M0,0 L0,9 L8,4.5 z" '
           'fill="#334155"/></marker>'
           '</defs>' + "".join(piezas) + '</svg>')

    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "flujo.svg").write_text(svg, encoding="utf-8", newline="\n")
    print(f"  docs/flujo.svg  {len(svg) // 1024} KB · "
          f"{c['borradores']} borradores · {c['publicados']} publicados · "
          f"{c['rechazados']} rechazados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
