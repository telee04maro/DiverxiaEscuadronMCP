# Ideas para el reto 04 (versión 2: desde problemas reales)

Documento de trabajo para elegir la idea (ADR 001). **Es interno: sale del repositorio antes de entregar.**

La versión 1 (cobros, reclamaciones, licitaciones, ayudas, luz) se descartó por básica: partía de la tecnología. Queda en el historial de git. Esta versión parte de **problemas documentados** y de **qué hace que un agente funcione de verdad**. Viene de tres investigaciones en paralelo: problemas en España, problemas en Málaga y agentes desplegados en 2025–2026.

Las cifras llevan su fuente. Lo marcado *(por verificar)* hay que contrastarlo con la fuente primaria antes del pitch.

---

## 1. Qué hace que un agente no sea básico (según la evidencia)

Gartner prevé que **más del 40 % de los proyectos de IA agéntica se cancelarán** antes de 2028 por coste, valor poco claro y controles débiles. MIT encontró que el **95 % de los pilotos** de IA generativa no tienen impacto medible. Los que funcionan comparten rasgos, y esos son nuestros criterios:

1. **Proactivo:** lo dispara un evento real (un aviso, un plazo, un dato), no una pregunta.
2. **Sobre datos y sistemas reales**, al menos una API pública viva.
3. **Mezcla reglas y LLM:** reglas donde son fiables y el modelo solo donde hay ambigüedad.
4. **Autonomía por niveles:** actúa solo en lo reversible y una persona decide lo irreversible o de alto riesgo (Reglamento de IA, Anexo III).
5. **Comprueba su propio resultado** y lo deja trazado. Es nuestra seña del Malackathon.
6. **Mide un antes y un después.** En España casi nadie publica cifras de impacto de agentes, así que medir ya diferencia.
7. **Enseña su modo de fallo:** qué hace cuando duda.
8. **Tiene un pagador claro** y un camino a producción.

Además, las **bases oficiales** puntúan innovación, impacto, adecuación al reto, viabilidad técnica y económica, **uso estratégico y responsable de la IA**, implementación, entregables, evolución, equipo y pitch. Por su parte, **Diverxia** premia la innovación social con impacto medible (ODS, retos sociales y rurales). En sus palabras: valores medioambientales y sociales.

---

## 2. Los problemas que encontramos (resumen)

| Problema | Cifra principal | Fuente | ¿Encaja con un agente? |
|---|---|---|---|
| **Calor extremo y mayores solos** | **144 muertes** atribuibles a la temperatura en Málaga del 1/1 al 6/9/2026, frente a **58 en todo 2025**. En España, 3.832 en el verano de 2025, el 96 % mayores de 65 | MoMo (Ministerio de Sanidad), vía [El Español](https://www.elespanol.com/malaga/20260909/calor-ceba-malaga-muertes-atribuibles-temperatura-doble/1003744374744_0.html) y [La Moncloa](https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/sanidad14/paginas/2025/021025-garcia-calor-extremo-mortalidad.aspx) | ✅✅ |
| **Dependencia: se muere esperando** | **21.374 personas** murieron en lista de espera de enero a septiembre de 2026; en Andalucía, 39.505 en espera y 402 días de media | [Observatorio de la Dependencia, vía Corresponsables](https://www.corresponsables.com/actualidad/mas-de-21-000-personas-fallecen-esperando-atencion-a-la-dependencia-durante-los-nueve-primeros-meses-de-2026/) | ✅ |
| Citas sanitarias perdidas | Málaga: 8,7 días de espera para el médico de familia; solo el 19,3 % se atiende en 48 h. Alrededor del 20 % de inasistencias *(por verificar)* | [El Español](https://www.elespanol.com/malaga/vivir/salud/20260319/malaga-registra-espera-media-dias-cita-medico-cabecera-solo-dan-horas/1003744175435_0.html) (estudio no oficial) | ✅ |
| Notificaciones y burocracia de autónomos | 226 h al año por autónomo *(ATA, estimación patronal)* | [Artículo14](https://www.articulo14.es/economia/el-coste-de-la-burocracia-para-los-autonomos-se-dispara-casi-400-euros-el-ultimo-ano-20260811.html) | 🟡 Requiere certificado digital |
| Vivienda (problema nº 1 de Málaga, 47 %) | Alquiler +80 % desde 2021 | [El Español (MADECA)](https://www.elespanol.com/malaga/20260413/preocupacion-movilidad-malaga-triplica-segundo-problema-provincia-detras-vivienda/1003744204220_0.html) | 🟡 Políticamente sensible; datos cerrados |
| Movilidad (del 4,6 % al 12 % de preocupación) | Atascos en la A-7; 26,7 M de pasajeros en el aeropuerto | MADECA, Aena | 🟡 Buenos datos abiertos, pero el agente informa más que actúa |
| Desabastecimiento de medicamentos | 1.194 presentaciones con problemas de suministro (primer semestre de 2025) | [AEMPS](https://www.aemps.gob.es/medicamentosUsoHumano/problemasSuministro/informes-semestrales/docs/primer-informe-semestral-problemas-suministro-2025.pdf) | 🟡 Existe CISMED |
| Agua (sequía) | Los embalses están al 92–95 % en 2026 | El Español | ❌ Ya no es urgente |

**Lo que más pesa:** dos investigaciones independientes llegaron por separado al **mismo primer puesto**: el calor extremo y los mayores que viven solos.

---

## 3. IDEA PRINCIPAL: agente de cuidado proactivo ante el calor extremo

**Nombre provisional:** TERRAL (el viento de Málaga que dispara las temperaturas).

**Tesis:** «Para un mayor que vive solo en plena ola de calor, el silencio no es un "estoy bien"».

### El problema
- En Málaga, **144 muertes atribuibles a la temperatura** hasta el 6/9/2026, frente a **58 en todo 2025**. Solo julio de 2026 sumó 72, frente a 18 en julio de 2025 (MoMo, vía El Español).
- En España, **3.832 muertes** atribuibles al calor del 16/5 al 30/9/2025, **un 87 % más** que en 2024. **El 96 % eran mayores de 65** y el 65 % mayores de 85 (Ministerio de Sanidad).
- En Málaga capital viven solas unas **25.075 personas de 65 años o más** (Observatorio Municipal, Padrón 2021).
- El Servicio Andaluz de Teleasistencia tiene **43.710 usuarios en Málaga**. Según datos de 2023, el 59 % vive solo y el 68 % tiene 80 años o más *(por verificar)*.

### Por qué no está resuelto
- La **teleasistencia es reactiva**: el mayor tiene que pulsar el botón, y quien se desorienta por el calor no lo pulsa.
- Los **avisos de AEMET no se cruzan** con quién es vulnerable en cada calle.
- En un pico de calor los **teleoperadores no llegan** a llamar a todos a tiempo, y **nadie distingue** quién no contestó de quién está bien.
- Existen programas de acompañamiento (Siempre Acompañados, voluntariado), pero **ninguno se activa automáticamente por el riesgo meteorológico**.

### Qué hace el agente (detecta → decide → actúa → comprueba)
1. **Detecta:** consulta cada día la predicción y los avisos de **AEMET OpenData** (API pública real) por municipio y zona.
2. **Decide a quién y en qué orden.** Calcula un riesgo individual con **reglas explicables**: temperatura prevista y noches tropicales, edad, si vive solo, patologías, aire acondicionado, movilidad y si no ha respondido antes. Prioriza y elige el canal y la hora: antes del pico de calor, nunca a la hora de la siesta.
3. **Actúa:**
   - Contacta por el canal de cada persona (WhatsApp, llamada o SMS) con mensajes cortos y adaptados.
   - **Entiende la respuesta** con Claude: señales de confusión, mareo, «no tengo agua», «no puedo bajar a por la compra».
   - Ejecuta la acción adecuada: consejos concretos, aviso a un familiar, petición de visita a los servicios sociales, ubicación del espacio climatizado más cercano o reserva de transporte.
4. **Comprueba:**
   - **Un caso no se cierra hasta que hay un contacto verificado.**
   - Sin respuesta: reintento por otro canal, luego un familiar y luego el profesional. **El silencio nunca cuenta como «bien».**
   - Vuelve a comprobar en las horas críticas a quien dijo estar mal.
5. **Una persona decide lo grave.** Ante una posible emergencia, el agente **prepara el caso y avisa al operador humano** con todo el contexto: no llama solo al 112. El triaje de emergencias es de alto riesgo en el Reglamento de IA. Este control por niveles es justo lo que valora el criterio de «uso responsable de la IA».
6. **Informa:** panel en directo para el ayuntamiento o la teleasistencia (contactados, verificados, en riesgo, escalados, sin contacto) y un informe del episodio de calor con su antes y su después.

**Fuera de las olas de calor**, el mismo agente sirve para la **soledad no deseada** (contacto periódico), las **olas de frío** y las campañas de vacunación. Aporta valor todo el año, no solo en verano.

### Por qué no es básico
| Criterio | Cómo lo cumple |
|---|---|
| Proactivo | Lo dispara un aviso real de AEMET, no una pregunta |
| Datos reales | API de AEMET OpenData; zonas y espacios públicos de los datos abiertos de Málaga |
| Reglas + LLM | Riesgo y escalado con reglas explicables; el lenguaje (entender respuestas, adaptar mensajes) con Claude |
| Autonomía por niveles | Contacta y aconseja solo; para lo grave, prepara el caso y decide una persona |
| Se comprueba | «El silencio no es un sí»: no hay caso cerrado sin contacto verificado |
| Antes y después | Tiempo en contactar a todos los vulnerables: el operador frente al agente |
| Modo de fallo visible | Respuestas ambiguas → al humano, con el motivo |
| Pagador | Ayuntamiento, Junta o adjudicatarias de teleasistencia |

### Prototipo en el hackathon
- **Real:**
  - la llamada a AEMET OpenData;
  - el motor de riesgo;
  - Claude interpretando respuestas y decidiendo;
  - las conversaciones reales por WhatsApp o un chat web con móviles del equipo;
  - el panel del operador en directo;
  - el registro auditable de cada decisión.
- **Sintético:** el registro de personas vulnerables. **Las bases prohíben usar datos personales sin autorización**, así que serán 200 personas ficticias realistas, generadas por nosotros.
- **Simulable:** forzar un aviso rojo para la demo si ese día no hay calor (mismo formato que AEMET).

### Demo de 3 minutos
1. «Mañana, aviso rojo por terral en Málaga: 42 °C» (formato real de AEMET).
2. El agente prioriza a **200 personas** en segundos y explica el porqué de las 5 primeras.
3. Contacta en directo. Tres compañeros hacen de mayores en sus móviles:
   - una responde bien;
   - otra dice «estoy un poco mareada y se me ha acabado el agua» → el agente lo entiende, avisa a la hija y abre un caso urgente para el operador con todo el contexto;
   - la tercera **no contesta** → reintento por otro canal → escala. **No la marca como «bien».**
4. Panel: 200 contactados, 197 verificados, 2 escalados y 1 en manos del operador, con tiempos.
5. Cifra final: lo que a un equipo de teleoperadores le lleva horas, el agente lo hace en minutos, y **ninguna persona queda sin verificar**.

### Hasta el MVP (unas 3–4 h)
1. Generador del registro sintético y motor de riesgo con reglas.
2. Cliente de AEMET OpenData y aviso simulado con el mismo formato.
3. Bucle del agente con Claude: decidir, redactar, interpretar y escalar.
4. Canal de conversación: chat web primero; WhatsApp en modo de pruebas si da tiempo.
5. Panel del operador y registro de acciones.

### Canvas (resumen)
| Bloque | Contenido |
|---|---|
| Segmento | **Cliente:** ayuntamientos (Derechos Sociales), la Junta (teleasistencia), empresas adjudicatarias de teleasistencia y aseguradoras de salud. **Usuario:** mayores vulnerables y sus familias |
| Propuesta de valor | Llegar a cada persona vulnerable **antes** del pico de calor y saber, con certeza, quién está bien y quién no |
| Canales | Licitaciones y contratos de teleasistencia, pilotos con el Ayuntamiento de Málaga, alianza con adjudicatarias |
| Relación | Servicio gestionado con operador humano al mando |
| Ingresos | Cuota por persona protegida al mes, añadida al contrato de teleasistencia, o licencia municipal anual |
| Recursos | Agente, motor de riesgo, integraciones (AEMET, canales), cumplimiento normativo |
| Actividades | Desarrollo, cumplimiento del Reglamento de IA y del RGPD, pilotos |
| Socios | Ayuntamiento, Junta, AEMET (datos), proveedores de teleasistencia, ONG de mayores |
| Costes | IA (se medirá por persona y episodio), mensajería y llamadas, infraestructura en la UE |

### Marketing
- **Nombre:** TERRAL (provisional; hay que comprobar la marca).
- **Eslogan:** «Que el calor no pille a nadie solo.» / «El silencio no es un estoy bien.»
- **Logo:** un sol con un corazón o una mano en el centro.
- **Estrategia:**
  - Mensaje de impacto social con datos de Málaga.
  - Piloto con un distrito.
  - Campaña a familias de mayores.
  - Prensa local antes del verano.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Datos de salud muy sensibles | Minimización, base legal pública (servicio social) y procesamiento en la UE. En el hackathon, solo datos sintéticos |
| Que el agente se equivoque con alguien en riesgo | Ante la duda escala; el humano decide lo grave; todo queda trazado |
| Mayores poco digitales | La llamada de voz como canal principal en producto; en la demo, chat o WhatsApp |
| «Ya existe la teleasistencia» | Es reactiva; el agente la vuelve proactiva y se integra con ella, no la sustituye |
| Transparencia | Se identifica como asistente de IA (Reglamento de IA, art. 50) |

---

## 4. ALTERNATIVA A: agente de expedientes de dependencia para los servicios sociales

**Tesis:** «En nueve meses, 21.374 personas murieron esperando una ayuda que ya les correspondía».

- **Problema:**
  - Andalucía tiene 39.505 personas en espera y 402 días de media, la tercera peor de España.
  - En España, 10.621 de los fallecidos de 2026 **ya tenían la prestación reconocida** (Observatorio de la Dependencia).
  - Los expedientes llegan incompletos, no hay triaje por riesgo vital y faltan trabajadores sociales.
- **Qué hace el agente:**
  - Recibe la documentación, detecta lo que falta y lo pide.
  - Propone la **prioridad por riesgo vital**, siguiendo la Instrucción 1/2026 de la Junta *(por verificar)*.
  - Redacta un borrador del informe social, vigila los plazos legales y, cuando se vencen, prepara la reclamación.
  - El trabajador social decide: la elegibilidad para prestaciones públicas es de alto riesgo según el Reglamento de IA.
- **Por qué es fuerte:** es el mayor impacto del listado.
- **Por qué es más débil para hoy:**
  - Sin datos reales ni APIs, todo sería sintético.
  - Se parece a la idea de ayudas que ya rechazamos.
  - La demo impresiona menos.
- **Encaje con la idea principal:** es la **ampliación natural**. Las personas que esperan la dependencia son las mismas que más sufren el calor.

## 5. ALTERNATIVA B: agente que recupera las citas perdidas en clínicas privadas

**Tesis:** «Cada hueco que nadie ocupa es un paciente que espera y dinero que se pierde».

- **Problema:**
  - Alrededor del 20 % de inasistencias *(por verificar)*.
  - Los recordatorios actuales (AviSAS, Doctoralia) **avisan pero no reasignan**.
- **Qué hace el agente:**
  - Confirma la cita entre 48 y 72 h antes, conversando: entiende «no puedo, ¿el jueves?».
  - Libera el hueco y **se lo ofrece en cascada** a la lista de espera, por prioridad y cercanía.
  - Reagenda y mide los huecos recuperados.
- **Por qué es fuerte:** el retorno económico es el más claro y la clínica privada paga ya.
- **Por qué es más débil:** el impacto social es menor y puede parecer un sistema de reservas.

---

## 6. Recomendación

**La idea principal, TERRAL.**
- Es el problema con los **datos oficiales más duros y más locales**: Málaga casi triplica sus muertes por calor en un año.
- Lo eligieron por separado dos investigaciones independientes.
- Cumple los 8 rasgos de un agente que funciona.
- Usa una **API pública real** (AEMET).
- Tiene una **demo muy emocional** con un momento clave: la persona que no contesta y el agente que **no se conforma con el silencio**. Es nuestro «un clic no es prueba» del Malackathon, aplicado a personas.
- Encaja con lo que premia Diverxia, que es el impacto social medible.

La dependencia queda como ampliación en la hoja de ruta del pitch. Las citas perdidas, como plan B si los mentores dicen que pesa más el negocio.

## 7. Lo que hay que hacer ya (lo decide el equipo)

- **Pedir la clave gratuita de AEMET OpenData:** llega por correo y tarda unos minutos.
- Preguntar a la organización por el **tamaño del equipo**: las bases hablan de 6 y somos 3.
- Preguntar a los mentores si pesa más el **impacto o el negocio**.
