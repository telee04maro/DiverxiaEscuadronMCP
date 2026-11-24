# 006. Qué permite la API de BALTER y cómo la usa Vigía

- **Fecha:** 2026-11-24
- **Estado:** aceptada. Amplía la [ADR 005](005-conectores-y-captacion.md).
- **Origen:** la documentación «Integración con la API de Balter» (v1, 27/10/2026) que nos ha pasado el equipo. **No se sube al repositorio:** es documentación de un tercero y el repositorio es público. La tiene el equipo.

## Lo que hemos verificado en la documentación

- **Autenticación:** una sola clave de integración (`Authorization: Bearer`). La clave determina la empresa; no hay usuario. `BALTER_USER` no hace falta.
- **URL base:** la de producción. La documentación no menciona un entorno de pruebas.
- **Solo tres operaciones**, con un permiso cada una:

| Operación | Qué hace | ¿Datos personales? | ¿Escribe? |
|---|---|---|---|
| Buscar un contacto (correo o teléfono) | Devuelve las coincidencias con su nombre y roles | **Sí** | No |
| Crear una oportunidad | Crea la oportunidad y, si no existe, la persona | Sí | **Sí, en producción** |
| Consultar artículos o servicios | Catálogo de la empresa | No | No |

- **No hay forma de listar ni leer oportunidades** (fechas, estado, responsable). Es la API del asistente de WhatsApp para **escribir** en BALTER, no una API para analizar.

## Decisión

1. **No hay `BalterConnector` por ahora.** El contrato `CrmConnector` necesita leer oportunidades, y BALTER no lo permite. Las demás operaciones leen datos personales o escriben en producción: siguen siendo del asistente de WhatsApp (Hermes), no de Vigía.
2. **Prueba de solo lectura sin datos personales:** `python -m vigia.connectors.balter_probe --autorizado`. Pide **un** artículo del catálogo y solo informa del código HTTP y de cuántos artículos llegaron, nunca de su contenido. Sin `--autorizado` no se ejecuta; ese indicador significa que la empresa ha dado su visto bueno. Distingue la clave válida (200), inválida (401) y sin permiso de catálogo (403). Un 200 con un formato distinto al documentado no cuenta como éxito.
3. **Cómo entran hoy las consultas reales en Vigía:** exportándolas de BALTER a la plantilla «Consultas y oportunidades» de «Tu empresa» (Excel o CSV). El agente de atención y captación las analiza igual que en la demo.
4. **Hoja de ruta:** pedir a BALTER una operación de solo lectura que liste oportunidades con su fecha de entrada, primera respuesta, estado y responsable. Con ella, el conector real es una implementación nueva de `CrmConnector`, sin tocar los agentes.

## Riesgos de la API real que afectan al asistente de WhatsApp

Lo recoge la propia documentación y conviene que lo sepa el compañero de Hermes:
- **Duplicados por el formato del teléfono:** la búsqueda puede no encontrar un número guardado con paréntesis o puntos, y crear la oportunidad puede crear un contacto duplicado. Conviene buscar siempre también por correo y enviar el teléfono normalizado. `normalize_phone` de Vigía lo deja como `+34XXXXXXXXX`.
- **Sin idempotencia:** cada petición válida crea una oportunidad nueva. Ante un tiempo agotado o un error 500, hay que comprobar en BALTER antes de reintentar.
- **Varias coincidencias (409 o más de un resultado):** hay que resolver la identidad; no vale coger el primer resultado.

El ERP de demo de Vigía ya evita estos duplicados (índices únicos y bloqueo). Por eso la demo no se puede presentar como prueba de lo que pasa en BALTER.

## Consecuencias

- La demo no cambia: sigue con el ERP de demo.
- «Conectado a BALTER» no se afirma en el pitch. Lo verificable es que tenemos el contrato y su documentación y que la clave funciona, si la prueba da 200. Las consultas reales entran por exportación.
