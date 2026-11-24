# 007. CRM de Vigía: una ficha única por cliente

- **Fecha:** 2026-11-24
- **Estado:** aceptada. Amplía la [ADR 005](005-conectores-y-captacion.md).
- **Origen:** pregunta del equipo: «si la empresa no tiene CRM, ¿cada agente crea el suyo y luego se genera uno general?».

## Contexto

Ya había un ERP/CRM de demo (contactos, consultas y notas) en el que escribe el asistente de WhatsApp. Pero cada agente veía a los clientes por su lado:
- **finanzas**, en las facturas (nombre, tipo y correo de cobro);
- **atención y captación**, en las consultas (un identificador de contacto);
- **las acciones**, en las reclamaciones.

Nadie podía ver que el cliente que nos debe dinero es el mismo que acaba de escribir por WhatsApp sin que nadie le conteste. Es el mismo problema que Vigía resuelve entre proveedores, pero dentro de casa.

## Opciones

| Opción | Ventaja | Por qué no / por qué sí |
|---|---|---|
| Un CRM por agente que luego se fusiona | Cada agente es independiente | Contactos duplicados y datos que se contradicen al fusionar. Es «cada proveedor ve su parte» otra vez |
| Que los agentes escriban sus clientes en el ERP durante el análisis | Persistente | El análisis dejaría de ser una lectura: efectos secundarios en un sistema de la empresa y riesgo justo antes de la entrega |
| **Un CRM calculado, con una ficha única por cliente (elegida)** | Una sola verdad, sin escrituras ni duplicados, con las mismas reglas que los agentes | No guarda historial propio: se recalcula en cada análisis a partir de las fuentes |

## Decisión

`src/vigia/crm.py` construye una ficha por cliente:
1. **Cada agente aporta su pieza:**
   - finanzas: facturas, importe vencido, factura más antigua y días medios de cobro, con la misma conciliación con el banco;
   - atención y captación: consultas, abiertas sin responsable y perdidas;
   - acciones: reclamaciones enviadas o pendientes de aprobación.
2. **Las piezas se unen por correo o teléfono normalizados** (union-find), así que un mismo cliente es una sola ficha. Si coinciden pero el nombre no, la ficha se marca para revisar: no se elige un nombre en silencio.
3. **Las mismas reglas que los agentes:** «sin responsable» usa la ventana de 30 días y las 48 h del agente de atención, medidas en la fecha del análisis. El CRM y los indicadores nunca se contradicen, y un mensaje que llega en directo no desplaza la ventana.
4. **Desconocido no es cero:** un contacto del que finanzas no sabe nada no «debe 0 €»; su deuda queda vacía.
5. **Alerta cruzada:** «debe dinero y tiene una consulta sin responsable: contéstale antes de reclamarle». Solo existe porque dos agentes hablan del mismo cliente.

En el panel: pestaña **«8 · Clientes (CRM)»**. El WhatsApp simulado acepta un correo, para enseñar el cruce en directo (por ejemplo, `pagos@mutuabeta.example`).

## Consecuencias

- **Si la empresa no tiene CRM,** el CRM de Vigía es esta ficha única. Las consultas entran por el asistente de WhatsApp (ERP de demo) o por la plantilla de «Tu empresa».
- **En la demo, finanzas factura a aseguradoras y las consultas son de pacientes:** no coinciden salvo que se escriba con el correo de una aseguradora. No se han cambiado los datos sintéticos para forzar el cruce.
- **Hoja de ruta:** guardar el historial de cada ficha, y unir también por NIF cuando las facturas lo traigan.
