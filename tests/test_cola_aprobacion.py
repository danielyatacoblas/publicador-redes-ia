"""Tests de la cola de aprobación.

El test más importante del proyecto es
`test_no_se_puede_publicar_sin_aprobacion`: convierte la política de revisión
humana en una garantía verificable, no en una promesa del README.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cola_aprobacion import (ColaAprobacion, ErrorAprobacion,  # noqa: E402
                                 MAX_REINTENTOS)
from src.generador import generar_con_plantillas  # noqa: E402

ITEM = {
    "id": "C001", "tipo": "convocatoria", "titulo": "Taller de Robótica",
    "detalle": "Cuatro sesiones para construir un robot.",
    "lugar": "Sede VES", "cupos": 24, "fecha": "2026-08-03T10:00",
}
AHORA = datetime(2026, 8, 10, 12, 0)     # después de la fecha programada


def _cola_con_un_post():
    cola = ColaAprobacion()
    b = generar_con_plantillas(ITEM, "instagram")
    item = cola.encolar(b)
    return cola, item.id


# ── la regla de oro ─────────────────────────────────────────────────────────

def test_no_se_puede_publicar_sin_aprobacion():
    cola, clave = _cola_con_un_post()
    assert cola.items[clave].estado == "pendiente"
    with pytest.raises(ErrorAprobacion, match="revisión humana"):
        cola.publicar(clave, ahora=AHORA)
    assert cola.items[clave].estado == "pendiente", "no debe cambiar de estado"


def test_no_se_puede_publicar_un_rechazado():
    cola, clave = _cola_con_un_post()
    cola.rechazar(clave, "coordinacion", "fecha equivocada")
    with pytest.raises(ErrorAprobacion):
        cola.publicar(clave, ahora=AHORA)


def test_el_editado_vuelve_a_revision_y_no_se_publica_solo():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "coordinacion")
    cola.editar(clave, "coordinacion", "texto corregido")
    assert cola.items[clave].estado == "pendiente"
    with pytest.raises(ErrorAprobacion):
        cola.publicar(clave, ahora=AHORA)


# ── ciclo normal ────────────────────────────────────────────────────────────

def test_ciclo_completo_hasta_publicado():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "coordinacion")
    item = cola.publicar(clave, ahora=AHORA)
    assert item.estado == "publicado"
    assert item.url_publicacion
    assert item.revisor == "coordinacion"


def test_editar_marca_el_origen_como_humano():
    cola, clave = _cola_con_un_post()
    assert cola.items[clave].origen == "plantillas"
    cola.editar(clave, "coordinacion", "texto nuevo")
    assert cola.items[clave].origen == "humano"


def test_historial_registra_cada_paso():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")
    cola.publicar(clave, ahora=AHORA)
    acciones = [h["accion"] for h in cola.items[clave].historial]
    assert acciones == ["generado", "aprobado", "publicado"]


def test_aprobar_dos_veces_falla():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")
    with pytest.raises(ErrorAprobacion):
        cola.aprobar(clave, "ana")


# ── programación por fecha ──────────────────────────────────────────────────

def test_no_publica_antes_de_la_fecha_programada():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")
    antes = datetime(2026, 8, 1, 9, 0)      # antes del 3 de agosto
    item = cola.publicar(clave, ahora=antes)
    assert item.estado == "aprobado", "debe quedar esperando su fecha"
    assert item.historial[-1]["accion"] == "pospuesto"


def test_listos_para_publicar_filtra_por_fecha():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")
    assert cola.listos_para_publicar(datetime(2026, 8, 1)) == []
    assert len(cola.listos_para_publicar(AHORA)) == 1


# ── fallos y reintentos ─────────────────────────────────────────────────────

def test_fallo_de_api_deja_el_item_en_fallido_no_en_publicado():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")

    def publicador_roto(item):
        raise RuntimeError("503 rate limit")

    item = cola.publicar(clave, publicador_roto, AHORA)
    assert item.estado == "fallido"
    assert "503" in item.motivo
    assert item.url_publicacion == "", "no debe simular una URL falsa"


def test_reintento_recupera_una_publicacion_fallida():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")
    intentos = {"n": 0}

    def falla_una_vez(item):
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise RuntimeError("timeout")
        return "https://instagram.com/p/ok"

    cola.publicar(clave, falla_una_vez, AHORA)
    assert cola.items[clave].estado == "fallido"
    cola.reintentar_fallidos(falla_una_vez, AHORA)
    assert cola.items[clave].estado == "publicado"


def test_no_reintenta_infinitamente():
    cola, clave = _cola_con_un_post()
    cola.aprobar(clave, "ana")

    def siempre_falla(item):
        raise RuntimeError("caido")

    cola.publicar(clave, siempre_falla, AHORA)
    for _ in range(10):
        cola.reintentar_fallidos(siempre_falla, AHORA)
    assert cola.items[clave].intentos <= MAX_REINTENTOS


# ── resumen ─────────────────────────────────────────────────────────────────

def test_resumen_cuenta_por_estado_y_origen():
    cola = ColaAprobacion()
    for red in ("instagram", "facebook", "linkedin"):
        cola.encolar(generar_con_plantillas(ITEM, red))
    claves = list(cola.items)
    cola.aprobar(claves[0], "ana")
    cola.publicar(claves[0], ahora=AHORA)
    cola.rechazar(claves[1], "ana", "no aplica")

    r = cola.resumen()
    assert r["total"] == 3
    assert r["publicado"] == 1
    assert r["rechazado"] == 1
    assert r["pendiente"] == 1
