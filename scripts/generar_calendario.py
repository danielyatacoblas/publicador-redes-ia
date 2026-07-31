#!/usr/bin/env python3
"""Genera el calendario de contenido ficticio (2 semanas) del Club STEM.

    python scripts/generar_calendario.py     # data/calendario.csv (14 contenidos)

Cada fila es un contenido a publicar: tipo, título, detalle, fecha, redes.
Reproducible (semilla fija) y sin datos reales de personas.
"""
from __future__ import annotations

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "calendario.csv"

random.seed(7)

CONTENIDOS = [
    ("convocatoria", "Taller de Robótica para niñas y niños de 8 a 12 años",
     "Cuatro sesiones para construir y programar su primer robot con piezas "
     "reutilizables. No se necesita experiencia previa ni computadora en casa.",
     "Sede Villa El Salvador", 24),
    ("tip_stem", "Haz un volcán con vinagre y bicarbonato",
     "Mezcla dos cucharadas de bicarbonato con vinagre y colorante. La reacción "
     "libera dióxido de carbono: la misma química que hace crecer los queques.",
     "", 0),
    ("testimonio", "Valeria, 11 años",
     "Antes pensaba que programar era muy difícil y solo para adultos. Ahora "
     "hice un juego y se lo enseñé a mi hermano menor.",
     "", 0),
    ("evento", "Feria Científica Escolar 2026",
     "Veinte proyectos creados por participantes del Club se exhibirán al "
     "público. Habrá demostraciones de robótica y un taller abierto para familias.",
     "Parque Zonal Huáscar", 0),
    ("logro", "Llegamos a 500 estudiantes en 2026",
     "Cerramos el primer semestre con 500 niñas y niños participando en "
     "nuestros programas, en cinco distritos de Lima Sur.",
     "", 0),
    ("convocatoria", "Programa de Voluntariado STEM",
     "Buscamos estudiantes y profesionales que quieran acompañar a los grupos "
     "los sábados. Capacitación inicial incluida.",
     "Modalidad mixta", 15),
    ("tip_stem", "Circuito simple con una pila y un foquito",
     "Con una pila, dos cables y un foco LED se entiende qué es un circuito "
     "cerrado. Si el foco no prende, revisa la polaridad del LED.",
     "", 0),
    ("evento", "Charla para familias: cómo acompañar la curiosidad",
     "Conversatorio gratuito sobre cómo responder a las preguntas de niñas y "
     "niños sin cortar su curiosidad, aunque no sepamos la respuesta.",
     "Virtual por Zoom", 0),
    ("testimonio", "Rosa, madre de familia",
     "Mi hijo llegaba a casa contando lo que había aprendido. Eso no pasaba "
     "antes con ningún curso.",
     "", 0),
    ("convocatoria", "Club de Programación con Scratch",
     "Ocho semanas creando juegos y animaciones. Para participantes de 9 a 14 "
     "años, con equipos disponibles en la sede.",
     "Sede Villa María del Triunfo", 20),
    ("tip_stem", "Mide la altura de tu casa con una sombra",
     "Con una regla, la sombra de un objeto conocido y una proporción se puede "
     "calcular la altura de cualquier cosa. Así midieron las pirámides.",
     "", 0),
    ("logro", "Nuestras egresadas ingresaron a carreras STEM",
     "Seis participantes del programa 2024 ingresaron este año a carreras de "
     "ingeniería y ciencias en universidades públicas.",
     "", 0),
    ("evento", "Jornada de puertas abiertas",
     "Ven a conocer los talleres, prueba las actividades y resuelve tus dudas "
     "con el equipo. Actividad libre para toda la familia.",
     "Sede Villa El Salvador", 0),
    ("tip_stem", "¿Por qué flota un barco de metal?",
     "No depende del peso sino de cuánta agua desplaza. Prueba con papel "
     "aluminio: en bolita se hunde, en forma de barquito flota.",
     "", 0),
]

REDES_POR_TIPO = {
    "convocatoria": "instagram,facebook,linkedin",
    "testimonio": "instagram,facebook",
    "tip_stem": "instagram,tiktok",
    "evento": "instagram,facebook,linkedin",
    "logro": "instagram,facebook,linkedin",
}


def main():
    inicio = datetime(2026, 8, 3, 10, 0)     # lunes
    filas = []
    for i, (tipo, titulo, detalle, lugar, cupos) in enumerate(CONTENIDOS):
        fecha = inicio + timedelta(days=i, hours=random.choice([0, 2, 5]))
        filas.append({
            "id": f"C{i+1:03d}",
            "tipo": tipo,
            "titulo": titulo,
            "detalle": detalle,
            "lugar": lugar,
            "cupos": cupos,
            "fecha": fecha.isoformat(timespec="minutes"),
            "redes": REDES_POR_TIPO[tipo],
            "objetivo": random.choice(["alcance", "inscripciones", "comunidad"]),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        wr.writeheader()
        wr.writerows(filas)

    total_posts = sum(len(f["redes"].split(",")) for f in filas)
    print(f"✓ {OUT.relative_to(ROOT)} — {len(filas)} contenidos "
          f"→ {total_posts} posts a generar")


if __name__ == "__main__":
    main()
