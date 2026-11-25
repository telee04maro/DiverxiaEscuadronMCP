# Estado del proyecto

Memoria compartida del equipo: **por dónde vamos y hacia dónde**. Se actualiza en cada commit que cierra un paso (ver `CLAUDE.md`, sección 2). Si eres una IA que acaba de hacer pull, lee esto primero.

## Rumbo

**Producto:** **Vigía** (nombre provisional), un equipo de agentes de IA para toda la pyme ([ADR 002](decisiones/002-vigia-equipo-de-agentes.md)).

**Tesis (candidata):** «Cada proveedor ve su parte. Vigía ve la causa».

**Prototipo:**
- **Especialistas en profundidad:** competencia y mercado, finanzas, y atención y captación (consultas del ERP/CRM).
- **Coordinador:** cruza los hallazgos de las tres áreas, encuentra la causa y crea el plan a 7, 30 y 90 días.
- **Acciones reales:**
  - reclamar facturas vencidas, conciliando con el banco al céntimo;
  - contraoferta, solo si finanzas confirma el margen;
  - re-medición con un «mes después» simulado.
- **Caso de la demo:** clínica de fisioterapia ficticia de Málaga, con datos sintéticos.
- **Entrada de una empresa real:** «Tu empresa» (entrevista + Excel/CSV con plantillas). ERP de demo con API para el asistente de WhatsApp (Hermes).
- **Hoja de ruta del pitch:** los otros especialistas (marketing y clientes, legal, organización y personas, chat del dueño) y la lectura de oportunidades de BALTER, que su API actual no ofrece (ADR 006).

## Hoja de ruta

Cada etapa deja una versión entregable. Marca `[x]` al terminar, con su evidencia, y apunta en «En curso» quién está con cuál.

- [x] **P. Preparación:** repositorio, normas (`CLAUDE.md`), permisos compartidos y plantillas.
- [x] **R. Reto recibido:** 04 «La IA como servicio»; enunciado y entregables en `docs/reto/`.
- [x] **D. Idea elegida:** Vigía, especialistas + coordinador (ADR 002, que sustituye a la 001).
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
- [x] **E10. Atención y captación** (ADR 005): agente de consultas del ERP/CRM, contrato `CrmConnector`, ERP de demo con API para Hermes y entrada «Tu empresa» (Excel/CSV con plantillas).
- [x] **E8. Congelación de funciones:** desde `a29b738` solo se endurece (red team R02, unidades en la re-medición, ruta de Claude ante salidas inválidas). Sin funciones nuevas.
- [ ] **E9. Entrega:** hecho lo del repositorio (README final, ideas internas fuera, sin secretos, CI en verde) y los ficheros de `docs/entrega/` listos. **Falta (equipo):** subirlos al Drive, vídeo o capturas de respaldo de la demo y ensayo del pitch.

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
- **Recorrido completo** (`uv run streamlit run src/vigia/app.py`, o en consola `uv run python -m vigia --fallo`):
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
- **Atención y captación:** consultas fuera de horario (en la demo, 59 % del total, 12,0 h de respuesta frente a 0,4 h en horario y 41 % perdidas frente a 0 %) cruzadas en la causa principal de tres áreas solo si los datos muestran más pérdidas fuera de horario; plan con «activar el asistente de WhatsApp» (con aprobación) y re-medición (de 12,0 h a minutos; perdidas del 41 % al 21 %).
- **ERP de demo con la forma de BALTER** y su API (token, 127.0.0.1 por defecto; 1.160–1.560 pet./s de lectura sin rechazos, medido con oha): Hermes registra consultas sin duplicar contactos ni oportunidades, también con 20 mensajes simultáneos; en el panel, pestaña 7, con mensaje de WhatsApp simulado y borrado de datos.
- **CRM de Vigía (ficha única de cliente, ADR 007):** finanzas, atención y acciones aportan cada uno su parte y se unen por correo o teléfono; mismas reglas que los agentes (en la demo, 8 sin responsable en el CRM y en el KPI). Pestaña 8 del panel. Alerta cruzada «contéstale antes de reclamarle» cuando el que debe dinero tiene una consulta sin atender.
- **Vocabulario por sector:** el mismo análisis habla de «pacientes» y «sesiones» en una clínica y de «clientes» y «ventas» en cualquier otra pyme (taller, restaurante…); lo que falta se nombra («Extracto bancario»), nunca como fichero.
- **«Tu empresa»:** entrevista inicial y subida de Excel/CSV con plantillas en español; validación fila a fila (CSV de Excel en Windows-1252, facturas repetidas, ficheros corruptos o importes imposibles salen como avisos); lo que falta es un hueco.
- **Entregables de negocio** en `docs/negocio/` (canvas, marketing con logo, guion del pitch) y uso de la IA en `docs/uso-ia.md`.

## En curso
| Tarea | Responsable | Desde |
|-------|-------------|-------|
| E9. Entrega: subir `docs/entrega/` al Drive, vídeo de respaldo y ensayo del pitch | Equipo (dueño del repositorio) | 24/11, 16:20 |
| BALTER real: anotar **quién dio el visto bueno** y guardar el correo (ver `docs/integracion-balter.md`) | Equipo (dueño del repositorio) | 24/11, 16:27 |

## Siguiente paso
1. Hecho: probado con Claude real; coste medido en `docs/uso-ia.md`, el canvas y el pitch. Red team R3 cerrado.
2. Subir los 4 entregables al Drive (los .md se pueden pegar en un documento o en diapositivas; el logo es `docs/negocio/logo.svg`).
3. Ensayar el pitch con el tiempo real y las preguntas a los mentores (tabla de arriba). Confirmar el tamaño del equipo: las bases hablan de 6 y somos 3.
4. Hecho: `docs/ideas.md` (interno) ya no está en el repositorio; sigue en el historial de git.
5. **Pitch de 3 minutos reescrito** (rama `claude/pitch-3min`, desde `732066e`): audio de 5,5 s (gestoría, agencia y banco diciendo «lo mío va bien» a la vez; `docs/negocio/pitch-audio-gancho.mp3`), dos datos reales con fuente (INE: solo el 34,3 % de las empresas de 10 o más empleados analiza sus datos; PMcM vía PIMEC: el 85 % de las grandes empresas incumple el plazo legal de pago), la clínica como ejemplo inventado y **el nombre «Vigía» solo al final** («Somos Vigía y venimos a…»). 387 palabras (2:55 a ritmo vivo). Todas las cifras clasificadas en el guion: datos reales verificados, resultados de la demo (sintéticos, no son estudios) y cifras de negocio. En el canvas, la cifra de 62.234 gestorías queda **por verificar**. Cifras cuadradas entre pitch, canvas y demo: el canvas recoge los dos datos reales en «Problemas», el agente de atención en el caso de la demo y los cobros contados igual que en el pitch (2 de 3 de la aseguradora; 3 de las 4 reclamadas). El lienzo A3 no cambia: sus cifras ya coinciden. **Ojo:** la imagen de antes y después de la rama `claude/gracious-pascal-xq2iyx` dice 75 % de quejas por espera y con el código actual es 50 %: hay que rehacerla antes de usarla.

6. **Plan de negocio** (rama `claude/plan-de-negocio`, desde `claude/pitch-3min`): `docs/negocio/plan-de-negocio.md`, modelo en `docs/negocio/plan-de-negocio-modelo.py` y PDF en `docs/entrega/5-plan-de-negocio.pdf`. Propuesta: pequeñas empresas de 10–49 empleados a través de gestorías (30 % recurrente), planes de 79/149/249 € al mes, el Ayuntamiento o Promálaga como patrocinador de un piloto (contrato menor de 15.000 € para 25 pymes) y unos 91.000–106.000 € de inversión hasta el equilibrio en el mes 16 (escenario base). **Pendiente de aprobar** por el equipo; si se aprueba, hay que actualizar el canvas y el pitch («desde 79 €»).

7. **Pitch emotivo** (rama `claude/plan-de-negocio`): el dueño en segunda persona («Abriste tu negocio para cuidar de la gente…»), los datos con cara humana («cuatro de cada diez pacientes… se van sin que nadie les conteste») y un bloque «Imagínate…» como segundo clímax antes de «Somos Vigía». 352 palabras (2:54 de media). El guion ya no dice el precio ni el canal de gestorías: en las preguntas del jurado van la venta directa y la propuesta de 690 € de alta y desde 199 € al mes, **pendientes de aprobar**.

8. **Eslogan nuevo: «Vuelve a lo que importa.»** (5 palabras; la organización pide menos de siete). Ya está en el cierre del pitch, en el marketing y en el canvas. La idea «Cada proveedor ve su parte. Vigía ve la causa» queda como tesis interna. **Falta** cambiarlo en el logo, el lienzo, el README, el panel y el PDF del prototipo, al unificar la marca (un logo, dos colores y una tipografía en todo, como pide la organización antes de las 12:30).

9. **Marca e interfaz** (de la rama `claude/paleta-y-logo`, integrada en `claude/entrega`) (marca e interfaz; sin cambios de lógica):
   - paleta C (azul petróleo `#1D5C7A`, terracota `#D9824E`, tinta `#1B2B34`, arena `#FAF7F2`) y logo «Atalaya» con sus versiones (`docs/negocio/logo*.svg`, `icono*.svg`, `docs/entrega/3-logo.png`);
   - panel rediseñado para el dueño: cabecera con los pasos (Analizar → Entender → Actuar → Medir), resumen «Lo más importante» en la pestaña 1, pestañas en lenguaje sencillo, etiquetas de autonomía en palabras y la causa cruzada destacada. Los botones se llaman igual que en el guion. Estilo en `src/vigia/ui.py`, con todo texto de datos escapado;
   - auditoría: el texto de terceros (anuncios, reseñas, ficheros subidos) ya no puede convertirse en enlaces, imágenes ni fórmulas en el panel (`ui.md_safe`, `tests/test_ui.py`); «comprobado» solo para cobros al céntimo («Mejoró (coincide en el tiempo)» para el resto) y «Pago incompleto» cuando falta un céntimo;
   - `3-marketing.pdf` reexportado con el logo nuevo. **Falta:** rehacer las capturas de `docs/entrega/capturas/` y `2-prototipo.pdf`, que enseñan el panel antiguo.

10. **Rama de entrega `claude/entrega`** (pitch + plan de negocio + marca y panel nuevos, con la pestaña 8 de `main` y sin el fallo del céntimo). Requisitos de la organización para antes de las 12:30:
   - **Eslogan** «Vuelve a lo que importa.» (5 palabras) en el logo, el pitch, el marketing, el canvas, el lienzo, el README, el panel y el prototipo;
   - **un logo** («Atalaya»), **dos colores** (azul petróleo `#1D5C7A` y terracota `#D9824E`) y **una tipografía** (Inter: en el logo, en el panel —servida desde `src/vigia/static/`, con su licencia OFL— y en todos los PDF);
   - **pieza que enseña el producto:** `2-prototipo.pdf` con capturas nuevas de las 8 pestañas (modo reglas);
   - **diapositiva final de herramientas de IA:** `docs/entrega/6-herramientas-de-ia.png` y `.pdf`;
   - pestañas con nombres cortos para que quepan las 8.
   **Pendiente:** el canvas y el lienzo siguen con el modelo de negocio anterior (gestorías y 99–399 €) hasta que se aprueben los precios del plan nuevo; comprobar el nombre «Vigía» con las cuatro pruebas del taller y en la OEPM.

## Última verificación
Formato: fecha y hora · SHA · comando o ID de ejecución · resultado.
- 24/11 · rama `claude/paleta-y-logo` · **Panel rediseñado, recorrido completo en el navegador** (Playwright, modo reglas): análisis → causa y plan → ejecutar, aprobar y marcar 6 tareas (no la campaña) → «un mes después» con el fallo inyectado: Seguros Gamma «sin efecto», 0,01 € pendiente, no se da por cobrada; pestañas 6 y 7 y «Tu empresa» sin errores (0 excepciones en pantalla). `uv run pytest` 137 en verde; ruff y mypy limpios.
- 25/11 · `732066e` · **Cifras del pitch** con `uv run python -m vigia` y `analyze()` en modo reglas sobre `mes-0` y `mes-1`: caja 9 días, aseguradora a 95 días, oferta a 20 € hace 18 días, 86 % de quejas por espera, 59 % fuera de horario, 12,0 h, 41 % perdidas, contraoferta 20 € −21 % / 25 € −16 % / 30 € −10 %; un mes después (simulado): 2 de 3 facturas de Mutua Beta cobradas, 0,0 h de mediana, quejas por espera 50 %. Todas coinciden con el guion.
- 24/11, 19:05 · `00fb343` · **Verificación final en limpio** (clon nuevo desde GitHub, sin clave de IA): ruff y mypy limpios, `uv run pytest` 177 en verde, `uv run python -m vigia` sin errores. **oha sobre la versión final:** lectura 1.160–1.560 pet./s según la carga del equipo (con el panel y el navegador abiertos, 1.160), **0 rechazos** con 50 y con 200 conexiones a la vez, el 1 % más lento por debajo de 200 ms; escritura 113–150 pet./s (pasan de una en una a propósito: sin duplicados). Quitar el `secure_delete` de las conexiones normales no cambió la cifra: la variación es de carga; se deja solo en «Borrar todos los datos». Capturas y `2-prototipo.pdf` rehechos con el código final y Claude real (quejas por espera 86 % → 50 %, igual con reglas que con Haiku).
- 24/11, 18:40 · `0ea4357` · **Red team R03** (seguridad, datos personales y proceso de los agentes, auditor independiente de solo lectura): 8 P1, 6 P2 y 3 P3, todos corregidos con su test en `tests/test_red_team_r3.py`. `uv run pytest`: 177 en verde; ruff y mypy limpios; CI en verde. **Con Claude real** tras los verificadores nuevos: 3 causas y 2 correos de la IA aceptados, 0 descartados (0,07 $, 27 s). Textos de la demo idénticos salvo lo previsto (detalle de reseñas; mes 1 de 75 % a 50 % de quejas por espera).
- 24/11, 18:00 · `a3514bf` · **Rendimiento con oha** contra la API del ERP de demo: lectura con 50 a la vez de 774 a 1.562 pet./s, de 17 rechazos a 0, el 1 % más lento de 1.026 ms a 47 ms; ráfaga de 200 a la vez, 100 % de éxito; escritura, el 1 % más lento de 586 ms a 188 ms. WAL medido y descartado (1,7 veces más lento en Windows). Análisis por reglas 2 ms, CRM 3 ms; con Claude 14 s, de ellos 12 s el cruce de Opus (con menos esfuerzo solo baja a 10 s: no compensa). Las dos lecturas de Haiku en paralelo: de 3,5 s a 2,0 s.
- 24/11, 13:00 · `20c9af6` · CI de GitHub Actions (Linux y Windows) en verde en todos los commits · `uv run pytest`: 44 tests en verde.
- 24/11, 13:05 · `20c9af6` · Recorrido completo en el panel (navegador) y en la consola, en **modo reglas** (sin clave de IA en este equipo). **No verificado aún con Claude real.**
- 24/11, 15:05 · `720f4ef` · Panel en el navegador tras reiniciarlo: análisis de la clínica (59 %, 12,0 h, 41 %), pestaña 7 (mensaje de WhatsApp simulado → nota, sin duplicar) y «un mes después» con unidades (12,0 h → 0,0 h); sin ejecutar acciones, no atribuye ningún cambio. Búsqueda de secretos en el repositorio: nada.
- 24/11, 17:55 · `5478878` · **CRM de Vigía:** 10 tests nuevos (147 en verde); textos de la demo idénticos. En el panel con Claude real: mensaje de WhatsApp con el correo de Mutua Beta → una sola ficha con deuda (8.633,50 €, 95 días) y consulta sin responsable, alerta cruzada; 110 fichas, 10 que necesitan algo (coherente con el agente). Corregido antes de subir: un mensaje de hoy desplazaba la ventana de 30 días (test de regresión).
- 24/11, 17:10 · Vocabulario por sector: los 107 textos de la demo de la clínica, idénticos antes y después (modo reglas). Un taller ficticio por «Tu empresa»: ninguna palabra de clínica, en reglas (`tests/test_vocabulary.py`) y con Claude real (0,017 $, causa con «clientes particulares» y cifras de los datos). Una empresa sana: ningún hallazgo ni causa. `uv run pytest`: 137 en verde.
- 24/11, 16:42 · `b2ffeb3` · **Entrega en limpio, como la vería el jurado:** clon nuevo desde GitHub siguiendo el README (`uv sync`, `cp .env.example .env`, sin clave de IA): `uv run pytest` 128 en verde; `uv run python -m vigia --fallo` sin errores y con el pago de 1 céntimo no dado por cobrado; panel con las 7 pestañas sin trazas. ZIP del código para el Drive con `git archive` desde `926d226` (159 ficheros, sin `.env` ni claves), fuera del repositorio: `vigia-prototipo-codigo.zip`, el único ZIP.
- 24/11, 16:27 · `48f6920` · **BALTER real, prueba de solo lectura** (`uv run python -m vigia.connectors.balter_probe --autorizado`, con el visto bueno confirmado por el equipo): **HTTP 200 · 1 artículo recibido**. La clave es válida y tiene permiso de lectura del catálogo. No se leyó ni guardó ningún dato personal ni el contenido del artículo, y no se escribió nada.
- 24/11, 16:10 · `b44e161` · **Claude real** (clave en `.env`, Opus 5.5 + Haiku 5.5): análisis 0,038–0,042 $ en 3 llamadas y 14–20 s; `uv run python -m vigia --fallo` 0,067 $ en 6 llamadas, sin errores; panel en el navegador 0,0383 $. Las 12 cifras de la causa de Claude existen en los hallazgos; los 2 correos suman al céntimo, cambian de tono y se identifican como IA; el fallo de un céntimo no se da por cobrado.
- 24/11, 15:10 · Ruta de Claude sin red (cliente falso, `tests/test_claude_model.py`): salida fuera del esquema → reglas, coste medido, tope de gasto y modelo desconocido nunca gratis. `uv run pytest`: 115 tests en verde.
- 24/11, 14:55 · `a29b738` · **Red team R02** (conector ERP, agente de atención y «Tu empresa»): 18 hallazgos, todos corregidos con su test de aceptación en `tests/test_red_team_r2.py`. `uv run pytest`: 112 tests en verde; ruff y mypy estricto limpios.
- 24/11, 13:20 · `babfc75` · **Red team R01:** 8 hallazgos P1 y 10 P2. Corregidos los 8 P1 y 9 de los P2, cada uno con su test de aceptación en `tests/test_red_team.py`. `uv run pytest`: 65 tests en verde. Recorrido completo repetido en el panel y en la consola con el código corregido.

## Problemas conocidos
- **Re-medición sin umbral (auditoría del 24/11):** cualquier movimiento en la dirección esperada cuenta como mejora y saca la acción del plan, aunque el problema siga (p. ej., quejas por espera del 86 % al 75 %; particulares del −15,4 % al −10,9 %). Propuesta: un objetivo por indicador y «seguir» en el plan mientras no se alcance. No se cambia en la congelación.
- **Con el fallo inyectado cambian las cifras de cobro:** sin fallo, 3 de las 4 facturas reclamadas (lo que dice el canvas); con fallo, que es lo que enseña el guion, 2 de 4. Quien presente tiene que saberlo.
- **La causa redactada por Claude varía entre ejecuciones** (mismo fondo, distinto título y orden). Las cifras siempre salen de los hallazgos; para un pitch reproducible, el modo reglas da siempre el mismo texto.
- **Fuentes de competencia:** Meta y Google Ads exigen identidad verificada o no tienen API de autoservicio, y Google prohíbe el scraping de resultados. Se usan instantáneas sintéticas con el formato oficial (ver `docs/fuentes.md`).
- **Red team R01, pendiente (P2):** el coordinador con IA acepta una hipótesis descartada si cita hallazgos existentes aunque no sean los relevantes (p. ej. descartar «la temporada» citando la caja). En modo reglas no ocurre.
- **BALTER real:** su API v1 no permite leer oportunidades, así que el agente de atención no puede analizar BALTER en directo. Las consultas reales entran por exportación a «Tu empresa». La clave se probó el 24/11 en solo lectura: funciona (ADR 006).
- **Riesgos de BALTER para el asistente de WhatsApp:** posibles contactos duplicados por el formato del teléfono, y sin idempotencia (un reintento crea otra oportunidad). El ERP de demo no los tiene; no se presenta como prueba de BALTER (ADR 006).
- **Hermes y Zernio** son componentes previos del compañero: pendiente de que la organización confirme que se pueden usar declarados como tales.
- **El ERP de demo serializa los registros** con un bloqueo por proceso: suficiente para la demo, no para varios servidores a la vez (ahí lo garantizan los índices únicos de la base de datos).
- **Competencia con datos propios de una empresa:** «Tu empresa» no tiene plantilla de anuncios ni de resultados de búsqueda, así que el agente compara precios y reseñas y lo demás lo da como dato que falta. Los anuncios de Meta y las posiciones en Google solo están en la demo (instantáneas sintéticas).
- **Umbrales sin calibrar:** horas de respuesta lentas, caída no estacional, etc., son razonables pero no se han ajustado con empresas reales; hace falta un piloto.
- **Streamlit no recarga los módulos de `vigia` al cambiar el código:** tras modificar algo, hay que reiniciar el panel.
- **La re-medición no prueba causalidad** salvo en los cobros, que se comprueban contra el banco. El panel lo dice («coincide en el tiempo»).
- **Tope de gasto con llamadas en paralelo:** las dos lecturas de Haiku comprueban el tope a la vez, así que se puede pasar como mucho en una llamada pequeña (≈0,0002 $).
- **Nombres en reseñas:** la limpieza quita nombres completos y nombres tras pistas («me atendió Laura»); un nombre suelto sin pista puede pasar (ver `docs/datos-personales.md`).
- **Extracto que empieza tarde:** una factura emitida antes del primer movimiento del extracto y sin ningún movimiento que la cite queda «sin datos del banco», no «impagada»: no se reclama hasta tener el extracto completo.

## Cambios de rumbo
Registro de pivotes, errores de enfoque y cambios de dirección, el más reciente primero. Cada uno enlaza a su decisión en `docs/decisiones/`.

| Fecha | Cambio | Motivo | Decisión |
|---|---|---|---|
| 2026-11-24 | **CRM de Vigía: ficha única de cliente** (función nueva tras la congelación E8, a petición del equipo) | Sin CRM, cada agente veía a los clientes por su lado; la ficha única cruza deuda y consultas del mismo cliente | [007](decisiones/007-ficha-unica-de-cliente.md) |
| 2026-11-24 | **Visto bueno para una prueba de solo lectura en BALTER**, confirmado por el equipo en la sesión (16:27). Alcance: un artículo del catálogo, sin datos personales ni escrituras. Falta anotar quién lo dio | Requisito de la ADR 005 antes de tocar BALTER | [006](decisiones/006-api-balter.md) |
| 2026-11-24 | **No hay conector de lectura de BALTER**; prueba de solo lectura del catálogo (con `--autorizado`) y consultas reales por exportación a «Tu empresa» | Su API v1 no permite listar oportunidades; las otras operaciones leen datos personales o escriben en producción | [006](decisiones/006-api-balter.md) |
| 2026-11-24 | Nuevo agente de atención y captación, contrato de conector ERP/CRM, ERP de demo con la forma de BALTER y entrada «Tu empresa». **BALTER de producción descartado** | Integrar el asistente de WhatsApp del compañero y mostrar cómo entra una empresa; BALTER real tiene datos de clientes y las bases lo impiden | [005](decisiones/005-conectores-y-captacion.md) |
| 2026-11-24 | El producto pasa a llamarse **Vigía** (antes, Centra); paquete `vigia` y variables `VIGIA_*` | Hay otras empresas que se llaman Centra | [004](decisiones/004-nombre-vigia.md) |
| 2026-11-24 | De consultor único a **Vigía**: especialistas + coordinador que cruza la información. En la demo, competencia y finanzas en profundidad. El documento legal pasa a la hoja de ruta | Centralizar no aporta por sí solo; el valor es la causa cruzada. «Dos agentes muy buenos mejor que seis a medias» | [002](decisiones/002-vigia-equipo-de-agentes.md) |
| 2026-11-24 | Idea elegida: consultor de IA permanente para pymes (caso de la clínica de fisioterapia) | Idea del equipo. Las propuestas v1 se descartaron por básicas y las v2 se dejaron como alternativas | [001](decisiones/001-idea-y-enfoque.md) |
