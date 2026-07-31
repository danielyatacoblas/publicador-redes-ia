"""Cola de aprobación y publicación programada.

Regla de oro del proyecto: **nada se publica sin aprobación humana**.
Este módulo hace cumplir esa regla en código, no solo en la documentación:
`publicar()` se niega a publicar cualquier post que no esté aprobado.

Estados posibles:

    borrador ──► pendiente ──┬─► aprobado ──► publicado
                             ├─► rechazado (con motivo)
                             └─► editado ──► pendiente (vuelve a revisión)

Un post publicado puede pasar a `fallido` si la API de la red devuelve error;
en ese caso queda listo para reintento y nunca se pierde en silencio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

ESTADOS = ("borrador", "pendiente", "aprobado", "rechazado", "publicado",
           "fallido")

MAX_REINTENTOS = 3


class ErrorAprobacion(Exception):
    """Se intentó publicar algo que no está aprobado."""


@dataclass
class ItemCola:
    id: str
    red: str
    tipo: str
    titulo: str
    texto: str
    fecha_programada: str
    origen: str = "plantillas"
    estado: str = "borrador"
    revisor: str = ""
    motivo: str = ""
    intentos: int = 0
    url_publicacion: str = ""
    historial: list[dict] = field(default_factory=list)

    def _log(self, accion: str, quien: str = "", detalle: str = ""):
        self.historial.append({
            "accion": accion, "quien": quien, "detalle": detalle,
            "estado": self.estado,
        })


class ColaAprobacion:
    """Gestiona el ciclo de vida de los posts. Sin dependencias externas:
    en producción cada método corresponde a una fila de Google Sheets."""

    def __init__(self):
        self.items: dict[str, ItemCola] = {}

    # ── alta ──
    def encolar(self, borrador) -> ItemCola:
        """Mete un borrador generado a la cola, en estado 'pendiente'."""
        clave = f"{borrador.id_contenido}:{borrador.red}"
        item = ItemCola(
            id=clave, red=borrador.red, tipo=borrador.tipo,
            titulo=borrador.titulo, texto=borrador.texto_completo,
            fecha_programada=borrador.fecha_programada, origen=borrador.origen,
            estado="pendiente")
        item._log("generado", detalle=f"motor={borrador.origen}")
        self.items[clave] = item
        return item

    # ── revisión humana ──
    def aprobar(self, clave: str, revisor: str) -> ItemCola:
        item = self._get(clave)
        if item.estado not in ("pendiente",):
            raise ErrorAprobacion(
                f"solo se puede aprobar lo que está pendiente (está '{item.estado}')")
        item.estado = "aprobado"
        item.revisor = revisor
        item._log("aprobado", revisor)
        return item

    def rechazar(self, clave: str, revisor: str, motivo: str) -> ItemCola:
        item = self._get(clave)
        item.estado = "rechazado"
        item.revisor = revisor
        item.motivo = motivo
        item._log("rechazado", revisor, motivo)
        return item

    def editar(self, clave: str, revisor: str, nuevo_texto: str) -> ItemCola:
        """El revisor corrige el texto: vuelve a 'pendiente' para segunda lectura."""
        item = self._get(clave)
        item.texto = nuevo_texto
        item.estado = "pendiente"
        item.origen = "humano"      # dejó de ser texto puro de IA
        item._log("editado", revisor)
        return item

    # ── publicación ──
    def publicar(self, clave: str, publicador=None, ahora: datetime | None = None) -> ItemCola:
        """Publica SOLO si está aprobado y ya llegó su fecha programada.

        `publicador` es una función (item) -> url que simula/realiza la
        llamada a la API de la red. Si lanza excepción, el item queda
        'fallido' y disponible para reintento.
        """
        item = self._get(clave)
        if item.estado != "aprobado":
            raise ErrorAprobacion(
                f"'{clave}' no está aprobado (estado '{item.estado}'): "
                "ningún post se publica sin revisión humana")

        ahora = ahora or datetime.now()
        if item.fecha_programada:
            try:
                programada = datetime.fromisoformat(item.fecha_programada)
                if ahora < programada:
                    item._log("pospuesto", detalle=f"programado para {item.fecha_programada}")
                    return item
            except ValueError:
                pass

        item.intentos += 1
        try:
            url = publicador(item) if publicador else f"https://demo.local/{item.id}"
            item.estado = "publicado"
            item.url_publicacion = url
            item._log("publicado", detalle=url)
        except Exception as e:                      # noqa: BLE001
            item.estado = "fallido"
            item.motivo = str(e)
            item._log("fallo", detalle=str(e))
        return item

    def reintentar_fallidos(self, publicador=None, ahora=None) -> list[ItemCola]:
        """Reintenta los fallidos que no agotaron los reintentos."""
        reintentados = []
        for item in self.items.values():
            if item.estado == "fallido" and item.intentos < MAX_REINTENTOS:
                item.estado = "aprobado"        # vuelve a estar listo
                reintentados.append(self.publicar(item.id, publicador, ahora))
        return reintentados

    # ── consultas ──
    def por_estado(self, estado: str) -> list[ItemCola]:
        return [i for i in self.items.values() if i.estado == estado]

    def listos_para_publicar(self, ahora: datetime) -> list[ItemCola]:
        salida = []
        for item in self.por_estado("aprobado"):
            if not item.fecha_programada:
                salida.append(item)
                continue
            try:
                if ahora >= datetime.fromisoformat(item.fecha_programada):
                    salida.append(item)
            except ValueError:
                salida.append(item)
        return salida

    def resumen(self) -> dict:
        r = {e: 0 for e in ESTADOS}
        for item in self.items.values():
            r[item.estado] += 1
        r["total"] = len(self.items)
        r["por_ia"] = sum(1 for i in self.items.values() if i.origen == "claude")
        r["editados_por_humano"] = sum(1 for i in self.items.values()
                                       if i.origen == "humano")
        return r

    def _get(self, clave: str) -> ItemCola:
        if clave not in self.items:
            raise KeyError(f"no existe el item '{clave}' en la cola")
        return self.items[clave]
