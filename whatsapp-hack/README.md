# Asistente de WhatsApp de la demo (Zernio → Hermes → ERP de Vigía)

Componente previo de un miembro del equipo, adaptado para el hackathon. Parte de un ciclo que **ya funciona en producción**. Esta versión es parametrizable: todos los valores de la instancia (carpeta, claves, perfil de Hermes, mutex, tarea programada, etiqueta del bot, empresa y **destino de las fichas**) vienen de un `config.json` local, que no está en el repositorio. Decisión: [ADR 008](../docs/decisiones/008-asistente-whatsapp-en-balter.md).

Flujo de cada conversación:
1. Zernio lee los mensajes nuevos.
2. Hermes redacta la respuesta y extrae los datos en JSON. Hermes no tiene herramientas.
3. El código valida esos datos contra el texto literal del contacto y responde.
4. Con el nombre y el correo, crea **una** consulta en el **ERP de demo de Vigía**, por su API (`POST /api/v1/enquiries`). El **agente de atención y captación** la ve en el panel (interruptor «Incluir también las consultas registradas en el ERP de demo») y mide el tiempo de respuesta.

**Destino de las fichas** (`erp.tipo` en `config.json`):

| Destino | Cuándo | Qué hace falta |
|---|---|---|
| `vigia` (por defecto) | Siempre en la demo | La API del ERP de demo en marcha y su token (`VIGIA_ERP_TOKEN`) |
| `balter` | Solo con **permiso por escrito** de quien gestiona BALTER | Quién lo autorizó (`balter_autorizado_por`), clave de la empresa **ficticia** y un artículo de control que solo exista en ella |

Sin permiso anotado o sin artículo de control, el ciclo se para antes de leer, responder o crear nada.

**Garantías contra duplicados:**
- Registro previo exclusivo antes de cada acción irreversible.
- Doble consulta al ERP por teléfono y por correo.
- Nada se reintenta a ciegas; un resultado incierto se comprueba en el ciclo siguiente.
- Un mutex impide que coincidan dos ciclos.
- Si una persona escribe desde el móvil, el asistente se retira.

**Lo que valida antes de enviar o guardar:**
- El nombre: todas sus palabras las ha escrito el contacto (límite: no distingue un nombre armado con palabras sueltas; lo revisa una persona en el ERP).
- El correo: exactamente uno de los que escribió el contacto, no uno recortado ni contenido en otro.
- La respuesta: sin correos, teléfonos, enlaces, formato técnico ni caracteres de control.

## Datos personales
- El primer mensaje avisa de que es un asistente de IA de demostración y **pide un nombre y un correo inventados**.
- Al ERP de Vigía va lo mínimo (nombre, correo, teléfono verificado por WhatsApp, asunto y resumen); la conversación se queda en Zernio. En las pruebas `HTEST` no se guarda el teléfono.
- **No proyectes `-Monitor`** ni las carpetas `registro\`: muestran nombres y correos.
- Al acabar el evento se borra todo (ver «Después del evento»).

## Instancia de la demo

| Qué | Valor |
|---|---|
| Carpeta | `%LOCALAPPDATA%\HACK-WhatsApp\ciclo`, fuera de OneDrive y de git |
| Claves (DPAPI, cifradas para el usuario de Windows) | `%LOCALAPPDATA%\HACK-WhatsApp\claves` |
| Perfil de Hermes | `hackaton-demo`, vacío, con `SOUL-hackaton-demo.md` |
| Mutex y tarea programada | `Local\HACK_WhatsApp_Ciclo` y `HACK WhatsApp - Demo` |
| Número de WhatsApp | El de la demo, con una cuenta de Zernio propia. Va en el `.env` local (`HACK_NUMERO_DEMO`), no en el repositorio |
| ERP | ERP de demo de Vigía (`http://127.0.0.1:8765/api/v1`, u otra URL de la red local con `-UrlErp`) |
| Etiqueta del bot | «🤖 Asistente Virtual Vigía:» |
| Pruebas desde el móvil | Primer mensaje que empieza por **`HTEST`** |

**Barreras de seguridad:**
- El instalador se para si una clave coincide con una de producción protegida.
- También se para si la clave de Zernio ve más de un número, o si el número no es el de la demo.
- El token del ERP de Vigía solo viaja por HTTPS o dentro de la red local.
- Con BALTER: permiso por escrito anotado y artículo de control comprobado antes de cada ciclo.

**Instalación de producción en el mismo equipo:** si la hay, se declara en el `.env` **local** del repositorio, que no se sube a git, separando varios valores con `;`:
```
HACK_PROTEGER_CLAVES=<carpetas de %LOCALAPPDATA% con las claves .dpapi de producción>
HACK_PROTEGER_CICLO=<carpeta de %LOCALAPPDATA% del ciclo de producción>
HACK_PROTEGER_MUTEX=<mutex de producción>
HACK_PROTEGER_PERFIL=<perfil de Hermes de producción>
```

## Puesta en marcha

Antes de empezar, añade `%LOCALAPPDATA%\HACK-WhatsApp` y la carpeta del repositorio a las excepciones del antivirus. Ejecuta cada bloque en PowerShell, desde la carpeta del repositorio.

**0 · Arrancar la API del ERP de demo** (en otra ventana; ver `docs/integracion-whatsapp-erp.md`)
```
$env:VIGIA_ERP_TOKEN = "<token largo, al menos 16 caracteres>"
uv run python -m vigia.connectors.http_api --port 8765
```
En el `.env` local: `VIGIA_ERP_TOKEN` (el mismo), `ZERNIO_API_KEY` y `HACK_NUMERO_DEMO`.

**1 · Instalar**
```
cls
powershell -ExecutionPolicy Bypass -File .\whatsapp-hack\HACK-Instalar.ps1
```
- Zernio y ERP de Vigía: `USAR` (los toma del `.env`) o pégalas.
- Si la API corre en otro portátil de la red: `-UrlErp http://<ip>:8765/api/v1`.
- Solo con permiso por escrito de BALTER: primero `HACK-ClaveBalter.ps1` y después `HACK-Instalar.ps1 -Destino balter`.

**2 · Pruebas sin conexión.** Tienen que terminar con `0 fallos`.
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo-Pruebas.ps1"
```
Desde el repositorio también las lanza `uv run pytest`, junto con una prueba de integración real bot → API del ERP → agente de captación (`tests/test_whatsapp_bot.py`, solo en Windows).

**3 · Leer solo los chats nuevos.** Frase: `PRODUCCION`.
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarProduccion
```

**4 · Arrancar en segundo plano.** Frase: `AUTOMATICO`.
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarFondo -Segundos 10
```
- Revisa el WhatsApp cada 10 segundos (mínimo 5), oculto, sin depender de ninguna ventana.
- Cada minuto, el Programador de tareas comprueba que sigue vivo y lo relanza si se ha caído.
- Funciona mientras la sesión de Windows esté iniciada (puede estar bloqueada). Para que el equipo no se suspenda: `powercfg /change standby-timeout-ac 0`.

**Ver en directo** (solo en tu pantalla, no en el proyector; cerrar esta ventana no lo para):
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Monitor
```

**Parar:** `-Parar`. **Otros comandos:** `-Estado`, `-Revisiones`, `-Ignorar <ID>`, `-Retomar <ID>`, y sin parámetros (modo REVISAR: no envía ni crea).

**Plan B** si falla WhatsApp, Zernio o Hermes: el formulario «Simular mensaje de WhatsApp» de la pestaña 7 del panel crea la misma consulta en el ERP de demo.

## Crear fichas de prueba

1. **Primer mensaje:** `HTEST: Hola, soy <nombre>. <consulta>`. Con `HTEST`, el chat es una prueba aunque el teléfono ya esté en el ERP:
   - no se busca ni se guarda el teléfono;
   - la consulta se crea como contacto nuevo, con el resumen marcado «PRUEBA (HTEST)».
2. **Datos:** cuando lo pida, da nombre con apellidos y un **correo ficticio nuevo** cada vez.
3. **Otra ficha desde el mismo móvil:** ejecuta `-NuevaPrueba`. El bucle puede seguir en marcha. Archiva sin borrar las conversaciones de prueba; lo escrito antes ya no cuenta.

## Después del evento

1. Ejecuta `-Parar`.
2. Borra los datos del ERP de demo: «Borrar todos los datos del ERP de demo» (pestaña 7 del panel). Si usasteis BALTER, borra allí las oportunidades y los contactos con la etiqueta `DEMO`.
3. Borra las conversaciones en Zernio.
4. Borra `%LOCALAPPDATA%\HACK-WhatsApp`.
