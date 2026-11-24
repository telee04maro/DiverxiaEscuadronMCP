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

**Lo que la IA nunca hace:**
- calcular dinero, plazos o márgenes;
- decidir si una factura está cobrada;
- enviar algo serio sin aprobación.

Todo eso lo hacen reglas deterministas o una persona.

**Protección frente a instrucciones escondidas:** los anuncios, las reseñas y los correos son datos de terceros. El mensaje de sistema prohíbe obedecer instrucciones que vengan dentro de ellos, y todas las salidas pasan por un esquema (Pydantic, con salidas estructuradas de la API) y por las comprobaciones de la tabla.

**Coste:**
- **Medido:** cada llamada registra sus tokens y su coste (pestaña 6 del panel).
- **Tope por ejecución:** `AI_BUDGET_USD`, 0,50 $ por defecto. Al alcanzarlo, se pasa a reglas.
- **Estimado:** unos 0,10–0,15 $ por análisis completo (5 llamadas), según los precios de los modelos de noviembre de 2026. En Opus 5.5 el razonamiento interno no se puede desactivar y se cobra como salida. Se medirá en cuanto haya clave.

## Para construirlo

| Para qué | Herramienta | Revisión humana |
|---|---|---|
| Analizar cómo ganamos el Malackathon y preparar el método (`CLAUDE.md`, plantillas) | Claude Code | El equipo eligió y corrigió el método |
| Leer el reto y las bases, e investigar problemas reales con datos (España, Málaga, agentes en producción, fuentes de datos y sus condiciones) | Claude Code con búsqueda web y agentes de investigación en paralelo | El equipo descartó ideas y eligió la suya (Centra) |
| Decisiones de arquitectura y stack (ADR 001–003) | Claude Code | Aprobadas por el equipo |
| Programar el prototipo, los tests y la CI | Claude Code (Claude Opus 5.5) | Revisión del diff en cada commit; puertas de calidad (ruff, mypy estricto, pytest en Linux y Windows) |
| Auditoría independiente («red team») del código | Agente de Claude separado, solo lectura | El equipo decide qué se corrige |
| Canvas, marketing, logo y guion del pitch | Claude Code, a partir de la idea y las notas del equipo | Revisados y ajustados por el equipo |

## Herramientas, modelos y datos (declaración)

- **Modelos:** Claude Opus 5.5 y Claude Haiku 5.5 (Anthropic), a través del SDK oficial `anthropic` 2.12.0.
- **Software:** Python 3.13, Streamlit 1.67, pandas 3.1, Pydantic 2.14 y python-dotenv. En desarrollo: ruff, mypy y pytest. Versiones fijadas en `uv.lock`.
- **Datos:** **todos sintéticos**, generados por `centra.data.synthetic`. La clínica, las aseguradoras y los competidores son ficticios, y los correos usan el dominio reservado `.example`. Los datos de la competencia imitan el formato oficial de la Biblioteca de Anuncios de Meta y de los resultados de búsqueda (`docs/fuentes.md`).
- **Componentes previos:** la plantilla de normas del equipo (`CLAUDE.md`), adaptada de nuestro proyecto del Malackathon 2026. El código de Centra se ha escrito durante el hackathon.
