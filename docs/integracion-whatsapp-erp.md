# Integración: asistente de WhatsApp (Hermes) ↔ ERP de Vigía

Contrato entre el lado de WhatsApp (Hermes y la pasarela Zernio, del compañero del equipo) y Vigía. Decisión: [ADR 005](decisiones/005-conectores-y-captacion.md).

**Regla de oro:** en el hackathon, Hermes escribe en el **ERP de demo de Vigía**, nunca en el BALTER de producción. Así lo pide su propia memoria (un gemelo aislado, sin credenciales ni URL de producción) y lo exigen las bases (nada de datos personales sin autorización).

```
Cliente ──WhatsApp──► Zernio (cuenta de prueba) ──► Hermes (portátil, sin tareas heredadas)
                                                         │  HTTP + token
                                                         ▼
                                     ERP de demo de Vigía (/api/v1)  ◄── Vigía lo lee y lo cruza
```

**El asistente real** está en `whatsapp-hack/` (ADR 008): usa `GET /contacts` para no duplicar y `POST /enquiries` para registrar. Instalación y uso en `whatsapp-hack/README.md`.

## Arrancar el ERP de demo

```bash
# En el equipo donde corre Vigía (PowerShell: $env:VIGIA_ERP_TOKEN = "...")
export VIGIA_ERP_TOKEN="<token largo, al menos 16 caracteres>"
uv run python -m vigia.connectors.http_api --port 8765            # solo este equipo (127.0.0.1)
uv run python -m vigia.connectors.http_api --host 0.0.0.0 --port 8765   # si Hermes está en otro portátil de la misma red
```

- El token se comparte en persona o por un canal privado: **nunca en el repositorio ni en el chat del proyecto**.
- Con `--host 0.0.0.0` el ERP queda accesible en la red local. Hacedlo solo en una red de confianza y apagadlo al terminar.
- Al acabar la demo, borrad los datos con «Borrar todos los datos del ERP de demo» (pestaña 7 del panel).

## Autenticación

Todas las peticiones llevan la cabecera `Authorization: Bearer <VIGIA_ERP_TOKEN>`. Sin ella, la respuesta es `401`.

## Operaciones (las 5 del conector de la memoria y una lectura)

Base: `http://<equipo-de-vigía>:8765/api/v1`. Cuerpos y respuestas en JSON (UTF-8). Teléfonos en cualquier formato habitual: `+34 600 000 001`, `0034600000001` y `600000001` son el mismo contacto.

| Operación de la memoria | Petición | Cuerpo | Respuesta |
|---|---|---|---|
| Buscar contacto | `GET /contacts?phone=…&email=…` | — | `200` contacto · `404` si no existe |
| Crear contacto | `POST /contacts` | `{"name", "phone"?, "email"?}` (al menos teléfono o correo) | `201` contacto `{"id", "name", "phone", "email"}` |
| Crear oportunidad | `POST /opportunities` | `{"contact_id", "topic", "summary"?, "urgent"?, "channel"?, "first_response_at"?}` | `201` oportunidad, **sin responsable asignado** |
| Añadir nota | `POST /opportunities/{id}/notes` | `{"text"}` | `201` |
| Marcar origen | `POST /opportunities/{id}/origin` | `{"origin": "whatsapp"}` | `200` |
| *(lectura)* Listar oportunidades | `GET /opportunities` | — | `200` lista |

### Atajo recomendado: todo el flujo en una llamada

`POST /enquiries` hace lo mismo que la memoria describe paso a paso:
1. busca el contacto;
2. si no existe, lo crea;
3. si ya tiene una oportunidad abierta, **añade la conversación como nota** en lugar de abrir otra;
4. si no, crea la oportunidad y marca el origen;
5. si es urgente, deja aviso para el responsable.

```json
POST /api/v1/enquiries
{
  "name": "Nombre que da el cliente",
  "phone": "600000001",
  "topic": "Primera visita",
  "summary": "Resumen de la conversación hecho por Hermes",
  "urgent": false,
  "channel": "whatsapp",
  "answered_at": "2026-11-24T21:32:00"
}
```

Respuesta `201`: `{"contact": {...}, "opportunity_id": "OP-…", "new_contact": true, "new_opportunity": true, "escalated": false}`

## Errores
| Código | Cuándo |
|---|---|
| `400` | JSON no válido |
| `401` | Falta el token o no es correcto |
| `404` | Ruta, contacto u oportunidad inexistentes |
| `413` | Cuerpo mayor de 64 KB |
| `422` | Datos no válidos. La respuesta lista los campos, sin detalles internos |

## Qué hace Vigía con estos datos
El **agente de atención y captación** lee las oportunidades (en el panel, el interruptor «Incluir también las consultas registradas en el ERP de demo»). Mide:
- el tiempo de respuesta dentro y fuera de horario;
- las consultas perdidas;
- las oportunidades sin responsable.

El coordinador lo cruza con finanzas y competencia.

## Pendiente para el BALTER real (no en el hackathon)
Cuando haya **documentación de la API de BALTER** y **visto bueno de la empresa**, se escribirá `BalterConnector` con este mismo contrato (`src/vigia/connectors/base.py`).
- La primera prueba será **solo de lectura y sin datos personales**: autenticación y un catálogo o recuento.
- **Nunca se escribirá en producción.**
- Las credenciales irán en `.env` (`BALTER_URL`, `BALTER_USER`, `BALTER_TOKEN`), puestas por el equipo.
