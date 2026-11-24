# 005. Conectores ERP/CRM, agente de atención y captación, y entrada de datos

- **Fecha:** 2026-11-24
- **Estado:** aceptada. Amplía la [ADR 002](002-vigia-equipo-de-agentes.md); ampliada por la [ADR 006](006-api-balter.md) (API real de BALTER).
- **Origen:**
  - la memoria del asistente de WhatsApp conectado a un ERP de un compañero del equipo (Hermes + Zernio + BALTER);
  - la pregunta «¿cómo entraría una empresa?».

## Contexto

Vigía solo funcionaba con la clínica de ejemplo:
- no tenía forma de recibir los datos de otra empresa;
- no estaba conectado a ningún ERP o CRM;
- le faltaba el agente de atención al cliente.

Un compañero tiene en producción un asistente de WhatsApp que atiende, cualifica y registra oportunidades en el ERP BALTER mediante un **conector de 5 operaciones**.

**BALTER es el ERP de producción de una empresa real, con datos de clientes.** Las bases prohíben usar datos personales o confidenciales sin autorización, y la propia memoria exige un gemelo aislado sin credenciales ni URL de producción.

## Opciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| Conectar Vigía al BALTER de producción | «Real» | Datos de clientes reales; acciones irreversibles en el ERP de un tercero; incumple las bases y la memoria; sin documentación de la API |
| **Interfaz de conector + ERP de demo con la forma de BALTER (elegida)** | Demo segura y reproducible; el lado de WhatsApp puede apuntar a él; cambiar al BALTER real es cambiar una pieza | El ERP de demo no es el real |
| Ignorar el ERP y el WhatsApp | Menos trabajo | El producto no muestra cómo entra una empresa ni cómo actúa en sus sistemas |

## Decisión

1. **Interfaz `CrmConnector`** (`src/vigia/connectors/base.py`) con las 5 operaciones de la memoria y una lectura:
   - `find_contact(phone, email)`: busca para no duplicar;
   - `create_contact`;
   - `create_opportunity`;
   - `add_note`;
   - `mark_origin`;
   - `list_opportunities`: lo que Vigía necesita leer.

   El flujo «registrar una consulta» (`register_enquiry`) aplica la regla de la memoria: si el contacto ya tiene una oportunidad abierta, se añade una nota en lugar de abrir otra.
2. **ERP de demo** (`src/vigia/connectors/demo_erp.py`): SQLite local con la forma de BALTER (contactos, oportunidades sin responsable asignado, notas, vía de entrada). Tiene una **API HTTP mínima** (`python -m vigia.connectors.http_api`) para que Hermes pueda escribir en él en lugar de en BALTER:
   - token obligatorio;
   - por defecto escucha solo en `127.0.0.1`.
3. **Conector BALTER real: pendiente.** No se escribe hasta tener:
   - la **documentación de su API**, porque no se inventan endpoints;
   - el **visto bueno de la empresa** propietaria de los datos;
   - las credenciales en `.env`, puestas por el equipo.

   Lista exacta y pasos en [`docs/integracion-balter.md`](../integracion-balter.md).

   La primera prueba será **de solo lectura, sin datos personales** (autenticación y un catálogo o recuento). **Nunca se escribe en producción.**
4. **Agente de atención y captación** (`src/vigia/specialists/customers.py`). Lee las oportunidades del ERP o CRM y detecta:
   - consultas fuera de horario que tardan en contestarse;
   - oportunidades perdidas;
   - oportunidades sin asignar.

   El coordinador lo cruza con finanzas y competencia. La acción que propone es activar el asistente de WhatsApp fuera de horario, con aprobación.
5. **Entrada «Tu empresa»** en el panel: entrevista inicial y subida de ficheros (CSV o Excel con plantillas descargables, cabeceras en español). Lo que falta aparece como hueco, nunca como cero.

## Contrato con el lado de WhatsApp (Hermes)

En `docs/integracion-whatsapp-erp.md`: operaciones, campos y autenticación de la API del ERP de demo. Hermes cambia su conector de BALTER por este contrato. El resto de su flujo no cambia, tal y como prevé su memoria.

## Consecuencias

- **A favor:**
  - Vigía muestra cómo entra una empresa (con Excel o con su ERP) y cómo actúa en sus sistemas.
  - La demo con WhatsApp en directo es posible sin tocar producción.
  - Más profundidad en la causa cruzada.
- **En contra:**
  - El ERP de demo no es BALTER.
  - Reutilizar Hermes y Zernio exige que la organización confirme que se aceptan como componentes previos declarados.
- **Datos personales en directo:** si el jurado escribe por WhatsApp, entran teléfonos reales. Hace falta un aviso de privacidad y borrar los datos después de la demo (`demo_erp.reset`), o usar móviles del equipo.
