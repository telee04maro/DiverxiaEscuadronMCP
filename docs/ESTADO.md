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
- **Caso de la demo:** clínica de fisioterapia ficticia de Málaga, con datos sintéticos.
- **Hoja de ruta del pitch:** los otros especialistas (marketing y clientes, legal, organización y personas, atención al cliente).

## Hoja de ruta

Cada etapa deja una versión entregable. Marca `[x]` al terminar, con su evidencia, y apunta en «En curso» quién está con cuál.

- [x] **P. Preparación:** repositorio, normas (`CLAUDE.md`), permisos compartidos y plantillas.
- [x] **R. Reto recibido:** 04 «La IA como servicio»; enunciado y entregables en `docs/reto/`.
- [x] **D. Idea elegida:** Centra, especialistas + coordinador (ADR 002, que sustituye a la 001).
- [x] **E0. Esqueleto del prototipo:** stack (ADR 003), dependencias fijadas, formato, lint y tests mínimos. Incluye el **contrato del hallazgo** (área, evidencia, confianza, impacto, esfuerzo, urgencia) y las interfaces de especialista, fuente y acción.
- [x] **E1. Datos sintéticos de la clínica:**
  - contabilidad, facturas a aseguradoras y particulares, y extracto bancario;
  - sesiones por mes;
  - reseñas propias;
  - competencia (anuncios, precios, reseñas);
  - el «mes después».
- [x] **E2. Fuentes de competencia verificadas** (`docs/fuentes.md`): condiciones, acceso y límites de la Biblioteca de Anuncios de Meta, el Centro de Transparencia de Google Ads, los buscadores y las reseñas. Fuente real o instantánea sintética con el mismo formato.
- [x] **E3. Especialista de finanzas:** indicadores con reglas (caja, márgenes, días de cobro, morosos), hallazgos con evidencia y la acción de reclamar facturas vencidas, con conciliación al céntimo.
- [x] **E4. Especialista de competencia y mercado:** anuncios, precios, posicionamiento y reseñas → hallazgos con evidencia.
- [x] **E5. Coordinador:** cruza los hallazgos, identifica la causa citando a los especialistas, prioriza, crea el plan a 7, 30 y 90 días y valida la contraoferta con finanzas.
- [x] **E6. MVP de principio a fin** (hito: unas 3–4 h desde E0): panel con el recorrido completo de la demo y el ejemplo de causa cruzada.
- [x] **E7. Re-medición:** el «mes después» simulado comprueba qué indicadores se movieron y reordena el plan.
- [x] **N1. Canvas:** `docs/negocio/canvas.md`. **Falta subirlo al Drive** (B).
- [x] **N2. Marketing:** `docs/negocio/marketing.md` y `logo.svg`. **Falta subirlo al Drive** (B).
- [x] **N3. Uso de la IA:** `docs/uso-ia.md`. **Falta subirlo al Drive, con capturas del panel.**
- [x] **N4. Guion del pitch:** `docs/negocio/pitch.md` y `docs/DEMO.md`. **Falta ensayarlo con el tiempo real.**
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
- **Recorrido completo** (`uv run streamlit run src/centra/app.py`, o en consola `uv run python -m centra --fallo`):
  empresa → especialistas → causa cruzada → plan a 7/30/90 días → acciones con aprobación → un mes después → registro y coste de IA.
- **Finanzas:**
  - caja (9 días de gasto);
  - cobros vencidos por cliente;
  - días de cobro;
  - caída de particulares no estacional;
  - conciliación al céntimo;
  - validación de la contraoferta (20 € y 25 € no compensan; 30 € sí).
- **Competencia:** oferta nueva en Meta (instantánea sintética), precio, reseñas con quejas por espera y visibilidad en Google. Lo que propone la IA se verifica contra el texto.
- **Coordinador:**
  - causa cruzada (finanzas + competencia) y «es la temporada» descartada;
  - causas de la IA validadas (se rechazan los hallazgos inexistentes);
  - modo reglas sin clave.
- **Acciones:**
  - el recordatorio amable sale solo y la reclamación formal espera aprobación;
  - el correo de la IA se verifica (facturas, importes, ningún importe inventado) y se identifica como IA;
  - no se envía nada dos veces;
  - bandeja local o SMTP solo al buzón de prueba.
- **Un mes después:** cobros comprobados al céntimo (el fallo de un céntimo no se da por cobrado); el resto de indicadores, «coincide» (no prueba la causa); el plan se reordena.
- **Entregables de negocio** en `docs/negocio/` (canvas, marketing con logo, guion del pitch) y uso de la IA en `docs/uso-ia.md`.

## En curso
| Tarea | Responsable | Desde |
|-------|-------------|-------|
| — | — | — |

## Siguiente paso
1. Probar con clave de Anthropic (`ANTHROPIC_API_KEY` en `.env`) y apuntar el coste real por análisis en `docs/uso-ia.md` y en el canvas.
2. Subir los 4 entregables al Drive (los .md se pueden pegar en un documento o en diapositivas; el logo es `docs/negocio/logo.svg`).
3. Ensayar el pitch con el tiempo real y las preguntas a los mentores (tabla de arriba). Confirmar el tamaño del equipo: las bases hablan de 6 y somos 3.
4. Antes de entregar: decidir si `docs/ideas.md` sale del repositorio (es interno).

## Última verificación
Formato: fecha y hora · SHA · comando o ID de ejecución · resultado.
- 24/11, 13:00 · `20c9af6` · CI de GitHub Actions (Linux y Windows) en verde en todos los commits · `uv run pytest`: 44 tests en verde.
- 24/11, 13:05 · `20c9af6` · Recorrido completo en el panel (navegador) y en la consola, en **modo reglas** (sin clave de IA en este equipo). **No verificado aún con Claude real.**
- 24/11, 13:20 · `babfc75` · **Red team R01:** 8 hallazgos P1 y 10 P2. Corregidos los 8 P1 y 9 de los P2, cada uno con su test de aceptación en `tests/test_red_team.py`. `uv run pytest`: 65 tests en verde. Recorrido completo repetido en el panel y en la consola con el código corregido.

## Problemas conocidos
- **Sin clave de IA en el portátil de desarrollo:** el modo Claude está cubierto por tests con respuestas guionizadas, pero no se ha ejecutado contra la API real.
- **Fuentes de competencia:** Meta y Google Ads exigen identidad verificada o no tienen API de autoservicio, y Google prohíbe el scraping de resultados. Se usan instantáneas sintéticas con el formato oficial (ver `docs/fuentes.md`).
- **Red team R01, pendiente (P2):** el coordinador con IA acepta una hipótesis descartada si cita hallazgos existentes aunque no sean los relevantes (p. ej. descartar «la temporada» citando la caja). En modo reglas no ocurre.
- **Streamlit no recarga los módulos de `centra` al cambiar el código:** tras modificar algo, hay que reiniciar el panel.
- **La re-medición no prueba causalidad** salvo en los cobros, que se comprueban al céntimo. El panel lo dice («coincide en el tiempo»).

## Cambios de rumbo
Registro de pivotes, errores de enfoque y cambios de dirección, el más reciente primero. Cada uno enlaza a su decisión en `docs/decisiones/`.

| Fecha | Cambio | Motivo | Decisión |
|---|---|---|---|
| 2026-11-24 | De consultor único a **Centra**: especialistas + coordinador que cruza la información. En la demo, competencia y finanzas en profundidad. El documento legal pasa a la hoja de ruta | Centralizar no aporta por sí solo; el valor es la causa cruzada. «Dos agentes muy buenos mejor que seis a medias» | [002](decisiones/002-centra-equipo-de-agentes.md) |
| 2026-11-24 | Idea elegida: consultor de IA permanente para pymes (caso de la clínica de fisioterapia) | Idea del equipo. Las propuestas v1 se descartaron por básicas y las v2 se dejaron como alternativas | [001](decisiones/001-idea-y-enfoque.md) |
