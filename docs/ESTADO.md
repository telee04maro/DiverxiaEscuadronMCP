# Estado del proyecto

Memoria compartida del equipo: **por dónde vamos y hacia dónde**. Se actualiza en cada commit que cierra un paso (ver `CLAUDE.md`, sección 2). Si eres una IA que acaba de hacer pull, lee esto primero.

## Rumbo

**Tesis (candidata):** «Una consultora te deja un informe. Nosotros te dejamos resultados medidos».

**Enfoque aceptado:** consultor de IA permanente para pymes que diagnostica, actúa y mide ([ADR 001](decisiones/001-idea-y-enfoque.md)).
- **Caso de la demo:** clínica de fisioterapia ficticia de Málaga, con datos sintéticos.
- **Acciones reales:**
  1. auditoría y plan priorizado;
  2. reclamar facturas vencidas, conciliando con el banco al céntimo;
  3. documento legal que falta, pendiente de validación por un asesor.
- **Cierre:** re-medición con un «mes después» simulado.

## Hoja de ruta

Cada etapa deja una versión entregable. Marca `[x]` al terminar, con su evidencia, y apunta en «En curso» quién está con cuál.

- [x] **P. Preparación:** repositorio, normas (`CLAUDE.md`), permisos compartidos y plantillas.
- [x] **R. Reto recibido:** 04 «La IA como servicio»; enunciado y entregables en `docs/reto/`.
- [x] **D. Idea elegida:** consultor de IA permanente para pymes; caso de la clínica de fisioterapia; tres acciones reales (ADR 001).
- [ ] **E0. Esqueleto del prototipo:** stack (ADR 002), dependencias fijadas, formato, lint y tests mínimos.
- [ ] **E1. Datos sintéticos de la clínica:** contabilidad, extracto bancario, agenda, reseñas propias y de la competencia, encuesta anónima y ficha legal. También el «mes después».
- [ ] **E2. Auditoría:** indicadores calculados con reglas, hallazgos con evidencia y confianza, interpretación con Claude y plan priorizado (semana, mes, trimestre).
- [ ] **E3. Acción: reclamar facturas vencidas:** decisión del tono, envío al buzón de demo y conciliación con el banco al céntimo.
- [ ] **E4. Acción: documento legal:** reglas de obligaciones con la norma citada, borrador y estado «pendiente de validación por un asesor».
- [ ] **E5. MVP de principio a fin** (hito: unas 3–4 h desde la idea): panel con el recorrido completo de la demo.
- [ ] **E6. Re-medición:** el «mes después» simulado compara los indicadores y reordena el plan.
- [ ] **N1. Canvas** (modelo de negocio) en el Drive. Responsable: B.
- [ ] **N2. Marketing** (logo, eslogan y estrategia de comunicación) en el Drive. Responsable: B.
- [ ] **N3. Uso de la IA** (`docs/uso-ia.md`) y presentación del prototipo en el Drive.
- [ ] **N4. Guion del pitch** y `DEMO.md`, ensayados con el tiempo real.
- [ ] **E7. Congelación de funciones** (unas 3 h antes de entregar): solo endurecer, reunir evidencias y preparar el pitch.
- [ ] **E8. Entrega:** los 4 entregables en el Drive, repositorio limpio y README final.

## Preguntas a los mentores

| Pregunta | Por qué cambia el plan | Respuesta | Quién / hora |
|---|---|---|---|
| ¿Criterios de evaluación y peso de cada uno? ¿Quién evalúa y cuándo? | Decide en qué invertir las horas (prototipo frente a negocio) | | |
| ¿Hora límite de cada hito? ¿Se revisan durante el día o solo al final? | Hoja de ruta y momento de enseñar avances a los mentores | | |
| ¿Cuánto dura el pitch? ¿Hay demo en directo? ¿Con qué formato (pantalla, PDF)? | Guion, demo y plan B | | |
| ¿Hay alguna empresa, sector o tipo de usuario prioritario? | Elección del problema | | |
| ¿Se pueden usar APIs de pago o servicios externos? ¿Algún dato o API proporcionado? | Stack y coste del prototipo | | |
| ¿«Uso de la IA» incluye cómo la hemos usado para construir, o solo la IA del producto? | Contenido del entregable 2 | | |

## Funciona
- Repositorio con las normas del equipo, permisos de Claude Code y plantillas de estado, ADR, demo y red team.

## En curso
| Tarea | Responsable | Desde |
|-------|-------------|-------|
| — | — | — |

## Siguiente paso
1. Aprobar el stack del prototipo (ADR 002) y arrancar E0.
2. Hacer las preguntas a los mentores (tabla de arriba) y confirmar el tamaño del equipo: las bases hablan de 6 y somos 3.
3. Repartir: A hace E0 y E2 (auditoría); B, el canvas y el marketing con el caso de la clínica; C, los datos sintéticos (E1) y el red team.
4. Decidir el nombre del producto.

## Última verificación
_Ninguna todavía._ Formato: fecha y hora · SHA · comando o ID de ejecución · resultado.

## Problemas conocidos
- Ninguno.

## Cambios de rumbo
Registro de pivotes, errores de enfoque y cambios de dirección, el más reciente primero. Cada uno enlaza a su decisión en `docs/decisiones/`.

| Fecha | Cambio | Motivo | Decisión |
|---|---|---|---|
| 2026-11-24 | Idea elegida: consultor de IA permanente para pymes (caso de la clínica de fisioterapia) | Idea del equipo. Las propuestas v1 se descartaron por básicas y las v2 se dejaron como alternativas | [001](decisiones/001-idea-y-enfoque.md) |
