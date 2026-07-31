# 02 · Publicador de redes con IA — idea → borrador → aprobación → multicanal

[![tests](https://img.shields.io/badge/tests-44%20passed-brightgreen)](tests/)
[![n8n](https://img.shields.io/badge/n8n-2%20workflows-orange)](workflows/)
[![IA](https://img.shields.io/badge/IA-Claude%20(opcional)-8A63D2)](prompts/)
[![licencia](https://img.shields.io/badge/licencia-MIT-blue)](LICENSE)

**Qué requisitos del aviso cubre:** automatizar la programación y publicación de contenido en
redes · flujos que conectan **creación de contenido con publicación
multicanal** · implementar **IA generativa** en flujos internos.

---

## 🎬 Qué hace

```
Calendario de contenido (Google Sheets)
        │  (n8n, cada día 08:00)
        ▼
  Genera 1 borrador POR RED con reglas propias de cada una
  (largo, tono, emojis, hashtags, CTA)   ← Claude o plantillas
        ▼
  ┌──────── COLA DE APROBACIÓN ────────┐
  │  una persona: ✅ aprueba           │   ⛔ nada se publica
  │               ✏️ edita → revisión   │      sin este paso
  │               ❌ rechaza (con motivo)│
  └──────────────┬─────────────────────┘
                 ▼  (solo lo aprobado, en su fecha)
   Instagram · Facebook · LinkedIn · TikTok
                 │
                 ├─ falla la API → estado "fallido" + reintento + aviso
                 └─ 24 h después → métricas de vuelta → KPIs (proyecto 03)
```

### La regla de oro, implementada en código

`ColaAprobacion.publicar()` **lanza excepción** si el post no fue aprobado por
una persona, y el nodo n8n aplica el mismo filtro. Hay tests para ambos:

```python
def test_no_se_puede_publicar_sin_aprobacion():
    with pytest.raises(ErrorAprobacion, match="revisión humana"):
        cola.publicar(clave)
```

---

## ⚡ Probarlo en 2 minutos (sin API key ni n8n)

```bash
pip install pytest
python scripts/generar_calendario.py       # 14 contenidos ficticios
python scripts/simular_publicacion.py      # ciclo completo end-to-end
python -m pytest tests/ -v                 # 44 tests
```

Salida real:

```
Motor de generación: plantillas
Contenidos del calendario: 14
Borradores generados y válidos: 36

Revisión humana (obligatoria antes de publicar):
  ✓ aprobados directo: 27
  ✏ editados y aprobados: 5
  ✗ rechazados: 4

⚠ 4 publicaciones fallaron → reintento automático

Publicación:
  ✓ publicados: 32
  ⚠ fallidos tras reintentos: 0
  · rechazados (nunca se publican): 4

Tasa de interacción por origen del texto:
  humano       5.30 %  (5 posts)
  plantillas   5.95 %  (27 posts)
```

> Ese último bloque responde a *"proponer mejoras a qué métricas se están
> midiendo"*: medir si el contenido generado por IA rinde mejor o peor que el
> editado por humanos permite decidir con datos, no con opinión.

### Con Claude (opcional)

```bash
pip install anthropic
set ANTHROPIC_API_KEY=sk-ant-...        # Windows (o export en Linux/Mac)
python scripts/simular_publicacion.py --motor claude
```

Sin API key el sistema **funciona igual** con el motor de plantillas: eso hace
que cualquiera pueda evaluar el repo sin gastar un sol.

---

## 🎨 Ejemplo real de salida (mismo contenido, 3 redes)

**Instagram** (2200 car., emojis, 8 hashtags):
```
🚀 ¡Abrimos inscripciones para Taller de Robótica para niñas y niños de 8 a 12 años!

Cuatro sesiones para construir y programar su primer robot con piezas
reutilizables. No se necesita experiencia previa ni computadora en casa.

📅 3 de agosto   📍 Sede Villa El Salvador
Cupos limitados: 24 niñas y niños.

Escríbenos por DM 📩

#ClubSTEM #EducacionSTEM #Peru #Inscripciones #TalleresSTEM #Robotica …
```

**LinkedIn** (sin emojis, tono institucional, 3 hashtags):
```
Abrimos convocatoria para Taller de Robótica para niñas y niños de 8 a 12 años.

Cuatro sesiones para construir y programar su primer robot con piezas
reutilizables. No se necesita experiencia previa ni computadora en casa.

Este programa forma parte de nuestro compromiso con el acceso equitativo a
la educación STEM en el Perú.

Conversemos sobre alianzas

#ClubSTEM #EducacionSTEM #Peru
```

**TikTok** (300 car., hook directo, corta en frase completa):
```
¿Taller de Robótica para niñas y niños de 8 a 12 años? 👀 Sí, y es gratis.
Cuatro sesiones para construir y programar su primer robot con piezas reutilizables.

Link en bio 🔗

#ClubSTEM #EducacionSTEM #Peru #Inscripciones #TalleresSTEM
```

---

## 🐳 Con n8n de verdad

```bash
docker compose up -d          # http://localhost:5678
```

Importa los dos workflows de `workflows/`:

| Workflow | Nodos | Qué hace |
| --- | --- | --- |
| `workflow_1_generar.json` | 8 | Calendario → prompts por red → Claude → cola de aprobación → aviso al equipo |
| `workflow_2_publicar.json` | 11 | Lee aprobados → filtra → publica en IG/FB/LinkedIn → marca estado → maneja fallos |

**Están partidos en dos a propósito**: entre generar y publicar hay una
persona. Un solo workflow "todo automático" sería justamente lo que la
política prohíbe.

Configurar antes de activar: `REEMPLAZAR_ID_HOJA`, `REEMPLAZAR_CHAT_ID`,
`REEMPLAZAR_ORG_ID` y la credencial Header Auth con `x-api-key` para Claude.

---

## 📁 Estructura

```
02_publicador_redes_ia/
├── src/
│   ├── generador.py           # reglas por red + motores plantillas/Claude
│   └── cola_aprobacion.py     # estados, revisión humana, reintentos
├── workflows/
│   ├── src/preparar_prompts.js     # arma el prompt por red
│   ├── src/filtrar_publicables.js  # la regla de oro dentro de n8n
│   ├── workflow_1_generar.json
│   └── workflow_2_publicar.json
├── prompts/                   # prompts versionados con criterios de aceptación
│   ├── v1_convocatoria.md
│   ├── v1_testimonio.md       # incluye reglas de protección de menores
│   └── v1_tip_stem.md
├── scripts/
│   ├── generar_calendario.py  # 14 contenidos ficticios reproducibles
│   ├── simular_publicacion.py # ciclo completo end-to-end
│   └── build_workflow.py
├── tests/                     # 44 tests
├── POLITICA_REVISION.md       # checklist del aprobador y roles
└── docker-compose.yml
```

---

## 🧪 Qué está probado

| Área | Tests |
| --- | --- |
| Reglas por red | Límite de caracteres, emojis solo donde corresponde, TikTok es el más corto |
| Contenido | Incluye fecha/lugar/cupos, nunca deja variables `{}` sin reemplazar |
| Recorte | No corta palabras a la mitad; prefiere cerrar en frase completa |
| **Aprobación** | **No se puede publicar sin aprobación, ni rechazado, ni editado sin re-revisión** |
| Programación | No publica antes de la fecha; sí cuando llega |
| Fallos | Un error de API deja `fallido` (no `publicado`), reintenta hasta 3 veces |
| Trazabilidad | El historial registra generado → aprobado → publicado con quién y cuándo |
| **Nodo n8n** | El filtro del workflow bloquea pendientes, rechazados y aprobados sin revisor |

---

## 🔐 Decisiones de diseño

- **Funciona sin API key** (motor de plantillas): evaluable sin costo.
- **Prompts versionados** con criterios de aceptación y reglas de protección
  de menores, no sueltos dentro del código.
- **Origen marcado** (`claude` / `humano`) para medir qué contenido rinde mejor.
- **Nada se pierde en silencio**: los fallos quedan visibles y con aviso.
- **Sin secretos en el repo**: las API keys van en el credential store de n8n.

---

## 📌 Estado

✅ **Funcional y probado en local.** 44 tests en verde, dos workflows n8n
importables, data ficticia incluida y prompts listos para usar con Claude.
