# Tratamiento de datos personales

Las bases del hackathon prohíben introducir datos personales, secretos empresariales o información confidencial sin autorización. **La demo es una clínica ficticia con datos sintéticos.** Este documento explica qué datos personales podría tratar Vigía con una empresa real, dónde quedan, qué llega a Claude y cómo se borran. Lo auditó el red team en su tercera ronda (R3); cada punto tiene su test en `tests/test_red_team_r3.py`.

## Qué datos entran

| Dato | De dónde | ¿Hace falta? | Qué hace Vigía |
|---|---|---|---|
| Nombre y correo de cobro de los clientes que facturan | Plantilla de facturas | El correo, solo para reclamar | Para un **particular** basta un identificador («Particular 12»). Sin correo válido no se reclama: sale como dato que falta |
| Texto de las reseñas | Plantilla de reseñas | El texto sí, el autor no | Se guarda **sin nombres, teléfonos, correos ni DNI**, de nadie (`domain/privacy.py`) |
| Nombre, teléfono, correo y mensaje de quien escribe por WhatsApp | El asistente de WhatsApp (`whatsapp-hack/`), a través de la API del ERP de demo | Sí, para contestar y no duplicar | Al ERP de demo (SQLite local) llegan el nombre, el correo, el teléfono (no en las pruebas `HTEST`), el asunto y un resumen; la conversación se queda en Zernio. El mensaje pasa por Zernio y por el modelo de Hermes (componentes del asistente), nunca por Claude. El primer mensaje pide **datos inventados** |
| Correos de reclamación enviados | Las acciones de finanzas | Sí, como justificante | En la bandeja local `outbox/` o, con SMTP, solo al buzón de prueba |

## Qué llega a Claude

| Llamada | Lo que recibe | Lo que **no** recibe |
|---|---|---|
| Leer anuncios de la competencia | El texto público de los anuncios | — |
| Clasificar reseñas | Las reseñas ya limpias | Nombres, teléfonos, correos o DNI |
| Cruzar hallazgos | Los hallazgos, con «Aseguradora 1», «Empresa 2»… en lugar del nombre de quien debe dinero | El nombre de ningún moroso |
| Redactar una reclamación | Facturas, fechas e importes; el cliente aparece como `[CLIENTE]` | El nombre del cliente, que se pone después en local |

Nada de esto incluye los mensajes del WhatsApp ni los datos de contacto del ERP. Anthropic no usa los datos enviados por la API para entrenar sus modelos por defecto (condiciones comerciales de la API); aun así, se envía lo mínimo.

## Dónde quedan y cómo se borran

| Dónde | Contenido | Cómo se borra |
|---|---|---|
| ERP de demo (`data/erp-demo.sqlite`, fuera de git) | Contactos, consultas y notas del WhatsApp | Pestaña 7 → «Borrar todos los datos del ERP de demo». Borra **también del fichero** (`secure_delete` y `VACUUM`): comprobado que no queda ni el nombre, ni el teléfono, ni el correo, ni el texto |
| `outbox/` (fuera de git) | Los correos de reclamación de la sesión | Borrar la carpeta |
| Memoria del panel | El análisis y el registro de la sesión | «Reiniciar la demo» o cerrar el panel; no se guarda en disco |
| Registro de la API | Nada del contenido de las peticiones | No se registra |
| `.env` (fuera de git) | Claves de Anthropic y de BALTER | Lo gestiona el equipo; un test impide que acaben en `.env.example` |

## Reglas que se cumplen siempre

- **Minimización:** solo lo que la acción necesita; lo demás no entra o se limpia al entrar.
- **Desconocido no es cero ni «impagado»:** sin extracto que cubra la factura, no se reclama a nadie.
- **Nada sale a terceros sin control:** los correos van a una bandeja local o al buzón de prueba; la reclamación formal espera aprobación.
- **Con una persona real en la demo** (el jurado escribiendo por WhatsApp): avisar antes y pulsar «Borrar todos los datos» al acabar.

## Límites conocidos

- La detección de nombres en las reseñas es heurística: quita nombres completos («Juan Pérez») y nombres tras pistas como «me atendió Laura». Un nombre suelto sin pista puede pasar.
- BALTER real: su API devuelve nombres al buscar contactos, así que Vigía no la usa para eso (ADR 006).
- Para un uso en producción harían falta el registro de actividades de tratamiento, el contrato de encargado con cada cliente y una evaluación de impacto si hubiera datos de salud. Queda en la hoja de ruta.
