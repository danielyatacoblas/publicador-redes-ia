"""Tests del generador de borradores por red social."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.generador import (REDES, Borrador, fecha_legible,  # noqa: E402
                           generar_borradores, generar_con_plantillas,
                           validar_borrador)

ITEM = {
    "id": "C001",
    "tipo": "convocatoria",
    "titulo": "Taller de Robótica",
    "detalle": "Cuatro sesiones para construir y programar su primer robot.",
    "lugar": "Sede Villa El Salvador",
    "cupos": 24,
    "fecha": "2026-08-03T10:00",
}


# ── formato y reglas por red ────────────────────────────────────────────────

@pytest.mark.parametrize("red", list(REDES))
def test_genera_para_todas_las_redes(red):
    b = generar_con_plantillas(ITEM, red)
    assert b.red == red
    assert b.texto.strip()
    assert b.id_contenido == "C001"


@pytest.mark.parametrize("red", list(REDES))
def test_respeta_el_limite_de_caracteres(red):
    b = generar_con_plantillas(ITEM, red)
    assert b.largo <= REDES[red].max_caracteres, (
        f"{red}: {b.largo} > {REDES[red].max_caracteres}")


def test_linkedin_no_lleva_emojis():
    b = generar_con_plantillas(ITEM, "linkedin")
    assert not re.search(r"[\U0001F300-\U0001FAFF]", b.texto_completo)


def test_instagram_si_lleva_emojis():
    b = generar_con_plantillas(ITEM, "instagram")
    assert re.search(r"[\U0001F300-\U0001FAFF]", b.texto_completo)


def test_tiktok_es_el_mas_corto():
    largos = {red: generar_con_plantillas(ITEM, red).largo for red in REDES}
    assert largos["tiktok"] < largos["instagram"]
    assert largos["tiktok"] < largos["facebook"]


def test_cantidad_de_hashtags_por_red():
    for red, regla in REDES.items():
        b = generar_con_plantillas(ITEM, red)
        assert len(b.hashtags) <= regla.hashtags


# ── contenido correcto ──────────────────────────────────────────────────────

def test_incluye_datos_duros_de_la_convocatoria():
    b = generar_con_plantillas(ITEM, "instagram")
    texto = b.texto_completo
    assert "Robótica" in texto
    assert "24" in texto, "debe mencionar los cupos"
    assert "Villa El Salvador" in texto, "debe mencionar el lugar"
    assert "3 de agosto" in texto, "debe mencionar la fecha en formato legible"


def test_no_quedan_variables_de_plantilla_sin_reemplazar():
    for tipo in ("convocatoria", "testimonio", "tip_stem", "evento", "logro"):
        item = {**ITEM, "tipo": tipo}
        for red in REDES:
            b = generar_con_plantillas(item, red)
            assert "{" not in b.texto and "}" not in b.texto, f"{tipo}/{red}"


def test_fecha_legible_en_espanol():
    assert fecha_legible("2026-08-03T10:00") == "3 de agosto"
    assert fecha_legible("2026-12-25") == "25 de diciembre"
    assert fecha_legible("") == ""


def test_recorte_no_corta_palabras_a_la_mitad():
    largo = {**ITEM, "detalle": "Palabra " * 200}
    b = generar_con_plantillas(largo, "tiktok")
    # no debe terminar en media palabra sin marca de recorte
    assert b.texto.endswith(("…", ".", "!", "?")) or b.texto[-1].isalnum()
    assert b.largo <= REDES["tiktok"].max_caracteres


# ── validación ──────────────────────────────────────────────────────────────

def test_validador_acepta_borrador_correcto():
    b = generar_con_plantillas(ITEM, "instagram")
    ok, problemas = validar_borrador(b)
    assert ok, problemas


def test_validador_rechaza_texto_vacio():
    b = Borrador("C1", "instagram", "convocatoria", "t", "   ")
    ok, problemas = validar_borrador(b)
    assert not ok and "vacío" in " ".join(problemas)


def test_validador_rechaza_exceso_de_caracteres():
    b = Borrador("C1", "tiktok", "convocatoria", "t", "x" * 500)
    ok, problemas = validar_borrador(b)
    assert not ok and "excede" in " ".join(problemas)


def test_validador_rechaza_emojis_en_linkedin():
    b = Borrador("C1", "linkedin", "convocatoria", "t", "Hola 🚀")
    ok, problemas = validar_borrador(b)
    assert not ok and "emojis" in " ".join(problemas)


def test_validador_rechaza_variables_sin_reemplazar():
    b = Borrador("C1", "instagram", "convocatoria", "t", "Hola {titulo}")
    ok, problemas = validar_borrador(b)
    assert not ok and "variables" in " ".join(problemas)


# ── API pública ─────────────────────────────────────────────────────────────

def test_generar_borradores_respeta_las_redes_pedidas():
    bs = generar_borradores(ITEM, ["instagram", "tiktok"])
    assert [b.red for b in bs] == ["instagram", "tiktok"]


def test_red_no_soportada_lanza_error():
    with pytest.raises(ValueError, match="red no soportada"):
        generar_borradores(ITEM, ["threads"])


def test_todo_el_calendario_ficticio_genera_borradores_validos():
    import csv
    cal = ROOT / "data" / "calendario.csv"
    if not cal.exists():
        pytest.skip("corre antes: python scripts/generar_calendario.py")
    total = 0
    for fila in csv.DictReader(cal.open(encoding="utf-8")):
        fila["cupos"] = int(fila.get("cupos") or 0)
        redes = [r.strip() for r in fila["redes"].split(",")]
        for b in generar_borradores(fila, redes):
            ok, problemas = validar_borrador(b)
            assert ok, f"{fila['id']}/{b.red}: {problemas}"
            total += 1
    assert total >= 30, f"se esperaban 30+ borradores, hubo {total}"
