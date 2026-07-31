# Política de revisión — nada se publica sin aprobación humana

Esta no es una recomendación: está **implementada en el código**.
`ColaAprobacion.publicar()` lanza `ErrorAprobacion` si el post no fue aprobado
por una persona, y hay un test que lo verifica
(`test_no_se_puede_publicar_sin_aprobacion`).

---

## 1. Por qué

La IA redacta rápido y bien, pero **no sabe** cuándo cambió una fecha, cuándo
una familia retiró su autorización, ni cuándo un dato científico está mal.
Publicar en nombre de una organización que trabaja con menores exige que una
persona responda por cada pieza publicada.

---

## 2. El circuito

```
Generado por IA ──► PENDIENTE ──┬──► APROBADO ──► publicado (programado)
   (cola)                       │
                                ├──► EDITADO ──► vuelve a PENDIENTE
                                │              (segunda lectura obligatoria)
                                └──► RECHAZADO (con motivo, nunca se publica)
```

Un post **editado** vuelve a la cola y cambia su `origen` a `humano`: así
sabemos qué porcentaje del contenido salió puro de IA y podemos medir su
rendimiento por separado.

---

## 3. Checklist del aprobador (30 segundos por post)

| # | Qué revisar | Por qué |
| --- | --- | --- |
| 1 | **Datos duros**: fecha, hora, lugar, cupos, precio | Es el error más frecuente y el más caro |
| 2 | **Menores**: sin apellidos, colegio ni ubicación exacta | Protección de datos de niñas y niños |
| 3 | **Autorización**: ¿la familia firmó para este uso? | Requisito legal y ético |
| 4 | **Veracidad científica**: ¿el tip es correcto? | La IA puede sonar segura y estar equivocada |
| 5 | **Promesas**: nada de "garantizado" ni resultados asegurados | Credibilidad de la organización |
| 6 | **Tono**: ¿suena al Club o suena a robot? | Identidad de marca |
| 7 | **CTA**: ¿queda claro qué hacer después? | Es lo que convierte |

Si algo del 1 al 5 falla → **rechazar**, no editar. Que vuelva a generarse
con los datos corregidos en el calendario.

---

## 4. Roles

| Rol | Puede | No puede |
| --- | --- | --- |
| Generador (automatizado) | Crear borradores en estado `pendiente` | Publicar |
| Coordinación de comunicaciones | Aprobar, editar, rechazar | Saltarse la revisión |
| Sistema (n8n) | Publicar lo aprobado en su fecha, reintentar fallos | Aprobar por su cuenta |

---

## 5. Trazabilidad

Cada post guarda su `historial`: quién lo generó, quién lo revisó, si fue
editado, cuándo se publicó y con qué URL. Ante cualquier reclamo se puede
reconstruir exactamente qué pasó y quién autorizó qué.

---

## 6. Manejo de fallos

Si la API de la red devuelve error, el post pasa a `fallido` (no a
"publicado"), se reintenta hasta 3 veces y, si sigue fallando, queda visible
en la cola para revisión manual. **Nunca se pierde en silencio.**

---

## 7. Qué NO automatizamos a propósito

- **Respuestas a comentarios y mensajes sensibles**: los responde una persona.
- **Contenido de crisis o temas delicados**: se redacta a mano.
- **Publicación de fotos de menores**: la selección de imágenes es siempre humana.
