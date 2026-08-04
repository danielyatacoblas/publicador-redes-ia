#!/usr/bin/env python3
"""Simula el ciclo completo: calendario → borradores IA → aprobación → publicación.

    python scripts/generar_calendario.py
    python scripts/simular_publicacion.py                 # motor plantillas (offline)
    python scripts/simular_publicacion.py --motor claude  # usa ANTHROPIC_API_KEY

Salidas:
    data/borradores.csv       ← lo que vería el equipo en la hoja de aprobación
    data/publicados.csv       ← posts publicados con su URL
    data/metricas.csv         ← alcance simulado 24 h después (alimenta el KPI)
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cola_aprobacion import ColaAprobacion  # noqa: E402
from src.generador import generar_borradores, validar_borrador  # noqa: E402

CAL = ROOT / "data" / "calendario.csv"
DATA = ROOT / "data"

random.seed(11)


def publicador_simulado(item):
    """Simula la API de la red social: 1 de cada 12 publicaciones falla."""
    if random.random() < 1 / 12:
        raise RuntimeError(f"API de {item.red} respondió 503 (rate limit)")
    slug = item.id.replace(":", "-").lower()
    return f"https://{item.red}.com/clubstem/posts/{slug}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", default="plantillas",
                    choices=["plantillas", "claude"])
    args = ap.parse_args()

    if not CAL.exists():
        raise SystemExit("Primero corre: python scripts/generar_calendario.py")

    calendario = list(csv.DictReader(CAL.open(encoding="utf-8")))
    cola = ColaAprobacion()

    # ── 1. Generación de borradores ──
    invalidos = []
    for item in calendario:
        item["cupos"] = int(item.get("cupos") or 0)
        redes = [r.strip() for r in item["redes"].split(",") if r.strip()]
        for b in generar_borradores(item, redes, motor=args.motor):
            ok, problemas = validar_borrador(b)
            if not ok:
                invalidos.append((b.id_contenido, b.red, problemas))
                continue
            cola.encolar(b)

    print("=== Publicador de redes con IA (simulación local) ===\n")
    print(f"Motor de generación: {args.motor}")
    print(f"Contenidos del calendario: {len(calendario)}")
    print(f"Borradores generados y válidos: {len(cola.items)}")
    if invalidos:
        print(f"   descartados por validación: {len(invalidos)}")
        for cid, red, probs in invalidos[:3]:
            print(f"    · {cid}/{red}: {', '.join(probs)}")

    # ── 2. Revisión humana (simulada: el equipo revisa la cola) ──
    aprobados = rechazados = editados = 0
    for clave in list(cola.items):
        dado = random.random()
        if dado < 0.08:
            cola.rechazar(clave, "coordinacion", "no encaja con la línea editorial")
            rechazados += 1
        elif dado < 0.20:
            item = cola.items[clave]
            cola.editar(clave, "coordinacion", item.texto + "\n\n(revisado por el equipo)")
            cola.aprobar(clave, "coordinacion")
            editados += 1
            aprobados += 1
        else:
            cola.aprobar(clave, "coordinacion")
            aprobados += 1

    print(f"\nRevisión humana (obligatoria antes de publicar):")
    print(f"  ✓ aprobados directo: {aprobados - editados}")
    print(f"   editados y aprobados: {editados}")
    print(f"  ✗ rechazados: {rechazados}")

    # ── 3. Publicación programada ──
    # "Hoy" = final del calendario, para que todas las fechas ya hayan llegado.
    ahora = max(datetime.fromisoformat(i["fecha"]) for i in calendario) + timedelta(days=1)
    listos = cola.listos_para_publicar(ahora)
    for item in listos:
        cola.publicar(item.id, publicador_simulado, ahora)

    fallidos = cola.por_estado("fallido")
    if fallidos:
        print(f"\n {len(fallidos)} publicaciones fallaron → reintento automático")
        cola.reintentar_fallidos(publicador_simulado, ahora)

    res = cola.resumen()
    print(f"\nPublicación:")
    print(f"  ✓ publicados: {res['publicado']}")
    print(f"   fallidos tras reintentos: {res['fallido']}")
    print(f"  · rechazados (nunca se publican): {res['rechazado']}")

    # ── 4. Métricas 24 h después (alimentan el dashboard del proyecto 03) ──
    publicados = cola.por_estado("publicado")
    metricas = []
    for item in publicados:
        base = {"instagram": 900, "facebook": 600, "linkedin": 350, "tiktok": 1500}[item.red]
        alcance = int(base * random.uniform(0.5, 1.9))
        interacciones = int(alcance * random.uniform(0.02, 0.09))
        metricas.append({
            "id": item.id, "red": item.red, "tipo": item.tipo,
            "fecha": item.fecha_programada, "origen": item.origen,
            "alcance": alcance, "interacciones": interacciones,
            "tasa_interaccion": round(100 * interacciones / alcance, 2),
        })

    DATA.mkdir(parents=True, exist_ok=True)
    _csv(DATA / "borradores.csv",
         [{"id": i.id, "red": i.red, "tipo": i.tipo, "estado": i.estado,
           "origen": i.origen, "revisor": i.revisor, "motivo": i.motivo,
           "fecha_programada": i.fecha_programada,
           "texto": i.texto.replace("\n", " ⏎ ")}
          for i in cola.items.values()])
    _csv(DATA / "publicados.csv",
         [{"id": i.id, "red": i.red, "fecha": i.fecha_programada,
           "url": i.url_publicacion, "intentos": i.intentos}
          for i in publicados])
    _csv(DATA / "metricas.csv", metricas)

    # comparativa IA vs humano (métrica que el aviso pide "proponer")
    if metricas:
        por_origen = {}
        for m in metricas:
            por_origen.setdefault(m["origen"], []).append(m["tasa_interaccion"])
        print("\nTasa de interacción por origen del texto:")
        for origen, vals in sorted(por_origen.items()):
            print(f"  {origen:<12} {sum(vals)/len(vals):.2f} %  ({len(vals)} posts)")

    print(f"\n✓ {(DATA/'borradores.csv').relative_to(ROOT)} "
          f"({len(cola.items)} filas — así lo ve el equipo)")
    print(f"✓ {(DATA/'publicados.csv').relative_to(ROOT)} ({len(publicados)} filas)")
    print(f"✓ {(DATA/'metricas.csv').relative_to(ROOT)} ({len(metricas)} filas)")


def _csv(path: Path, filas: list[dict]):
    if not filas:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        wr.writeheader()
        wr.writerows(filas)


if __name__ == "__main__":
    main()
