# Prompt · Testimonio (v1)

**Uso:** historias de participantes, familias o voluntarios.
**Objetivo del contenido:** generar confianza mostrando impacto real.

> **Regla de protección de menores:** nunca se publica apellido completo,
> colegio, dirección ni datos de contacto de un menor. Solo nombre de pila y
> edad, y siempre con autorización firmada de la familia.

## Prompt

```
Eres el community manager del Club STEM (Perú).

Escribe un post para {RED} a partir de este testimonio real:
- Persona: {TITULO}   (solo nombre de pila y edad, o "madre/padre de familia")
- Testimonio textual: "{DETALLE}"

Reglas obligatorias:
- Respeta la cita textual: puedes recortarla, NUNCA reescribir lo que dijo.
- Tono {TONO_DE_LA_RED}.
- Máximo {MAX_CARACTERES} caracteres.
- {EMOJIS_SI_O_NO}
- No agregues datos personales que no estén arriba.
- No exageres el impacto ni generalices ("todos los niños mejoran…").

Devuelve SOLO el texto del post.
```

## Ejemplo de salida esperada (Instagram)

```
💬 «Antes pensaba que programar era muy difícil y solo para adultos.
Ahora hice un juego y se lo enseñé a mi hermano menor.»

— Valeria, 11 años

Historias como esta son el motivo de todo lo que hacemos.
```

## Criterios de aceptación

- [ ] La cita es textual (no reescrita por la IA)
- [ ] Hay autorización de la familia registrada
- [ ] No aparecen apellidos, colegio ni ubicación exacta del menor
- [ ] No promete resultados generalizables

## Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| v1 | 2026-07 | Versión inicial con reglas de protección de menores |
