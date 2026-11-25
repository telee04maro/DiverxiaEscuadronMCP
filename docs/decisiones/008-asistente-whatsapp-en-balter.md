# 008. Asistente de WhatsApp de la demo: Zernio → Hermes → ERP de demo de Vigía (BALTER solo con permiso)

- **Fecha:** 2026-11-25
- **Estado:** aceptada. Amplía la [ADR 005](005-conectores-y-captacion.md) y la [ADR 006](006-api-balter.md).
- **Origen:** el reto pide un agente que actúe en los sistemas de la empresa. Un miembro del equipo aporta su asistente de WhatsApp (componente previo, en producción en otra empresa) en la rama `Miguel`. Esa versión escribía en BALTER, en una empresa ficticia. Revisada e integrada en `development` el 25/11.

## Decisión

1. El asistente (`whatsapp-hack/`) es un ciclo en PowerShell parametrizable con un `config.json` local:
   - lee WhatsApp por Zernio;
   - Hermes redacta y extrae datos, sin herramientas;
   - el código valida y crea **una** consulta por conversación.
2. **Destino por defecto: el ERP de demo de Vigía**, por su API (`/api/v1/contacts` y `/api/v1/enquiries`, contrato en `docs/integracion-whatsapp-erp.md`). Motivos:
   - cumple la regla de las ADR 005 y 006: en el hackathon no se escribe en el BALTER de producción;
   - el agente de atención y captación **ve y mide** lo que entra por WhatsApp; la API de BALTER no permite leer oportunidades, así que en BALTER el jurado no vería la unión con Vigía;
   - lo que escribe el público se queda en un sistema nuestro que se borra al acabar.
3. **BALTER, solo con permiso por escrito** de quien lo gestiona. Se anota quién lo dio (`balter_autorizado_por`) y hace falta un artículo de control que solo exista en la empresa ficticia. Sin las dos cosas, el ciclo se para antes de leer, responder o crear nada.
4. **Instancia separada de cualquier instalación de producción.** Tiene su propia carpeta, claves DPAPI, perfil de Hermes, mutex, tarea programada y cuenta de Zernio. Los valores de producción que haya que proteger y el número de la demo se declaran solo en el `.env` local, nunca en el repositorio.
5. **Garantías contra duplicados**, porque ninguna de las dos APIs tiene idempotencia:
   - registro previo exclusivo;
   - doble consulta por teléfono y correo;
   - ningún reintento a ciegas;
   - mutex entre ciclos.
6. **Las pruebas del equipo** empiezan por `HTEST`: no se busca ni se guarda el teléfono del probador.

## Cambios al integrarlo (revisión del 25/11)

- El correo tiene que ser exactamente uno de los escritos por el contacto (antes valía uno recortado, como `ana@gmail.co` de `ana@gmail.com`).
- Una respuesta con enlaces no se envía (podría venir de una instrucción inyectada en el chat).
- Intervalo mínimo de revisión: 5 s (con 2 s eran unas 43.000 consultas al día a Zernio).
- El token del ERP solo viaja por HTTPS o dentro de la red local, y un 404 de ruta no se toma por «el contacto no existe».
- El primer mensaje pide un nombre y un correo inventados.
- El número de WhatsApp de la demo sale del repositorio (va en el `.env` local).

## Consecuencias

- Pruebas: 113 comprobaciones sin conexión y una prueba de integración real bot → API del ERP → agente de captación (`tests/test_whatsapp_bot.py`, en la CI de Windows).
- **Límite conocido:** el nombre se valida palabra a palabra; no distingue un nombre armado con palabras sueltas del mensaje. Lo revisa una persona en el ERP.
- **Pendiente de declarar:** el modelo de IA que usa Hermes (lo configura su autor en el perfil `hackaton-demo`).
- Al terminar el evento se borran los datos del ERP de demo, las conversaciones de Zernio y la carpeta local del asistente.
- La documentación de la API de BALTER sigue fuera del repositorio.
