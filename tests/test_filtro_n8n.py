"""Verifica que el nodo n8n que decide qué se publica respete la MISMA regla
de oro que la cola de Python: sin aprobación humana, no se publica.

Si alguien relaja el filtro del workflow, este test falla — aunque el código
Python siga correcto.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tests" / "correr_filtro_js.mjs"

AYER = (datetime.now() - timedelta(days=1)).isoformat(timespec="minutes")
MANANA = (datetime.now() + timedelta(days=1)).isoformat(timespec="minutes")


def _filtrar(items: list[dict]) -> list[str]:
    proc = subprocess.run(
        ["node", str(RUNNER), json.dumps(items, ensure_ascii=False)],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    if proc.returncode != 0:
        pytest.fail(f"el nodo JS falló:\n{proc.stderr}")
    return json.loads(proc.stdout)


pytestmark = pytest.mark.skipif(shutil.which("node") is None,
                                reason="Node.js no está instalado")


def test_deja_pasar_lo_aprobado_y_vencido():
    items = [{"id_cola": "C1:instagram", "estado": "aprobado",
              "revisor": "coordinacion", "fecha_programada": AYER}]
    assert _filtrar(items) == ["C1:instagram"]


def test_bloquea_lo_pendiente():
    items = [{"id_cola": "C2:instagram", "estado": "pendiente",
              "revisor": "", "fecha_programada": AYER}]
    assert _filtrar(items) == []


def test_bloquea_lo_rechazado():
    items = [{"id_cola": "C3:facebook", "estado": "rechazado",
              "revisor": "coordinacion", "fecha_programada": AYER}]
    assert _filtrar(items) == []


def test_bloquea_aprobado_sin_revisor_registrado():
    """Aprobado pero sin constancia de quién aprobó: no pasa (trazabilidad)."""
    items = [{"id_cola": "C4:linkedin", "estado": "aprobado",
              "revisor": "  ", "fecha_programada": AYER}]
    assert _filtrar(items) == []


def test_respeta_la_fecha_programada():
    items = [{"id_cola": "C5:instagram", "estado": "aprobado",
              "revisor": "ana", "fecha_programada": MANANA}]
    assert _filtrar(items) == []


def test_publica_sin_fecha_programada():
    items = [{"id_cola": "C6:tiktok", "estado": "aprobado",
              "revisor": "ana", "fecha_programada": ""}]
    assert _filtrar(items) == ["C6:tiktok"]


def test_filtra_correctamente_un_lote_mixto():
    items = [
        {"id_cola": "A:instagram", "estado": "aprobado", "revisor": "ana", "fecha_programada": AYER},
        {"id_cola": "B:instagram", "estado": "pendiente", "revisor": "", "fecha_programada": AYER},
        {"id_cola": "C:facebook", "estado": "aprobado", "revisor": "ana", "fecha_programada": MANANA},
        {"id_cola": "D:linkedin", "estado": "rechazado", "revisor": "ana", "fecha_programada": AYER},
        {"id_cola": "E:tiktok", "estado": "APROBADO", "revisor": "luis", "fecha_programada": AYER},
    ]
    assert _filtrar(items) == ["A:instagram", "E:tiktok"], (
        "solo deben pasar los aprobados con revisor y fecha cumplida "
        "(el estado no distingue mayúsculas)")
