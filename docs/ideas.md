# Ideas para el reto 04: cómo sería cada una

Documento de trabajo para elegir la idea (ADR 001). **Es interno: sale del repositorio antes de entregar.**

Las cifras marcadas *(por verificar)* vienen de prensa o de estudios sectoriales: hay que contrastarlas con la fuente original antes del pitch. Los nombres son provisionales (hay que comprobar marcas antes de usarlos).

---

## 1. Qué busca el reto y cómo filtramos

El reto premia un agente que **detecta una necesidad, decide y ejecuta**, y que va «más allá de los asistentes tradicionales». Los entregables (canvas, marketing, pitch) dicen que se evalúa **un negocio**, no solo una demo técnica.

Filtro que aplicamos a cada idea (puntuación de 1 a 5, subjetiva, a confirmar con la rúbrica real):

| Criterio | Pregunta |
|---|---|
| **Problema** | ¿Es real y se puede contar con una cifra? |
| **Actúa** | ¿El agente hace algo en el mundo, o solo informa? |
| **Demo** | ¿Se puede enseñar de principio a fin con lo que construimos en 3–4 h? |
| **Negocio** | ¿Está claro quién paga y por qué? |
| **Alcance** | ¿Sirve a empresas **y** ciudadanos? |
| **Diferencia** | ¿Lo harán otros 20 equipos? |
| **Encaje** | ¿Aprovecha lo que sabemos hacer (verificar el efecto real, cuadrar el dinero, automatizar webs)? |

## 2. Lista larga y descartes rápidos

| Idea | Veredicto | Motivo |
|---|---|---|
| Chatbot de reservas y atención para comercio (WhatsApp) | ❌ | Lo harán muchos equipos; es un «asistente tradicional» |
| Agente de incidencias urbanas (foto → aviso al ayuntamiento) | ❌ | Idea frecuente; la visión con fotos reales es poco fiable para una demo |
| Agente de citas médicas y medicación para mayores | ❌ | Necesita credenciales sanitarias reales; difícil de demostrar sin simularlo todo |
| Agente gestor fiscal del autónomo (gastos, trimestrales, Verifactu) | 🔶 | Bueno, pero solapa con COBRA; queda como ampliación de COBRA |
| **COBRA**: agente de cobros para pymes y autónomos | ✅ Finalista | |
| **RECLAMA**: agente que recupera el dinero del consumidor | ✅ Finalista | |
| **LICITA**: agente de licitaciones públicas para pymes | ✅ Finalista | |
| **TE TOCA**: agente de ayudas públicas para familias | ✅ Finalista | |
| **VATIO**: agente que revisa la factura de la luz y la optimiza | ✅ Finalista (más débil) | |

## 3. Comparativa de finalistas

| | Problema | Actúa | Demo | Negocio | Alcance | Diferencia | Encaje | **Total /35** |
|---|---|---|---|---|---|---|---|---|
| **COBRA** | 5 | 5 | 5 | 5 | 3 | 4 | 5 | **32** |
| **RECLAMA** | 4 | 5 | 4 | 4 | 3 | 3 | 5 | **28** |
| **LICITA** | 4 | 3 | 4 | 5 | 3 | 5 | 4 | **28** |
| **TE TOCA** | 5 | 3 | 4 | 2 | 4 | 4 | 4 | **26** |
| **VATIO** | 4 | 3 | 3 | 4 | 3 | 2 | 3 | **22** |

---

## 4. Lo que comparten todas: el núcleo del agente

Cualquiera de las ideas se construye con el mismo esqueleto, así que **E0 puede empezar antes de elegir**:

```
Conectores (entrada)  →  Percibir  →  Decidir  →  Actuar  →  Comprobar el efecto  →  Registro e informe
 correo, CSV del banco,   extraer     reglas +    enviar,    ¿llegó el dinero?        cada paso con su
 datos abiertos, PDF      datos (IA)  IA (tono,   rellenar,  ¿respondieron?           evidencia; panel
                                      prioridad)  reclamar   ¿cambió el estado?       para el usuario
```

- **La IA (Claude) hace** lo que necesita lenguaje: extraer datos de documentos y correos, clasificar, decidir el siguiente paso entre opciones acotadas y redactar los mensajes.
- **Las reglas deterministas hacen** lo que no puede fallar: importes, plazos legales, intereses, elegibilidad y la conciliación al céntimo.
- **El humano aprueba** las acciones de más riesgo (configurable: «todo automático», «aprobar las reclamaciones formales», «aprobarlo todo»).
- **Nunca se da algo por hecho sin comprobar su efecto.** Esta es nuestra seña del Malackathon.
- Todo queda en un **registro de acciones** visible: qué vio, qué decidió, qué hizo y qué comprobó. Es el mejor material para la demo y para «explicad cómo habéis usado la IA».

---

## 5. COBRA: el agente que cobra tus facturas

**Tesis:** «Un agente que dice que ha cobrado no prueba nada: COBRA solo cierra una factura cuando el dinero está en tu banco».

### Problema
- Las empresas tardan de media **67 días** en pagar a sus proveedores, frente al límite legal de 60, y el **85 % de las grandes empresas** incumple *(PMcM 2025, por verificar)*.
- Quien más lo sufre es la pyme y el autónomo: perseguir facturas consume horas, es incómodo y muchas veces no se reclaman ni los intereses de demora que marca la ley.

### Para quién y quién paga
- **Usuario y cliente:** pymes y autónomos que facturan a otras empresas (servicios, construcción, agencias, proveedores de hostelería…).
- **Canal:** asesorías y gestorías, que llevan decenas de clientes cada una y pueden ofrecerlo como servicio.

### Qué hace el agente
1. **Percibe:** lee las facturas emitidas (PDF o un listado del programa de facturación) y los movimientos del banco (CSV o banco de prueba).
2. **Detecta:** qué facturas han vencido, cuánto y desde cuándo; también los pagos parciales y los que no se pueden identificar.
3. **Decide** la siguiente acción para cada cliente según su historial y la antigüedad de la deuda:
   - recordatorio amable;
   - segundo aviso;
   - reclamación formal con los intereses de demora calculados;
   - escalar al humano (por ejemplo, un cliente estratégico).
4. **Actúa:** redacta y envía el correo con el tono adecuado; propone un plan de pagos si el cliente responde que no puede pagar; agenda el siguiente seguimiento.
5. **Comprueba:** cruza el banco; una factura **solo pasa a «cobrada» cuando entra el importe exacto, de ese cliente, al céntimo**. Si entra de menos, la deja «parcial» y sigue.
6. **Informa:** un panel con lo recuperado, los días medios de cobro y lo que queda pendiente.

### Por qué no es un asistente tradicional
No espera a que le preguntes: vigila, decide y actúa solo dentro de los límites que fija el usuario, y demuestra el resultado con el dinero en el banco.

### Dónde va la IA y dónde no
| IA (Claude) | Reglas deterministas |
|---|---|
| Extraer datos de facturas y respuestas de clientes | Vencimientos, importes, intereses de demora (Ley 3/2004) |
| Entender la respuesta del cliente («pago el viernes», «no recibimos la factura») y decidir el siguiente paso | Conciliación al céntimo con el banco |
| Redactar el mensaje con el tono adecuado | Límites: nunca reclamar a quien ya pagó ni enviar dos avisos el mismo día |

Coste de IA: **se medirá** por factura gestionada (presumiblemente céntimos).

### Prototipo (qué es real y qué simulado)
- **Real:** extracción de facturas PDF, motor de reglas, decisiones con Claude, envío real de correos a buzones de demo, lectura de un extracto CSV y conciliación.
- **Simulado:** el banco (un CSV que «recibe» un pago durante la demo) y los clientes (buzones del equipo que responden).
- **Pantallas:** panel de facturas por estado, ficha de un cliente con el historial de acciones y un registro del agente.

### Demo de 2 minutos
1. Panel con 6 facturas vencidas de 3 clientes y 4.800 € pendientes.
2. «Ejecutar agente»: decide y envía tres correos distintos (amable, segundo aviso, reclamación formal con intereses). Se enseña cada correo y **por qué** eligió ese tono.
3. Un «cliente» responde «pagaremos la mitad ahora y la mitad el mes que viene». El agente lo entiende, propone el plan de pagos y agenda el seguimiento.
4. Entra un pago en el banco por **1 céntimo menos**: el agente **no** la cierra y avisa. Entra el pago correcto: la cierra.
5. Panel final: euros recuperados y días medios de cobro.

### Hasta el MVP (unas 3–4 h)
1. Datos de demo: facturas PDF, clientes y CSV del banco.
2. Extracción de facturas + motor de reglas (vencidas, intereses).
3. Decisión y redacción con Claude + envío de correo.
4. Conciliación con el CSV + cambio de estado.
5. Panel web mínimo + registro de acciones.

### Canvas (resumen)
| Bloque | Contenido |
|---|---|
| Segmento | Pymes y autónomos B2B; asesorías como canal |
| Propuesta de valor | Cobra antes sin perseguir a nadie y sin romper la relación con el cliente; demuestra cada euro recuperado |
| Canales | Asesorías, integraciones con programas de facturación, asociaciones de autónomos y empresarios |
| Relación | Autoservicio con aprobación humana configurable |
| Ingresos | Suscripción mensual por tramos de facturas + opción de % sobre lo recuperado en reclamaciones formales |
| Recursos clave | Agente, motor de reglas legales, integraciones bancarias y de facturación |
| Actividades clave | Desarrollo, cumplimiento legal y de privacidad, integraciones |
| Socios | Asesorías, bancos (open banking), programas de facturación |
| Costes | IA (medido por factura), infraestructura, ventas a través de asesorías |

### Marketing
- **Eslogan:** «Tú facturas. COBRA cobra.» / «Cobrar ya no es tu trabajo.»
- **Logo:** una C que se cierra como un círculo de verificación (✔): la factura «se cierra» al cobrarse.
- **Estrategia:** casos reales de autónomos («recuperé 3.200 € en un mes»), contenido sobre la ley de morosidad y alianzas con asesorías de Málaga como primeros clientes.

### Pitch
- **Gancho:** «¿Cuántos días tarda en pagarte tu peor cliente? La media en España son 67, y la ley dice 60».
- **Cifra estrella:** euros recuperados y días de cobro reducidos en la demo.
- **Cierre:** la tesis.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Que el agente dañe la relación con un cliente | Tono gradual, lista de clientes protegidos y aprobación humana de las reclamaciones formales |
| Que el jurado diga «ya existen programas de cobros» | Diferencia: decide y actúa solo, entiende las respuestas y **demuestra** el cobro conciliando con el banco |
| Acceso real al banco | En la demo, CSV; en producto, open banking |
| Datos de terceros | Mínimos, en la UE y con base legal de interés legítimo (por verificar con un experto) |

### Ampliaciones
Gestor fiscal del autónomo (gastos, trimestrales, preparación para Verifactu, que será obligatorio para autónomos el 1/7/2027 *(por verificar, se habla de retrasos)*) y predicción de riesgo de impago por cliente.

---

## 6. RECLAMA: el agente que recupera tu dinero

**Tesis:** «Te deben dinero y no lo sabes. RECLAMA lo encuentra, lo reclama y no para hasta que llega a tu cuenta».

### Problema
- Los consumidores pierden dinero que les corresponde por ley: retrasos y cancelaciones de vuelos (entre 250 y 600 € por pasajero según la distancia, Reglamento 261/2004), cargos indebidos, devoluciones que no llegan, garantías, suscripciones que siguen cobrando.
- **Solo reclama en torno al 30 %** de los pasajeros con problemas *(Refund.me vía Hosteltur, dato antiguo, por verificar)*. La mayoría no conoce sus derechos o desiste por pereza.

### Para quién y quién paga
- **Usuario:** el ciudadano.
- **Modelo:** comisión solo si cobra (habitual en el sector) o una suscripción familiar. Canal B2B2C: bancos, aseguradoras o agencias de viaje que lo ofrecen como ventaja a sus clientes.

### Qué hace el agente
1. **Percibe:** con permiso, revisa el correo (tarjetas de embarque, facturas, confirmaciones de pedidos) y los movimientos del banco.
2. **Detecta:** un vuelo con retraso de más de 3 h, un cargo duplicado, una devolución prometida que no ha llegado, una suscripción que debía cancelarse.
3. **Decide:** si hay derecho y cuánto, según reglas (distancia del vuelo → importe; plazos de devolución → reclamable).
4. **Actúa:** redacta y presenta la reclamación por el canal correcto (formulario o correo de la empresa) con los justificantes; si no responden en plazo, escala (hoja de reclamaciones, organismo de consumo, AESA en vuelos).
5. **Comprueba:** **solo cierra el caso cuando el dinero entra en la cuenta**.

### Por qué no es un asistente tradicional
No te explica tus derechos: los ejerce por ti, de principio a fin, y te enseña el dinero recuperado.

### Dónde va la IA y dónde no
| IA (Claude) | Reglas deterministas |
|---|---|
| Leer correos y documentos y detectar casos | Importe según distancia y retraso (Reglamento 261/2004), plazos legales |
| Redactar la reclamación y entender la respuesta de la empresa | Elegibilidad, cuándo escalar, conciliación con el banco |

### Prototipo
- **Real:** lectura de un buzón de demo, detección de casos, cálculo del importe, redacción y envío de la reclamación por correo a un buzón que hace de aerolínea, conciliación con un CSV.
- **Simulado:** el estado de los vuelos (datos de demo; una API real de vuelos sería una ampliación), la respuesta de la empresa y el banco.

### Demo de 2 minutos
1. Buzón de demo con 40 correos. «Analizar»: el agente encuentra 3 casos (un vuelo con 4 h de retraso → 400 €; un cargo duplicado de 59,99 €; una devolución de un pedido que no ha llegado).
2. Envía las tres reclamaciones y enseña una.
3. La «aerolínea» responde rechazándola por «circunstancias extraordinarias». El agente lo entiende, pide la justificación y escala.
4. Entra la devolución del cargo duplicado en el banco: caso cerrado. Panel: «Recuperado: 59,99 €. En curso: 400 €».

### Canvas (resumen)
| Bloque | Contenido |
|---|---|
| Segmento | Viajeros y consumidores digitales; B2B2C con bancos, aseguradoras y agencias |
| Propuesta de valor | Recupera el dinero que te deben sin que tengas que saber que te lo deben |
| Ingresos | % solo si se cobra; licencia B2B2C |
| Socios | Asociaciones de consumidores, bancos, abogados para los casos que van a juicio |
| Costes | IA por caso, gestión legal de los casos difíciles |

### Marketing
- **Eslogan:** «Lo tuyo, de vuelta.»
- **Logo:** una flecha que vuelve a una cartera.
- **Estrategia:** muy viral («este agente me ha recuperado 400 € de un vuelo»); campañas en verano y en épocas de huelgas.

### Pitch
- **Gancho:** «Levantad la mano si os han retrasado un vuelo. ¿Cuántos habéis cobrado los 400 €?».

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Ya existen empresas de reclamación de vuelos | Diferencia: **detección proactiva** en tu correo y banco, todo tipo de reclamaciones y cierre comprobado con el dinero |
| Acceso al correo personal (privacidad) | Permisos mínimos, solo lectura de remitentes relevantes, todo en la UE |
| Representación legal ante la empresa | Mandato del usuario; el agente no se hace pasar por él |

---

## 7. LICITA: el agente que encuentra y prepara concursos públicos para tu pyme

**Tesis:** «La administración compra cada día; la mayoría de pymes nunca se presenta. LICITA vigila, filtra y te deja la oferta lista para firmar».

### Problema
- La contratación pública mueve una parte enorme de la economía, pero **la mayoría de pymes nunca presenta una oferta**: no se enteran, no entienden los pliegos o no tienen tiempo para la documentación *(estudio CNMC E/CNMC/004/23, por verificar la cifra)*.

### Para quién y quién paga
Pymes que venden a la administración (obras, servicios, suministros, consultoría). Suscripción mensual; canal a través de asociaciones empresariales y cámaras de comercio.

### Qué hace el agente
1. **Percibe:** lee las **licitaciones reales** de la Plataforma de Contratación del Sector Público (datos abiertos).
2. **Decide:** puntúa cada licitación frente al perfil de la empresa (actividad, códigos CPV, zona, solvencia, tamaño) y explica por qué encaja o no.
3. **Actúa:** lee el pliego, extrae requisitos, criterios y plazos, prepara la lista de documentos y un borrador de la documentación administrativa (DEUC) y de la memoria técnica, y agenda los plazos.
4. **Comprueba:** valida que no falta ningún documento obligatorio antes de dar la oferta por lista; vigila aclaraciones y modificaciones del pliego.

La presentación final requiere el certificado de la empresa: el agente lo deja listo para firmar.

### Dónde va la IA y dónde no
| IA (Claude) | Reglas deterministas |
|---|---|
| Leer pliegos (PDF largos), resumir y extraer requisitos | Filtros de CPV, importe, zona y plazos |
| Explicar el encaje y redactar borradores | Lista de comprobación de documentos obligatorios |

### Prototipo
- **Real:** **datos abiertos reales de licitaciones** (es nuestra mayor baza de credibilidad), puntuación, lectura de un pliego real y generación de la lista de documentos y los borradores.
- **Simulado:** el perfil de la empresa y la presentación (no se presenta nada).

### Demo de 2 minutos
1. Perfil: «empresa de limpieza de Málaga, 15 empleados».
2. El agente revisa las licitaciones publicadas hoy y presenta 3 que encajan, con su porqué.
3. Abre una: resumen del pliego, requisitos de solvencia que **no** cumple la empresa (honestidad) y documentos necesarios.
4. Genera el paquete de la oferta y el calendario de plazos.

### Canvas (resumen)
| Bloque | Contenido |
|---|---|
| Segmento | Pymes que pueden vender a la administración y no lo hacen |
| Propuesta de valor | De «no me entero» a «oferta lista para firmar» |
| Ingresos | Suscripción por tramos; servicio premium de redacción revisada por expertos |
| Socios | Cámaras de comercio, asociaciones empresariales, consultoras de licitación |

### Marketing
- **Eslogan:** «Tu empresa también puede trabajar para lo público.»
- **Estrategia:** alianzas con cámaras de comercio y mensaje de impacto: más pymes compitiendo = mejores precios para todos.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Actúa menos (no presenta la oferta) | El valor está en encontrar y preparar; la firma es del cliente |
| Pliegos muy largos | Extracción por secciones y coste de IA medido |
| El jurado lo ve muy B2B y poco «ciudadano» | Enfoque de impacto: dinero público mejor repartido entre empresas locales |

---

## 8. TE TOCA: el agente de las ayudas que nadie pide

**Tesis:** «La ayuda existe, pero la mitad no la pide. TE TOCA no informa: tramita».

### Problema
- El **52 %** de los hogares con derecho al Ingreso Mínimo Vital no lo solicita, y en el complemento por infancia la cifra llega al **71 %** *(AIReF, quinta opinión, julio de 2026; por verificar en el informe original)*.
- Las ayudas son difíciles de encontrar, los requisitos son complejos y los trámites, una barrera.

### Para quién y quién paga
- **Usuario:** familias, mayores, personas en situación vulnerable.
- **Cliente:** ayuntamientos y servicios sociales (para aumentar su alcance), ONG y fundaciones, o bancos y aseguradoras como servicio social. Es un ciclo de venta lento: es la principal debilidad del canvas.

### Qué hace el agente
1. **Percibe:** una conversación sencilla (texto o voz) y documentos (nómina, libro de familia, contrato de alquiler).
2. **Decide:** a qué ayudas tiene derecho, según **reglas basadas en la normativa** y citando el artículo de cada una.
3. **Actúa:** prepara el expediente (documentos, formularios rellenados), pide la cita previa si aplica y avisa de plazos y requerimientos.
4. **Comprueba:** sigue el estado de la solicitud y recuerda la renovación.

La presentación requiere la identidad digital del ciudadano: el agente lo deja todo listo y le guía en el último paso.

### Dónde va la IA y dónde no
| IA (Claude) | Reglas deterministas |
|---|---|
| Conversación accesible y lectura de documentos | Elegibilidad según la normativa, con la cita a la norma |
| Explicar en lenguaje llano | Cálculo de importes y plazos |

### Demo de 2 minutos
Una madre con dos hijos y un contrato temporal cuenta su situación. El agente detecta 3 ayudas (con su importe estimado y la norma), rellena las solicitudes y crea el calendario de pasos.

### Canvas (resumen)
| Bloque | Contenido |
|---|---|
| Segmento | Familias vulnerables; administraciones y entidades sociales como clientes |
| Propuesta de valor | Que las ayudas lleguen a quien tiene derecho |
| Ingresos | Licencias a administraciones y entidades sociales; patrocinio social |

### Marketing
- **Eslogan:** «Te toca. Y te lo tramitamos.»
- **Estrategia:** a través de servicios sociales, colegios y ONG, con mensaje de impacto social.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Un error en la elegibilidad perjudica a una familia | Reglas citando la norma, la IA nunca decide la elegibilidad y siempre hay revisión humana |
| Datos muy sensibles | Minimización y procesamiento en la UE |
| Quién paga | Pilotos con ayuntamientos; en el pitch, el ahorro social y el alcance |

---

## 9. VATIO: el agente que revisa tu factura de la luz

**Tesis:** «Pagas potencia que no usas. VATIO lo detecta y lo cambia».

### Problema
- El **63 %** de los hogares tiene contratado, de media, **1,1 kW más** de potencia de la que usa en las horas punta *(Panel de Hogares de la CNMC)*.
- Hay unas **800 ofertas de más de 80 comercializadoras**: comparar es difícil *(CNMC)*.

### Qué hace el agente
1. Lee la factura (PDF).
2. Analiza el consumo.
3. Calcula la potencia y la tarifa óptimas.
4. Prepara la solicitud de cambio, que es gratuita.
5. Comprueba en la siguiente factura que el ahorro ha llegado.

### Por qué es más débil
- Ya hay comparadores, incluido el de la CNMC: hay poca diferencia.
- El ahorro por hogar es pequeño.
- Actuar de verdad exige la firma del titular.

Puede servir como ampliación de cualquiera de las otras («también revisa tus facturas»).

---

## 10. Recomendación

1. **COBRA:** es la opción más completa. Actúa de verdad, tiene una demo potente con el truco del céntimo, un modelo de negocio claro y nuestra seña de identidad.
2. **RECLAMA:** es la más emocional y fácil de contar al público. Tiene el riesgo de que digan «ya existe».
3. **LICITA:** es la más creíble porque usa datos reales. Es muy B2B y actúa menos.
4. **TE TOCA:** tiene el mayor impacto social, pero un negocio débil y actúa menos.

**Antes de decidir conviene preguntar a los mentores qué pesa más: impacto social o negocio.** Si pesa más el impacto, TE TOCA sube. Si pesa más el negocio, COBRA.

## Fuentes

- PMcM, informe de morosidad 2025, a través de [Forbes](https://forbes.es/economia/907227/el-85-de-las-grandes-empresas-incumple-los-plazos-legales-de-pago-segun-pmcm/) y [Ara](https://es.ara.cat/economia/gran-empresa-administraciones-retardan-pago-pymes-autonomos_1_5709465.html).
- AIReF sobre el IMV, a través de [Artículo14](https://www.articulo14.es/economia/el-toque-final-de-la-airef-al-imv-pide-su-completa-remodelacion-para-incentivar-el-empleo-20260724.html) y [El Salto](https://www.elsaltodiario.com/renta-basica/55percent-hogares-podrian-recibir-imv-no-lo-han-solicitado-segun-airef).
- Reclamaciones de vuelos: [Hosteltur (Refund.me)](https://www.hosteltur.com/121290_solo-30-espanoles-reclama-sus-derechos-como-pasajero.html) y [administracion.gob.es](https://administracion.gob.es/pag_Home/Tu-espacio-europeo/derechos-obligaciones/ciudadanos/viajes/pasajeros/avion.html).
- Contratación pública: [OIReScon, informe anual 2025](https://www.hacienda.gob.es/rsc/oirescon/informe-anual-supervision-2025/ias2025-modulo1.pdf) y [CNMC](https://www.cnmc.es/sites/default/files/6379840.pdf).
- Verifactu: [Infoautónomos](https://www.infoautonomos.com/blog/verifactu-cuando-es-obligatorio-a-quien-afecta/).
- Energía: [CNMC, Panel de Hogares](https://cnmc.es/prensa/panel-hogares-electricidad-gas-20260626?back=news).
