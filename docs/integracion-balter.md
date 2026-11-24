# Conectar el BALTER real

Hoy Vigía lee las consultas de un **ERP de demo con la forma de BALTER** ([ADR 005](decisiones/005-conectores-y-captacion.md)). Para conectarlo al BALTER de verdad hacen falta las tres cosas de abajo. **Sin las tres no se conecta**: BALTER tiene datos de clientes reales, y las bases del hackathon prohíben usarlos sin autorización.

## Estado (24/11/2026)

| # | Qué | Estado |
|---|---|---|
| 1 | **Documentación de la API** | ✅ Recibida (v1, 27/10/2026). **Se guarda fuera del repositorio**, porque es de un tercero y el repositorio es público. Resumen y decisión en la [ADR 006](decisiones/006-api-balter.md) |
| 2 | **Visto bueno** de la empresa dueña de BALTER para una prueba de solo lectura | ✅ Confirmado por el equipo el 24/11 (16:27) y anotado en `docs/ESTADO.md`. Falta añadir quién lo dio |
| 3 | **Credenciales en `.env`** | ✅ `BALTER_URL` y `BALTER_TOKEN`. `BALTER_USER` no hace falta: la API se autentica solo con la clave |

## Lo que hemos aprendido de la API

**No permite leer oportunidades.** Solo busca contactos (devuelve nombres), crea oportunidades (escribe en producción) y consulta el catálogo de artículos. Por eso:
- Vigía **no se conecta a BALTER para analizar**: las consultas reales entran exportándolas a la plantilla «Consultas y oportunidades» de «Tu empresa».
- La única prueba sin datos personales es pedir **un artículo del catálogo**.

## La prueba (solo con el visto bueno)

**Resultado del 24/11, 16:27:** `HTTP 200 · artículos recibidos: 1`. La clave funciona y puede leer el catálogo.

```powershell
uv run python -m vigia.connectors.balter_probe --autorizado
```

Solo muestra el código HTTP y cuántos artículos llegaron (0 o 1), nunca su contenido ni la clave:

| Resultado | Qué significa |
|---|---|
| `HTTP 200 · artículos recibidos: 1` | La clave funciona y puede leer el catálogo |
| `HTTP 401` | Clave inválida, revocada o caducada |
| `HTTP 403` | Clave válida, pero sin permiso de catálogo (`articles.read`). Normal si es la clave de Hermes, que solo busca y escribe |

Sin `--autorizado`, no se ejecuta.

## Lo que nunca hace Vigía con BALTER

- Buscar contactos: devuelve nombres de personas.
- Crear oportunidades o contactos: escribe en producción. Eso es cosa del asistente de WhatsApp.
- Guardar o mostrar la clave en logs, informes o pantallas.
