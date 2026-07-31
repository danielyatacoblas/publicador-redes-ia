#!/usr/bin/env python3
"""Construye los workflows de n8n del publicador de redes.

    python scripts/build_workflow.py

Genera dos workflows (el proceso está partido en dos a propósito, porque
entre generar y publicar hay una persona aprobando):

  workflow_1_generar.json   → calendario → prompts → Claude → cola de aprobación
  workflow_2_publicar.json  → cola aprobada → publicar multicanal → métricas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workflows" / "src"
OUT = ROOT / "workflows"

HOJA = "REEMPLAZAR_ID_HOJA"


def _node(nid, name, ntype, tv, pos, params, extra=None):
    n = {"parameters": params, "id": nid, "name": name, "type": ntype,
         "typeVersion": tv, "position": pos}
    if extra:
        n.update(extra)
    return n


def _cond(left, right, cid, op="equals"):
    return {
        "options": {"caseSensitive": False, "leftValue": "",
                    "typeValidation": "loose", "version": 2},
        "conditions": [{"id": cid, "leftValue": left, "rightValue": right,
                        "operator": {"type": "string", "operation": op}}],
        "combinator": "and",
    }


def build_generar(js_prompts: str) -> dict:
    nodes = [
        _node("cron-g", "Cada día 08:00", "n8n-nodes-base.scheduleTrigger", 1.2,
              [-280, 300],
              {"rule": {"interval": [{"field": "cronExpression",
                                      "expression": "0 8 * * *"}]}}),
        _node("gs-cal", "Calendario · Leer contenidos", "n8n-nodes-base.googleSheets", 4.5,
              [-60, 300],
              {"documentId": {"__rl": True, "value": HOJA, "mode": "id"},
               "sheetName": {"__rl": True, "value": "Calendario", "mode": "name"},
               "options": {}},
              {"notes": "Columnas: id,tipo,titulo,detalle,lugar,cupos,fecha,redes,objetivo"}),
        _node("if-pend", "¿Falta generarlo?", "n8n-nodes-base.if", 2,
              [160, 300],
              {"conditions": _cond("={{ $json.generado }}", "si", "cg", "notEquals"),
               "options": {}}),
        _node("code-p", "Preparar prompts por red", "n8n-nodes-base.code", 2,
              [380, 220], {"jsCode": js_prompts}),
        _node("claude", "Claude · Redactar borrador", "n8n-nodes-base.httpRequest", 4.2,
              [600, 220],
              {"method": "POST",
               "url": "https://api.anthropic.com/v1/messages",
               "sendHeaders": True,
               "headerParameters": {"parameters": [
                   {"name": "anthropic-version", "value": "2023-06-01"},
                   {"name": "content-type", "value": "application/json"}]},
               "sendBody": True,
               "specifyBody": "json",
               "jsonBody": "={{ JSON.stringify({ model: 'claude-sonnet-5', "
                           "max_tokens: 800, messages: [{ role: 'user', "
                           "content: $json.prompt }] }) }}",
               "options": {"batching": {"batch": {"batchSize": 3, "batchInterval": 1000}}}},
              {"notes": "Credencial: Header Auth con x-api-key = ANTHROPIC_API_KEY.\n"
                        "Sin API key, usar el motor de plantillas del repo."}),
        _node("code-fmt", "Armar fila de aprobación", "n8n-nodes-base.code", 2,
              [820, 220],
              {"jsCode": (
                  "// Une la respuesta de Claude con los metadatos del post\n"
                  "const salida = [];\n"
                  "const entradas = $('Preparar prompts por red').all();\n"
                  "$input.all().forEach((item, i) => {\n"
                  "  const meta = entradas[i] ? entradas[i].json : {};\n"
                  "  const bloques = item.json.content || [];\n"
                  "  const texto = bloques.filter((b) => b.type === 'text')\n"
                  "    .map((b) => b.text).join('').trim();\n"
                  "  salida.push({ json: {\n"
                  "    id_cola: meta.id_cola,\n"
                  "    id_contenido: meta.id_contenido,\n"
                  "    red: meta.red,\n"
                  "    tipo: meta.tipo,\n"
                  "    titulo: meta.titulo,\n"
                  "    texto: texto + (meta.cta ? '\\n\\n' + meta.cta : ''),\n"
                  "    largo: texto.length,\n"
                  "    excede_limite: texto.length > (meta.max_caracteres || 99999),\n"
                  "    fecha_programada: meta.fecha_programada,\n"
                  "    estado: 'pendiente',\n"
                  "    origen: 'claude',\n"
                  "    revisor: '',\n"
                  "  }});\n"
                  "});\n"
                  "return salida;\n")}),
        _node("gs-cola", "Cola · Agregar para aprobación", "n8n-nodes-base.googleSheets", 4.5,
              [1040, 220],
              {"operation": "append",
               "documentId": {"__rl": True, "value": HOJA, "mode": "id"},
               "sheetName": {"__rl": True, "value": "Aprobacion", "mode": "name"},
               "columns": {"mappingMode": "autoMapInputData", "value": {}},
               "options": {}}),
        _node("tg-aviso", "Avisar al equipo que hay borradores", "n8n-nodes-base.telegram", 1.2,
              [1260, 220],
              {"chatId": "REEMPLAZAR_CHAT_ID",
               "text": "=📝 Hay {{ $items().length }} borradores esperando "
                       "aprobación en la hoja. Nada se publica hasta que "
                       "alguien los revise.",
               "additionalFields": {}}),
    ]
    connections = {
        "Cada día 08:00": {"main": [[{"node": "Calendario · Leer contenidos", "type": "main", "index": 0}]]},
        "Calendario · Leer contenidos": {"main": [[{"node": "¿Falta generarlo?", "type": "main", "index": 0}]]},
        "¿Falta generarlo?": {"main": [[{"node": "Preparar prompts por red", "type": "main", "index": 0}], []]},
        "Preparar prompts por red": {"main": [[{"node": "Claude · Redactar borrador", "type": "main", "index": 0}]]},
        "Claude · Redactar borrador": {"main": [[{"node": "Armar fila de aprobación", "type": "main", "index": 0}]]},
        "Armar fila de aprobación": {"main": [[{"node": "Cola · Agregar para aprobación", "type": "main", "index": 0}]]},
        "Cola · Agregar para aprobación": {"main": [[{"node": "Avisar al equipo que hay borradores", "type": "main", "index": 0}]]},
    }
    return {"name": "Club STEM · 1. Generar borradores con IA",
            "nodes": nodes, "connections": connections,
            "settings": {"executionOrder": "v1"}, "pinData": {},
            "tags": [{"name": "club-stem"}, {"name": "redes"}]}


def build_publicar(js_filtrar: str) -> dict:
    nodes = [
        _node("cron-p", "Cada hora", "n8n-nodes-base.scheduleTrigger", 1.2,
              [-280, 300],
              {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}}),
        _node("gs-ap", "Cola · Leer aprobados", "n8n-nodes-base.googleSheets", 4.5,
              [-60, 300],
              {"documentId": {"__rl": True, "value": HOJA, "mode": "id"},
               "sheetName": {"__rl": True, "value": "Aprobacion", "mode": "name"},
               "options": {}}),
        _node("code-f", "Filtrar publicables", "n8n-nodes-base.code", 2,
              [160, 300], {"jsCode": js_filtrar},
              {"notes": "Solo pasa lo aprobado por una persona y con fecha cumplida"}),
        _node("sw-red", "Enrutar por red", "n8n-nodes-base.switch", 3,
              [380, 300],
              {"rules": {"values": [
                  {"conditions": _cond("={{ $json.red }}", "instagram", "r1"),
                   "renameOutput": True, "outputKey": "instagram"},
                  {"conditions": _cond("={{ $json.red }}", "facebook", "r2"),
                   "renameOutput": True, "outputKey": "facebook"},
                  {"conditions": _cond("={{ $json.red }}", "linkedin", "r3"),
                   "renameOutput": True, "outputKey": "linkedin"},
              ]},
               "options": {"fallbackOutput": "extra", "renameFallbackOutput": "otras"}}),
        _node("pub-ig", "Publicar · Instagram", "n8n-nodes-base.httpRequest", 4.2,
              [620, 60],
              {"method": "POST",
               "url": "=https://graph.facebook.com/v20.0/{{ $env.IG_USER_ID }}/media_publish",
               "sendBody": True, "specifyBody": "json",
               "jsonBody": "={{ JSON.stringify({ caption: $json.texto }) }}",
               "options": {}},
              {"onError": "continueErrorOutput",
               "notes": "Meta Graph API. Alternativa gratuita para demo: Buffer"}),
        _node("pub-fb", "Publicar · Facebook", "n8n-nodes-base.httpRequest", 4.2,
              [620, 220],
              {"method": "POST",
               "url": "=https://graph.facebook.com/v20.0/{{ $env.FB_PAGE_ID }}/feed",
               "sendBody": True, "specifyBody": "json",
               "jsonBody": "={{ JSON.stringify({ message: $json.texto }) }}",
               "options": {}},
              {"onError": "continueErrorOutput"}),
        _node("pub-li", "Publicar · LinkedIn", "n8n-nodes-base.linkedIn", 1,
              [620, 380],
              {"postAs": "organization",
               "organization": "REEMPLAZAR_ORG_ID",
               "text": "={{ $json.texto }}",
               "additionalFields": {}},
              {"onError": "continueErrorOutput"}),
        _node("noop-otras", "Otras redes (manual)", "n8n-nodes-base.noOp", 1,
              [620, 540], {}),
        _node("gs-upd", "Cola · Marcar publicado", "n8n-nodes-base.googleSheets", 4.5,
              [880, 220],
              {"operation": "update",
               "documentId": {"__rl": True, "value": HOJA, "mode": "id"},
               "sheetName": {"__rl": True, "value": "Aprobacion", "mode": "name"},
               "columns": {"mappingMode": "defineBelow", "matchingColumns": ["id_cola"],
                           "value": {"id_cola": "={{ $json.id_cola }}",
                                     "estado": "publicado",
                                     "publicado_en": "={{ $json.publicado_en }}"}},
               "options": {}}),
        _node("gs-err", "Registrar fallo para reintento", "n8n-nodes-base.googleSheets", 4.5,
              [880, 480],
              {"operation": "update",
               "documentId": {"__rl": True, "value": HOJA, "mode": "id"},
               "sheetName": {"__rl": True, "value": "Aprobacion", "mode": "name"},
               "columns": {"mappingMode": "defineBelow", "matchingColumns": ["id_cola"],
                           "value": {"id_cola": "={{ $json.id_cola }}",
                                     "estado": "fallido"}},
               "options": {}},
              {"notes": "El post NO se pierde: queda visible para reintento manual"}),
        _node("tg-err", "Avisar fallo al equipo", "n8n-nodes-base.telegram", 1.2,
              [1100, 480],
              {"chatId": "REEMPLAZAR_CHAT_ID",
               "text": "=⚠️ Falló la publicación de {{ $json.id_cola }}. "
                       "Queda en la cola para reintento.",
               "additionalFields": {}}),
    ]
    conn_pub = [{"node": "Cola · Marcar publicado", "type": "main", "index": 0}]
    conn_err = [{"node": "Registrar fallo para reintento", "type": "main", "index": 0}]
    connections = {
        "Cada hora": {"main": [[{"node": "Cola · Leer aprobados", "type": "main", "index": 0}]]},
        "Cola · Leer aprobados": {"main": [[{"node": "Filtrar publicables", "type": "main", "index": 0}]]},
        "Filtrar publicables": {"main": [[{"node": "Enrutar por red", "type": "main", "index": 0}]]},
        "Enrutar por red": {"main": [
            [{"node": "Publicar · Instagram", "type": "main", "index": 0}],
            [{"node": "Publicar · Facebook", "type": "main", "index": 0}],
            [{"node": "Publicar · LinkedIn", "type": "main", "index": 0}],
            [{"node": "Otras redes (manual)", "type": "main", "index": 0}],
        ]},
        "Publicar · Instagram": {"main": [conn_pub, conn_err]},
        "Publicar · Facebook": {"main": [conn_pub, conn_err]},
        "Publicar · LinkedIn": {"main": [conn_pub, conn_err]},
        "Registrar fallo para reintento": {"main": [[{"node": "Avisar fallo al equipo", "type": "main", "index": 0}]]},
    }
    return {"name": "Club STEM · 2. Publicar aprobados",
            "nodes": nodes, "connections": connections,
            "settings": {"executionOrder": "v1"}, "pinData": {},
            "tags": [{"name": "club-stem"}, {"name": "redes"}]}


def main():
    js_prompts = (SRC / "preparar_prompts.js").read_text(encoding="utf-8")
    js_filtrar = (SRC / "filtrar_publicables.js").read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre, wf in (("workflow_1_generar.json", build_generar(js_prompts)),
                       ("workflow_2_publicar.json", build_publicar(js_filtrar))):
        p = OUT / nombre
        p.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ {p.relative_to(ROOT)} — {len(wf['nodes'])} nodos")
    print("\nEl proceso está partido en dos workflows a propósito:")
    print("  entre generar y publicar hay una PERSONA aprobando.")


if __name__ == "__main__":
    main()
