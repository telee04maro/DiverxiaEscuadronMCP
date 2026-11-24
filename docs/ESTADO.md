# Estado del proyecto

Memoria compartida del equipo: **por dónde vamos y hacia dónde**. Se actualiza en cada commit que cierra un paso (ver `CLAUDE.md`, sección 2). Si eres una IA que acaba de hacer pull, lee esto primero.

## Rumbo

**Producto:** **Centra** (nombre provisional), un equipo de agentes de IA para toda la pyme ([ADR 002](decisiones/002-centra-equipo-de-agentes.md)).

**Tesis (candidata):** «Cada proveedor ve su parte. Centra ve la causa».

**Prototipo:**
- **Especialistas en profundidad:** competencia y mercado, y finanzas.
- **Coordinador:** cruza los dos hallazgos, encuentra la causa y crea el plan a 7, 30 y 90 días.
- **Acciones reales:**
  - reclamar facturas vencidas, conciliando con el banco al céntimo;
  - contraoferta, solo si finanzas confirma el margen;
  - re-medición con un «mes después» simulado.
- **Caso de la demo:** clínica de fisioterapia ficticia de Málaga, con datos sintéticos (por confirmar).
- **Hoja de ruta del pitch:** los otros especialistas (marketing y clientes, legal, organización y personas, atención al cliente).

## Hoja de ruta

Cada etapa deja una versión entregable. Marca `[x]` al terminar, con su evidencia, y apunta en «En curso» quién está con cuál.

- [x] **P. Preparación:** repositorio, normas (`CLAUDE.md`), permisos compartidos y plantillas.
- [x] **R. Reto recibido:** 04 «La IA como servicio»; enunciado y entregables en `docs/reto/`.
- [x] **D. Idea elegida:** Centra, especialistas + coordinador (ADR 002, que sustituye a la 001).
- [ ] **E0. Esqueleto del prototipo:** stack (ADR 003), dependencias fijadas, formato, lint y tests mínimos. Incluye el **contrato del hallazgo** (área, evidencia, confianza, impacto, esfuerzo, urgencia) y las interfaces de especialista, fuente y acción.
- [ ] **E1. Datos sintéticos de la clínica:**
  - contabilidad, facturas a aseguradoras y particulares, y extracto bancario;
  - sesiones por mes;
  - reseñas propias;
  - competencia (anuncios, precios, reseñas);
  - el «mes después».
- [ ] **E2. Fuentes de competencia verificadas** (`docs/fuentes.md`): condiciones, acceso y límites de la Biblioteca de Anuncios de Meta, el Centro de Transparencia de Google Ads, los buscadores y las reseñas. Fuente real o instantánea sintética con el mismo formato.
- [ ] **E3. Especialista de finanzas:** indicadores con reglas (caja, márgenes, días de cobro, morosos), hallazgos con evidencia y la acción de reclamar facturas vencidas, con conciliación al céntimo.
- [ ] **E4. Especialista de competencia y mercado:** anuncios, precios, posicionamiento y reseñas → hallazgos con evidencia.
- [ ] **E5. Coordinador:** cruza los hallazgos, identifica la causa citando a los especialistas, prioriza, crea el plan a 7, 30 y 90 días y valida la contraoferta con finanzas.
- [ ] **E6. MVP de principio a fin** (hito: unas 3–4 h desde E0): panel con el recorrido completo de la demo y el ejemplo de causa cruzada.
- [ ] **E7. Re-medición:** el «mes después» simulado comprueba qué indicadores se movieron y reordena el plan.
- [ ] **N1. Canvas** (modelo de negocio) en el Drive. Responsable: B.
- [ ] **N2. Marketing** (logo, eslogan y estrategia de comunicación) en el Drive. Responsable: B.
- [ ] **N3. Uso de la IA** (`docs/uso-ia.md`) y presentación del prototipo en el Drive.
- [ ] **N4. Guion del pitch** y `DEMO.md`, ensayados con el tiempo real.
- [ ] **E8. Congelación de funciones** (unas 3 h antes de entregar): solo endurecer, reunir evidencias y preparar el pitch.
- [ ] **E9. Entrega:** los 4 entregables en el Drive, repositorio limpio y README final.

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
1. Aprobar el stack del prototipo (ADR 003) y arrancar E0.
2. Confirmar el caso de la demo (clínica de fisioterapia) y verificar las fuentes de competencia (E2).
3. Hacer las preguntas a los mentores (tabla de arriba) y confirmar el tamaño del equipo: las bases hablan de 6 y somos 3.
4. Repartir:
   - A: E0, finanzas y coordinador.
   - B: canvas, marketing, el ejemplo de causa cruzada para el pitch y el canal de gestorías.
   - C: datos sintéticos (E1), fuentes (E2) y red team.

## Última verificación
_Ninguna todavía._ Formato: fecha y hora · SHA · comando o ID de ejecución · resultado.

## Problemas conocidos
- Ninguno.

## Cambios de rumbo
Registro de pivotes, errores de enfoque y cambios de dirección, el más reciente primero. Cada uno enlaza a su decisión en `docs/decisiones/`.

| Fecha | Cambio | Motivo | Decisión |
|---|---|---|---|
| 2026-11-24 | De consultor único a **Centra**: especialistas + coordinador que cruza la información. En la demo, competencia y finanzas en profundidad. El documento legal pasa a la hoja de ruta | Centralizar no aporta por sí solo; el valor es la causa cruzada. «Dos agentes muy buenos mejor que seis a medias» | [002](decisiones/002-centra-equipo-de-agentes.md) |
| 2026-11-24 | Idea elegida: consultor de IA permanente para pymes (caso de la clínica de fisioterapia) | Idea del equipo. Las propuestas v1 se descartaron por básicas y las v2 se dejaron como alternativas | [001](decisiones/001-idea-y-enfoque.md) |
