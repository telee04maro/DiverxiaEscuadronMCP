# Entregable 4 · Guion del pitch: Vigía

**Duración base:** 3 minutos, con un bloque opcional para llegar a 5. Hay que ajustarla al tiempo real que dé la organización.
**Un único presentador** y otra persona manejando la demo.
**Regla de oro:** amplitud en el pitch, profundidad en la demo.

| Tiempo | Qué se dice | Qué se ve |
|---|---|---|
| **0:00–0:25 · El gancho** | «Ana tiene una clínica de fisioterapia en Málaga con 15 personas. La gestoría le lleva los impuestos, una agencia las redes y ella, las cuentas en un Excel. Desde septiembre entran menos pacientes, y cada proveedor le dice que lo suyo va bien. Todos tienen razón: **cada uno ve su parte**.» | Logo y eslogan |
| **0:25–0:45 · La solución** | «Vigía es un equipo de expertos de IA para toda la pyme. Hay un agente por área, cada uno con sus propias fuentes, y **un coordinador que cruza lo que ve cada uno**. No es otro chat: detecta, decide, actúa y comprueba que ha funcionado.» | Pestaña 1, «Analizar con el equipo de agentes» |
| **0:45–1:25 · Los especialistas** | «El agente de finanzas lee el banco y las facturas: **la caja aguanta 9 días** y una aseguradora paga a 95 días. El de competencia lee la Biblioteca de Anuncios de Meta: **la clínica de al lado lanzó hace 18 días una primera sesión a 20 €** y promete "sin esperas". Y el 86 % de las reseñas recientes de Ana se quejan de la espera. El de atención lee el ERP: **el 59 % de las consultas por WhatsApp llegan fuera de horario y tardan 12 horas en contestarse; se pierde el 41 %, cuando en horario no se pierde ninguna**.» | Pestaña 2: hallazgos con su evidencia |
| **1:25–2:00 · La causa cruzada** *(el momento clave)* | «Ningún proveedor ve esto. El coordinador lo cruza: **no es la temporada**, porque el año pasado no bajó. **Se pierden particulares por precio y por espera, también cuando escriben por la noche, justo lo que la competencia promete resolver.** Y la caja no aguanta una guerra de precios.» | Pestaña 3: causa cruzada y descartado «es la temporada» |
| **2:00–2:30 · Actúa, con control** | «El plan a 7, 30 y 90 días ya está en marcha. El recordatorio amable **lo ha enviado solo**; la reclamación formal a la aseguradora **espera a que Ana la apruebe**. La contraoferta la propone competencia y **la valida finanzas**: a 20 € cada paciente nuevo dejaría un 21 % menos, así que propone 30 € con cita en 48 horas.» | Pestaña 4: aprobar y enviar |
| **2:30–2:50 · Mide** | «Un mes después, Vigía comprueba qué ha funcionado. Una factura solo cuenta como cobrada cuando **el pago aparece en el banco**: de lo reclamado a la aseguradora, ya hay 2 de 3 facturas cobradas. Con el asistente de WhatsApp, las consultas de fuera de horario pasan de 12 horas a minutos de respuesta, y las quejas por la espera bajan del 86 % al 50 %. Vigía dice que **coincide**, no que lo pruebe. Lo que no funcionó vuelve al plan de esta semana.» | Pestaña 5 |
| **2:50–3:00 · Cierre** | «Suscripción desde 99 € al mes, con 4 céntimos de IA por análisis, y la vendemos a través de las gestorías, que ya tienen la confianza de las pymes. **Cada proveedor ve su parte. Vigía ve la causa.**» | Logo |

### Bloque opcional (+2 minutos)
- **Uso responsable de la IA** (pestaña 6). «Las reglas calculan y la IA interpreta. Todo lo que escribe la IA se comprueba contra los datos: una cifra, una fecha, una cuenta bancaria o un enlace que no estén en ellos y el texto se descarta. Claude no ve los nombres de quien debe dinero. Cada decisión queda registrada y el coste se mide.»
- **Escala.** Añadir un especialista (marketing, legal, personas) es enchufar un módulo: el coordinador cruza sus hallazgos sin cambios y solo se añaden sus acciones al plan. Hay unas 1,36 millones de pymes con asalariados en España.

## Preguntas probables del jurado

| Pregunta | Respuesta corta |
|---|---|
| ¿En qué se diferencia de ChatGPT? | Está conectado a los datos de la empresa, cada agente tiene sus fuentes, actúa (envía, reclama, propone) y **mide si funcionó**. ChatGPT te responde; Vigía te dice la causa y cierra el ciclo |
| ¿Y si se equivoca en algo legal o de dinero? | Autonomía por niveles: solo actúa sin preguntar en lo reversible. Lo serio lo aprueba una persona o lo revisa un experto. Las cifras de dinero las calculan reglas, no la IA |
| ¿Cómo conseguiréis clientes? | A través de **gestorías y asesorías**: ya tienen la confianza de miles de pymes y Vigía les permite ofrecer más que impuestos |
| ¿Los datos de la demo son reales? | La clínica es **ficticia**: las bases prohíben datos personales. Los datos de la competencia son instantáneas con el formato exacto de las APIs oficiales (Meta Ad Library, Search Console, Places). Lo hemos verificado en `docs/fuentes.md` |
| ¿Cuánto cuesta la IA? | **Medido:** 0,04 $ por análisis y 0,07 $ con los correos de reclamación; unos 0,30 $ por empresa y mes con un análisis semanal, frente a 99 € de suscripción. El panel mide cada llamada y hay un tope por ejecución. Sin clave de IA, el producto funciona igual con reglas |
| ¿Por qué solo tres especialistas? | Porque tres agentes muy buenos valen más que seis a medias: finanzas, competencia, y atención y captación funcionan de verdad, con sus fuentes, y se cruzan. Marketing, legal y personas están en la hoja de ruta: la arquitectura permite enchufarlos y el coordinador cruza sus hallazgos sin cambios |
| ¿La re-medición prueba que la acción causó la mejora? | No, y lo decimos: indica que **coincide en el tiempo**. Lo que sí se comprueba son los cobros, contra el extracto del banco |
| ¿Cómo sabéis que la IA no se inventa cifras? | Cada cifra que escribe (importes, porcentajes, días) se busca en los datos con su unidad; una cuenta bancaria, un enlace, un teléfono o un plazo que no estén en los datos descartan el texto y se usa una plantilla. Con Claude real: 3 causas y 2 correos aceptados, 0 descartados. Hay tests con textos inventados que lo demuestran |
| ¿Qué hacéis con los datos personales? | Lo mínimo: las reseñas se guardan sin nombres, teléfonos ni correos; Claude lee «Aseguradora 1» en vez del nombre de quien debe dinero; «Borrar todos los datos» los borra también del disco. Detalle en `docs/datos-personales.md` |
