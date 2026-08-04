<h1 align="center">Publicador de redes con IA</h1>

<p align="center"><i>La IA redacta, una persona aprueba, el sistema publica</i></p>

<p align="center">![tests](https://img.shields.io/badge/tests-44%20passed-brightgreen) ![n8n](https://img.shields.io/badge/n8n-2%20workflows-EA4B71) ![IA](https://img.shields.io/badge/IA-Claude%20(opcional)-8A63D2) ![licencia](https://img.shields.io/badge/licencia-MIT-blue)</p>

---

## 🎥 Demo en video

<!-- ────────────────────────────────────────────────────────────────────
     ESPACIO RESERVADO PARA EL VIDEO

     Cuando lo tengas subido a YouTube (recomiendo "no listado"), reemplaza
     este bloque por la miniatura clickeable:

     [![Ver la demo](https://img.youtube.com/vi/TU_VIDEO_ID/maxresdefault.jpg)](https://youtu.be/TU_VIDEO_ID)

     Y borra el aviso de abajo.
     ──────────────────────────────────────────────────────────────────── -->

> 🎬 *Video de la demo en camino.* Mientras tanto, el proyecto corre completo
> en local en menos de dos minutos siguiendo [⚡ Probarlo](#-probarlo-en-2-minutos).

---

## 🎯 El problema

Adaptar cada pieza de contenido a Instagram, Facebook, LinkedIn y TikTok —con su largo, su tono y sus hashtags— consume horas por semana. Automatizarlo del todo tampoco sirve: publicar sin revisar, en nombre de una organización que trabaja con menores, es inaceptable.

## 💡 Qué hace este proyecto

1. **Un borrador por red**, con las reglas propias de cada una: LinkedIn sin emojis y tono institucional, TikTok corto y directo, Instagram con sus hashtags.
2. **Cola de aprobación**: una persona aprueba, edita o rechaza. Lo editado vuelve a revisión.
3. **Publicación programada** multicanal, solo de lo aprobado y en su fecha.
4. **Nada se pierde en silencio**: si la API de una red falla, el post queda marcado y se reintenta, con aviso al equipo.
5. **Mide qué funciona**: compara el rendimiento del texto de IA contra el editado por humanos.

---

## 🗺️ Cómo funciona

```mermaid
flowchart TD
    C["🗓️ Calendario de contenido<br/>Google Sheets"] -->|cada día 08:00| P
    P["🤖 Claude redacta<br/>un borrador por red"] --> Q
    subgraph Q ["📋 Cola de aprobación"]
        R{"Revisión<br/>humana"}
    end
    R -->|❌ rechaza| Z["Nunca se publica<br/>queda el motivo"]
    R -->|✏️ edita| R
    R -->|✅ aprueba| S{"¿Llegó su<br/>fecha?"}
    S -->|todavía no| T["⏳ Espera"]
    S -->|sí| U["📱 Instagram · Facebook · LinkedIn"]
    U -->|error de API| V["⚠️ Marcado como fallido<br/>reintento + aviso"]
    U -->|24 h después| W["📊 Métricas de vuelta<br/>al dashboard"]
```

---

## ⚡ Probarlo en 2 minutos

```bash
pip install pytest
python scripts/generar_calendario.py    # 14 contenidos ficticios
python scripts/simular_publicacion.py   # el ciclo completo end-to-end
python -m pytest -v                     # 44 tests
```

Funciona **sin API key**: trae un motor de plantillas equivalente. Con
`ANTHROPIC_API_KEY` usa Claude de verdad (`--motor claude`).

---

### 🔒 La regla de oro está en el código, no en el README

```python
def test_no_se_puede_publicar_sin_aprobacion():
    with pytest.raises(ErrorAprobacion, match="revisión humana"):
        cola.publicar(clave)
```

`publicar()` lanza excepción si el post no fue aprobado por una persona, y el nodo de n8n aplica exactamente el mismo filtro. Hay tests para ambos: una promesa en la documentación se puede olvidar, un test no.

---

## 📁 Estructura

```
├── src/
│   ├── generador.py           # reglas por red + motores plantillas/Claude
│   └── cola_aprobacion.py     # estados, revisión humana, reintentos
├── workflows/
│   ├── workflow_1_generar.json   # calendario → Claude → cola
│   └── workflow_2_publicar.json  # aprobados → redes → métricas
├── prompts/                   # prompts versionados
├── scripts/                   # data ficticia y simulación
└── tests/                     # 44 tests
```

---

## 🌿 Flujo de trabajo con Git

El repositorio sigue **Git Flow**: `main` siempre desplegable, `develop` como
integración, y una rama por cambio. Los merges son `--no-ff` para que cada
funcionalidad quede como un bloque legible en el historial, y cada versión
lleva su tag.

```mermaid
gitGraph
   commit id: "chore: repo setup"
   branch develop
   checkout develop
   branch feature/core
   commit id: "feat: core logic"
   checkout develop
   merge feature/core
   branch feature/tests
   commit id: "test: suite"
   checkout develop
   merge feature/tests
   checkout main
   merge develop tag: "v1.0.0"
   checkout develop
   branch fix/review
   commit id: "fix: review findings"
   checkout develop
   merge fix/review
   checkout main
   merge develop tag: "v1.1.0"
```

| Rama | Para qué |
| --- | --- |
| `main` | Solo versiones liberadas. Cada merge lleva su tag. |
| `develop` | Integración de todo lo terminado. |
| `feature/*` | Una funcionalidad nueva. |
| `fix/*` | Una corrección concreta. |
| `release/*` | Preparación de la versión, luego se fusiona a `main` y `develop`. |

Los mensajes siguen [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `test:`, `docs:`, `chore:` — con el porqué del cambio en el
cuerpo, no solo el qué.

---

## 📚 Documentación

| Documento | Contenido |
| --- | --- |
| [`GUIA.md`](GUIA.md) | Guía técnica completa: arquitectura, decisiones, configuración y puesta en marcha |
| [`POLITICA_REVISION.md`](POLITICA_REVISION.md) | Checklist del aprobador, roles y qué NO se automatiza a propósito |
| [`prompts/`](prompts/) | Prompts versionados con criterios de aceptación y reglas de protección de menores |

---

## 📄 Licencia

[MIT](LICENSE) · Daniel Yataco Blas

> Proyecto de demostración construido con **datos ficticios**. No es un sistema
> en producción de ninguna organización.
