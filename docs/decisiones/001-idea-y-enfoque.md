# 001. Idea: qué problema resuelve nuestro agente

- **Fecha:** 2026-11-24
- **Estado:** propuesta. **Decide el equipo.**
- **Origen:** reto 04 «La IA como servicio» (`docs/reto/`)

## Contexto

El reto pide un agente que **identifique necesidades reales, decida y ejecute tareas de forma autónoma** para empresas y ciudadanos, **más allá de los asistentes tradicionales** («actúa, conecta servicios, genera valor»). Se entregan un canvas (modelo de negocio), el prototipo con el uso de la IA, el marketing y el guion del pitch.

Habrá unas 200 personas. Muchos equipos harán «un chatbot que responde y reserva citas». Para diferenciarnos necesitamos:
- un agente que **haga algo verificable en el mundo**;
- un **problema con cifras**;
- **alguien que pague** (canvas).

Nuestra ventaja del Malackathon es demostrar el efecto real («un clic no es prueba») y cuadrar el dinero al céntimo.

**Criterios de comparación** (inferidos; hay que confirmar la rúbrica con los mentores):
1. Problema real y medible.
2. El agente **actúa** de verdad.
3. Demostrable de principio a fin en unas 3–4 h.
4. Modelo de negocio claro (quién paga).
5. Impacto en empresas **y** ciudadanos.
6. Diferenciación entre 200.
7. Encaje con nuestras fortalezas.

## Opciones evaluadas

> **Actualización 2 (24/11):** el equipo descartó por básicas todas las opciones de abajo, incluidas las de la primera ampliación (COBRA, RECLAMA, LICITA, TE TOCA, VATIO). Se rehízo la búsqueda partiendo de **problemas documentados** y de la evidencia sobre qué agentes funcionan; los detalles están en [`docs/ideas.md`](../ideas.md). Hay una propuesta principal y dos alternativas:
> - **Propuesta principal:** TERRAL, un agente de cuidado proactivo ante el calor extremo para mayores que viven solos.
> - **Alternativa A:** expedientes de dependencia.
> - **Alternativa B:** recuperar las citas perdidas.
>
> La tabla siguiente queda como historial.

| | A. Agente de cobros para pymes y autónomos | B. Agente de ayudas para ciudadanos | C. Agente de incidencias urbanas | D. Agente de atención y reservas para comercio local |
|---|---|---|---|---|
| **Qué hace** | Lee facturas emitidas y movimientos del banco. Detecta las vencidas, decide la acción según el cliente y su historial (recordatorio → aviso formal → reclamación con intereses de demora), la ejecuta y **solo cierra la factura cuando el cobro aparece en el banco y cuadra al céntimo** | Detecta a qué ayudas tiene derecho una familia (IMV, complemento por infancia, bono social, alquiler…), prepara el expediente y los documentos, rellena la solicitud y vigila plazos y requerimientos | El ciudadano envía una foto o un audio. El agente clasifica, geolocaliza, agrupa duplicados, abre el aviso en el servicio correcto, hace seguimiento y **verifica la resolución** con una foto posterior | Atiende por WhatsApp, reserva, cobra la señal y recuerda la cita |
| **Problema con cifras (por verificar)** | Plazo medio de pago de 67 días frente al límite legal de 60; el 85 % de las grandes empresas incumple (PMcM 2025) | El 52 % de quienes tienen derecho al IMV no lo pide; en el complemento por infancia, el 71 % (AIReF, 2026) | Tiempos de resolución y duplicados en los avisos municipales (sin cifra todavía) | Llamadas perdidas y ausencias (sin cifra todavía) |
| **¿Actúa?** | ✅ Envía, reclama, concilia y cierra | 🟡 Prepara y rellena; presentar exige certificado o Cl@ve del ciudadano | ✅ Abre y sigue avisos (sistema municipal simulado) | ✅ Reserva y cobra |
| **Demo en 3–4 h** | ✅ Bandeja de correo + extracto bancario (CSV o banco de prueba) + envío real a un correo de demo | ✅ Reglas de elegibilidad + PDF rellenado | 🟡 Necesita imágenes, mapa y sistema de avisos simulado | ✅ |
| **Quién paga** | ✅ La pyme o el autónomo (suscripción o % de lo recuperado); asesorías como canal | 🟡 Ayuntamientos, servicios sociales, ONG o bancos (B2G/B2B2C): ciclo de venta lento | 🟡 Ayuntamiento (B2G) | ✅ El comercio |
| **Empresas y ciudadanos** | Empresas; autónomos como ciudadanos | Ciudadanos; administración como cliente | Ambos | Empresas |
| **Diferenciación** | Alta: poca competencia en un hackathon de estudiantes; el «cuadra al céntimo» es nuestro | Alta en impacto; riesgo de que el jurado lo vea como un buscador de ayudas | Media: idea frecuente | **Baja: será la idea más repetida** |
| **Riesgos** | Tono de las reclamaciones (relación con el cliente); acceso real al banco (en la demo, CSV o sandbox) | Consejo legal erróneo (mitigación: motor de reglas citando la norma y la IA solo extrae datos); datos muy sensibles | Visión poco fiable con fotos reales | Copiable |

**Descartada D:** es lo que hará la mayoría.

## Recomendación (pendiente de decisión del equipo)

**A, el agente de cobros**, con B como alternativa fuerte.

**Por qué A:**
- Es el que más claramente **actúa**: envía, reclama, concilia y cierra.
- Tiene un ROI fácil de contar en el pitch: euros recuperados y días de cobro reducidos.
- El canvas es sencillo, porque paga quien sufre el problema.
- Encaja con la regla que nos hizo ganar: **una factura solo se cierra cuando el dinero está en el banco y cuadra al céntimo**.
- La IA tiene un papel claro y explicable:
  - extraer datos de facturas y correos;
  - decidir la acción y el tono según el historial del cliente;
  - redactar el mensaje.
- Reglas deterministas para lo que no puede fallar: plazos legales, intereses e importes.
- Aprobación humana configurable para las acciones de más riesgo.

**Tesis candidata (A):** «Un agente que dice que ha cobrado no prueba nada: el nuestro solo cierra una factura cuando el dinero está en el banco».

**Tesis candidata (B):** «La ayuda existe, pero la mitad no la pide: un agente que no informa, tramita».

## Consecuencias

Se completan cuando el equipo decida: stack, MVP de la demo y reparto. Al aceptar se actualizan la «Tesis» y el «Enfoque aceptado» de `CLAUDE.md` y el «Rumbo» de `docs/ESTADO.md`.

## Fuentes

- PMcM, *Informe sobre morosidad 2025*, a través de [Forbes](https://forbes.es/economia/907227/el-85-de-las-grandes-empresas-incumple-los-plazos-legales-de-pago-segun-pmcm/) y [Ara](https://es.ara.cat/economia/gran-empresa-administraciones-retardan-pago-pymes-autonomos_1_5709465.html). Cifras de prensa: hay que contrastarlas con el informe original antes del pitch.
- AIReF, quinta opinión sobre el IMV (julio de 2026), a través de [Artículo14](https://www.articulo14.es/economia/el-toque-final-de-la-airef-al-imv-pide-su-completa-remodelacion-para-incentivar-el-empleo-20260724.html) y [El Salto](https://www.elsaltodiario.com/renta-basica/55percent-hogares-podrian-recibir-imv-no-lo-han-solicitado-segun-airef). Hay que contrastarlas con el informe original.
