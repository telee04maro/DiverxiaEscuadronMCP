# 004. Cambio de nombre: de Centra a Vigía

- **Fecha:** 2026-11-24
- **Estado:** aceptada (decisión del equipo). Amplía la [ADR 002](002-vigia-equipo-de-agentes.md); no cambia el producto.

## Contexto

«Centra» era un nombre provisional, y hay otras empresas que se llaman así. Mantenerlo supone riesgo de confusión y de conflicto de marca.

## Decisión

El producto pasa a llamarse **Vigía**. El vigía es quien observa desde lo alto todo el horizonte y **avisa a tiempo**, que es exactamente lo que hace el coordinador con las áreas de la pyme.

- **Tesis:** «Cada proveedor ve su parte. **Vigía ve la causa.**»
- **Código:**
  - el paquete Python pasa de `centra` a `vigia` (sin tilde en los identificadores);
  - las variables de entorno, de `CENTRA_*` a `VIGIA_*`;
  - el panel se arranca con `uv run streamlit run src/vigia/app.py`;
  - la consola, con `uv run python -m vigia`.
- **Documentos:** se sustituye el nombre en todos ellos, incluidos el lienzo, el logo, el pitch y la marca. La ADR 002 se renombra a `002-vigia-equipo-de-agentes.md`. Las ADR siguen recogiendo la historia de las decisiones.

## Consecuencias

- Hay que actualizar el `.env` local de cada miembro del equipo: `CENTRA_USE_AI` pasa a `VIGIA_USE_AI` y `CENTRA_OUTBOX` a `VIGIA_OUTBOX`.
- **«Vigía» también es provisional:** antes de usarlo comercialmente hay que comprobar la marca en la OEPM y la EUIPO, y la disponibilidad del dominio.
