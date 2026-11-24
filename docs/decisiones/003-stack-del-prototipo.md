# 003. Stack del prototipo

- **Fecha:** 2026-11-24
- **Estado:** aceptada
- **Origen:** E0 de la hoja de ruta. El equipo pidió iterar hasta tener el proyecto final con los valores por defecto propuestos.

## Contexto

Hay que construir en pocas horas un prototipo de Centra con:
- dos especialistas en profundidad (competencia y finanzas);
- un coordinador que cruza sus hallazgos;
- acciones reales;
- re-medición;
- un panel para la demo.

Las condiciones de partida:
- El ordenador del equipo tiene `uv` y Python, pero no Node ni Docker.
- El equipo ganó el Malackathon con Python, uv, ruff, mypy y pytest.
- Las bases prohíben datos personales, así que los datos son sintéticos y viven en CSV y JSON, que es el formato en que las pymes tienen sus datos de verdad (Excel).

## Opciones evaluadas

| Pieza | Opciones | Elegida y por qué |
|---|---|---|
| Lenguaje | Python / TypeScript | **Python 3.13** con `uv`: está instalado y es el flujo con el que ganamos |
| IA | SDK oficial `anthropic` / frameworks de agentes de terceros | **SDK oficial `anthropic` 2.12.0** (API `2026-10-21`). El bucle lo controlamos nosotros: el coordinador y los especialistas son código, y Claude se usa en puntos concretos con **salidas estructuradas validadas** (`messages.parse` con modelos Pydantic). Un framework añadiría dependencias y opacidad sin aportar nada a dos especialistas |
| Modelos | Opus 5.5 / Sonnet 5.5 / Haiku 5.5 | **`claude-opus-5-5`** para cruzar hallazgos, explicar causas y redactar. **`claude-haiku-5-5`** para clasificar en volumen (temas de reseñas, ofertas de anuncios). Es lo que pide `CLAUDE.md` (sección 4). Los ID de modelo y el tope de gasto van en `.env` |
| Interfaz | Streamlit / FastAPI + HTMX / Next.js | **Streamlit 1.67.0**: es lo más rápido para un panel de demo sin Node. La lógica está separada de la interfaz, así que se puede cambiar sin tocar a los agentes |
| Datos | pandas / CSV estándar | **pandas 3.1.1** para los indicadores. Dinero siempre con `Decimal` |
| Modelos de datos | dataclasses / Pydantic | **Pydantic 2.14.4**: valida datos de entrada y salidas del LLM, y es lo que usa `messages.parse` |
| Envío de correos | SMTP real / bandeja local | **Interfaz `Mailer`** con dos implementaciones. La **bandeja local** (por defecto): escribe `.eml` en `outbox/` y los muestra en el panel. **SMTP**: si hay credenciales en `.env`, solo a destinatarios de prueba |
| Calidad | — | ruff 0.17.6, mypy 2.4.1 (estricto), pytest 9.2.0 y CI en Linux y Windows |

Versiones comprobadas en PyPI el 24/11/2026. Para `anthropic` se fija la 2.12.0 en lugar de la 2.13.0, que tenía un día.

## Decisión

- El stack de la tabla, con versiones exactas en `pyproject.toml` y `uv.lock`.
- **Funciona sin clave de IA:** cada uso de Claude tiene una alternativa determinista basada en reglas. El panel indica en qué modo se ejecutó.
- **Coste medido:** cada llamada registra sus tokens y su coste según la tabla de precios de la configuración. Un tope por ejecución (`AI_BUDGET_USD`) corta las llamadas y pasa a modo reglas.
- **Salida del LLM no confiable:** se valida con el esquema. Además, el coordinador rechaza toda causa que cite hallazgos que no existen o que solo tenga apoyo de una única área cuando dice ser cruzada.

## Consecuencias

- **A favor:**
  - Demo reproducible sin red, también con el modo reglas.
  - Coste controlado.
  - Arquitectura extensible: un especialista nuevo es una implementación nueva registrada.
- **En contra:** Streamlit limita el diseño visual. Se acepta para un prototipo.
- **Fallback por rechazo de seguridad:** no se activa el parámetro `fallbacks` del servidor (beta). Para análisis de negocio sobre datos sintéticos el riesgo es bajo, y si una respuesta acaba en `refusal`, ese paso se resuelve con reglas y queda anotado en el registro.
