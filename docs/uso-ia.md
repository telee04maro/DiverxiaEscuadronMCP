# Entregable 2 · Prototipo y uso de la IA

Lo exigen las bases: declarar las herramientas, los modelos y los datos usados, y explicar cómo se ha usado la IA, tanto **dentro del producto** como **para construirlo**.

## Principio: las reglas calculan y la IA interpreta

Cada uso de IA tiene detrás **una regla que lo verifica o lo sustituye**. Así el producto:
- no inventa cifras;
- funciona sin clave de IA, en modo reglas, para demostraciones y pruebas;
- y su coste está acotado.

## En el producto

| Agente | Qué hace la IA | Modelo | Por qué aquí | Cómo se verifica | Si no hay IA |
|---|---|---|---|---|---|
| Competencia | Lee el texto de los anuncios de la competencia: oferta, precio y si promete «sin esperas» | `claude-haiku-5-5` (esfuerzo bajo) | Texto libre y variado; clasificación barata en volumen | **El precio extraído debe aparecer literalmente en el anuncio**; si no, se descarta y queda en el registro | Expresiones regulares (precios en €, «sin esperas») |
| Competencia | Clasifica las reseñas por tema (espera, trato, precio, resultado, instalaciones) | `claude-haiku-5-5` | El lenguaje de las reseñas es ambiguo | Solo se aceptan índices de reseñas que existen y temas de una lista cerrada | Palabras clave |
| Coordinador | **Cruza los hallazgos de los especialistas** y propone la causa real, citando los hallazgos que la sostienen, y las hipótesis que se descartan | `claude-opus-5-5` (esfuerzo medio) | Es el razonamiento que ningún proveedor hace: unir finanzas y competencia | **Se rechaza toda causa que cite hallazgos inexistentes.** Que una causa sea «cruzada» lo calcula el código a partir de las áreas de los hallazgos citados, no lo decide la IA | Reglas de cruce explícitas (p. ej. caída de particulares + oferta de la competencia + quejas por espera) |
| Finanzas | Redacta la reclamación de cobro con el tono adecuado | `claude-opus-5-5` | El tono importa: no romper la relación con el cliente | **Deben aparecer cada factura, cada importe y el total, y ningún importe que no esté en los datos**; si no, se usa la plantilla. Todo correo se identifica como redactado por IA (Reglamento de IA, art. 50) | Plantillas por tono |
| Atención y captación | Nada: mide tiempos de respuesta, consultas perdidas y sin responsable con reglas | — | Son cálculos sobre datos del ERP/CRM | Reglas deterministas | — |

El **asistente de WhatsApp** (Hermes, componente previo del compañero, pendiente de que la organización lo acepte como tal) usa su propia IA para conversar. Vigía solo recibe lo que registra en el ERP a través del contrato `CrmConnector`, y lo valida (teléfono o correo obligatorio, longitudes, sin duplicar contactos).

**Lo que la IA nunca hace:**
- calcular dinero, plazos o márgenes;
- decidir si una factura está cobrada;
- enviar algo serio sin aprobación.

Todo eso lo hacen reglas deterministas o una persona.

**Protección frente a instrucciones escondidas:** los anuncios, las reseñas y los correos son datos de terceros. El mensaje de sistema prohíbe obedecer instrucciones que vengan dentro de ellos, y todas las salidas pasan por un esquema (Pydantic, con salidas estructuradas de la API) y por las comprobaciones de la tabla.

**Coste:**
- **Medido:** cada llamada registra sus tokens y su coste (pestaña 6 del panel).
- **Tope por ejecución:** `AI_BUDGET_USD`, 0,50 $ por defecto. Al alcanzarlo, se pasa a reglas.
- **Medido con la API real (24/11/2026, clínica de la demo):**
  - **Análisis** (3 llamadas: Haiku lee los anuncios y clasifica las reseñas; Opus cruza los hallazgos): **0,038–0,042 $** y 14–20 s. Casi todo es la llamada de Opus (unos 3.300 tokens de entrada y 1.200–1.400 de salida).
  - **Recorrido completo** (análisis + 2 correos de reclamación redactados por Claude + re-medición): **0,067 $** en 6 llamadas.
  - **Por empresa y mes**, con un análisis semanal y sus reclamaciones: unos **0,30 $**.
- **Comprobado en esa ejecución:** las 12 cifras que cita la causa de Claude (4,7 → 3,0, 86 %, 41 %, 8 oportunidades, 15,4 %, 18 días, 350 m, posición 6, 8.633,50 €, 64 días, 22 días, 29 días) salen de hallazgos calculados con reglas; los correos suman el total exacto (8.633,50 €), cambian de tono según el cliente y se identifican como IA.

## Para construirlo

| Para qué | Herramienta | Revisión humana |
|---|---|---|
| Analizar cómo ganamos el Malackathon y preparar el método (`CLAUDE.md`, plantillas) | Claude Code | El equipo eligió y corrigió el método |
| Leer el reto y las bases, e investigar problemas reales con datos (España, Málaga, agentes en producción, fuentes de datos y sus condiciones) | Claude Code con búsqueda web y agentes de investigación en paralelo | El equipo descartó ideas y eligió la suya (Vigía) |
| Decisiones de arquitectura y stack (ADR 001–003) | Claude Code | Aprobadas por el equipo |
| Programar el prototipo, los tests y la CI | Claude Code (Claude Opus 5.5) | Revisión del diff en cada commit; puertas de calidad (ruff, mypy estricto, pytest en Linux y Windows) |
| Auditoría independiente («red team») del código | Agente de Claude separado, solo lectura | El equipo decide qué se corrige |
| Canvas, marketing, logo y guion del pitch | Claude Code, a partir de la idea y las notas del equipo | Revisados y ajustados por el equipo |

## Herramientas, modelos y datos (declaración)

- **Modelos:** Claude Opus 5.5 y Claude Haiku 5.5 (Anthropic), a través del SDK oficial `anthropic` 2.12.0.
- **Software:** Python 3.13, Streamlit 1.67, pandas 3.1, Pydantic 2.14 y python-dotenv. En desarrollo: ruff, mypy y pytest. Versiones fijadas en `uv.lock`.
- **Datos:** **todos sintéticos**, generados por `vigia.data.synthetic`. La clínica, las aseguradoras y los competidores son ficticios, y los correos usan el dominio reservado `.example`. Los datos de la competencia imitan el formato oficial de la Biblioteca de Anuncios de Meta y de los resultados de búsqueda (`docs/fuentes.md`).
- **Componentes previos:** la plantilla de normas del equipo (`CLAUDE.md`), adaptada de nuestro proyecto del Malackathon 2026. El código de Vigía se ha escrito durante el hackathon.
