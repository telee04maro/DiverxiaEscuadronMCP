# 008. Asistente de WhatsApp de la demo: Zernio → Hermes → BALTER (empresa ficticia)

- **Fecha:** 2026-11-25
- **Estado:** aceptada (rama `Miguel`). Amplía la [ADR 006](006-api-balter.md).
- **Origen:** el reto pide un agente que actúe en los sistemas de la empresa. El equipo dispone de una clave de integración de BALTER de una **empresa ficticia creada para la demo**.

## Decisión

1. El asistente (`whatsapp-hack/`) es un ciclo en PowerShell que ya se ha usado en producción, ahora parametrizable con un `config.json` local:
   - lee WhatsApp por Zernio;
   - Hermes redacta y extrae datos, sin herramientas;
   - el código valida y crea **una** oportunidad en BALTER por conversación.
2. **Solo escribe en la empresa ficticia.** En la API de BALTER, la clave decide la empresa. Antes de hacer nada, el ciclo comprueba que el catálogo de esa empresa tiene un artículo de control que solo existe en la demo. Si no lo tiene, se para.
3. **Instancia separada de cualquier instalación de producción.** Tiene su propia carpeta, claves DPAPI, perfil de Hermes, mutex, tarea programada y cuenta de Zernio. Los valores de producción que haya que proteger se declaran solo en el `.env` local, nunca en el repositorio.
4. **Garantías contra duplicados**, porque la API no tiene idempotencia:
   - registro previo exclusivo;
   - doble consulta por teléfono y correo;
   - ningún reintento a ciegas;
   - mutex entre ciclos.
5. **Las pruebas del equipo** empiezan por `HTEST`. Así no se usa su teléfono, que ya está en BALTER como empleado.

## Consecuencias

- El primer mensaje avisa de que es un asistente virtual de demostración y de que los datos se borrarán.
- Al terminar el evento se borran en BALTER las oportunidades y los contactos con la etiqueta `DEMO`.
- La documentación de la API de BALTER sigue fuera del repositorio.
