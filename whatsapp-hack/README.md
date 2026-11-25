# Asistente de WhatsApp del hackathon (Zernio → Hermes → BALTER)

El asistente parte de un ciclo que **ya funciona en producción**. Esta versión es parametrizable: todos los valores de la instancia (carpeta, claves, perfil de Hermes, mutex, tarea programada, etiqueta del bot y empresa) vienen de un `config.json` local, que no está en el repositorio.

Flujo de cada conversación:
1. Zernio lee los mensajes nuevos.
2. Hermes redacta la respuesta y extrae los datos en JSON. Hermes no tiene herramientas.
3. El código valida esos datos contra el texto literal del contacto, responde y crea **una** oportunidad en BALTER.

**Garantías contra duplicados:**
- Registro previo exclusivo antes de cada acción irreversible.
- Doble consulta al ERP por teléfono y por correo.
- Nada se reintenta a ciegas.
- Un mutex impide que coincidan dos ciclos.
- Si una persona escribe desde el móvil, el asistente se retira.

## Instancia de la demo

| Qué | Valor |
|---|---|
| Carpeta | `%LOCALAPPDATA%\HACK-WhatsApp\ciclo`, fuera de OneDrive y de git |
| Claves (DPAPI, cifradas para el usuario de Windows) | `%LOCALAPPDATA%\HACK-WhatsApp\claves` |
| Perfil de Hermes | `hackaton-demo`, vacío, con `SOUL-hackaton-demo.md` |
| Mutex y tarea programada | `Local\HACK_WhatsApp_Ciclo` y `HACK WhatsApp - Demo` |
| Número de WhatsApp | 607 145 471, con una cuenta de Zernio propia |
| ERP | BALTER, **empresa ficticia** de la demo |
| Etiqueta del bot | «🤖 Asistente Virtual Vigía:» |
| Pruebas desde el móvil | Primer mensaje que empieza por **`HTEST`** |

**Barreras de seguridad:**
- El instalador se para si una clave coincide con una de producción protegida.
- También se para si la clave de Zernio ve más de un número, o si el número no es el de la demo.
- Antes de leer o crear nada, el ciclo comprueba que el catálogo de la empresa de la clave de BALTER tiene el **artículo de control**. Ese artículo solo existe en la empresa de la demo.

**Instalación de producción en el mismo equipo:** si la hay, se declara en el `.env` **local** del repositorio, que no se sube a git, separando varios valores con `;`:
```
HACK_PROTEGER_CLAVES=<carpetas de %LOCALAPPDATA% con las claves .dpapi de producción>
HACK_PROTEGER_CICLO=<carpeta de %LOCALAPPDATA% del ciclo de producción>
HACK_PROTEGER_MUTEX=<mutex de producción>
HACK_PROTEGER_PERFIL=<perfil de Hermes de producción>
```

## Puesta en marcha

Antes de empezar, añade `%LOCALAPPDATA%\HACK-WhatsApp` y la carpeta del repositorio a las excepciones del antivirus. Ejecuta cada bloque en PowerShell, desde la carpeta del repositorio.

**1 · Clave de BALTER de la empresa de la demo**
```
cls
powershell -ExecutionPolicy Bypass -File .\whatsapp-hack\HACK-ClaveBalter.ps1
```
- Pega la clave; no se verá.
- Elige por número un artículo del catálogo que solo exista en la empresa de la demo.
- Escribe `DEMO`.

**2 · Instalar**
```
cls
powershell -ExecutionPolicy Bypass -File .\whatsapp-hack\HACK-Instalar.ps1
```
- Zernio: `USAR`, si está en el `.env`, o pégala.
- BALTER: Intro.
- Artículo de control: Intro.
- Escribe `DEMO`.

**3 · Pruebas sin conexión.** Tienen que terminar con `0 fallos`.
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo-Pruebas.ps1"
```

**4 · Leer solo los chats nuevos.** Frase: `PRODUCCION`.
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarProduccion
```

**5 · Arrancar en segundo plano.** Frase: `AUTOMATICO`.
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarFondo -Segundos 10
```
- Revisa el WhatsApp cada 10 segundos, oculto, sin depender de ninguna ventana.
- Cada minuto, el Programador de tareas comprueba que sigue vivo y lo relanza si se ha caído.
- Funciona mientras la sesión de Windows esté iniciada (puede estar bloqueada). Para que el equipo no se suspenda: `powercfg /change standby-timeout-ac 0`.

**Ver en directo** (cerrar esta ventana no lo para):
```
cls
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Monitor
```

**Parar:** `-Parar`. **Otros comandos:** `-Estado`, `-Revisiones`, `-Ignorar <ID>`, `-Retomar <ID>`, y sin parámetros (modo REVISAR: no envía ni crea).

## Crear fichas de prueba

1. **Primer mensaje:** `HTEST: Hola, soy <nombre>. <consulta>`. Con `HTEST`, el chat es una prueba aunque el teléfono ya esté en BALTER (por ejemplo, como empleado):
   - no se busca ni se envía el teléfono;
   - la ficha se crea como contacto nuevo, con las etiquetas `DEMO`, `Vigia` y `PRUEBA_IA_HERMES`.
2. **Datos:** cuando lo pida, da nombre con apellidos y un **correo ficticio nuevo** cada vez.
3. **Otra ficha desde el mismo móvil:** ejecuta `-NuevaPrueba`. El bucle puede seguir en marcha. Archiva sin borrar las conversaciones de prueba; lo escrito antes ya no cuenta.

## Después del evento

1. Ejecuta `-Parar`.
2. Borra en BALTER las oportunidades y los contactos con la etiqueta `DEMO`, y las conversaciones en Zernio.
3. Borra `%LOCALAPPDATA%\HACK-WhatsApp`.
