# Plan de negocio de Vigía: a quién vendemos, cuánto cobramos y si las cuentas salen

**Versión 1 · 25/11/2026.** Documento de trabajo del equipo. Cada cifra va marcada:
- **[verificado]:** comprobado en la fuente original;
- **[fuente secundaria]:** solo la hemos visto en prensa, blogs o webs comerciales;
- **[hipótesis]:** decisión o estimación nuestra, que hay que validar con el piloto.

El modelo financiero completo (36 meses, cuatro escenarios) está en `plan-de-negocio-modelo.py`. Todas las tablas de este documento salen de él.

## 1. La decisión en cinco líneas

1. **Vendemos a pequeñas empresas de 10 a 49 empleados, a través de sus gestorías y asesorías.** La gestoría recomienda Vigía y se lleva un **30 % recurrente** de lo que paga su cliente.
2. **Suscripción mensual con tres planes: 79 €, 149 € y 249 € al mes** (sin IVA). Se cobra por domiciliación bancaria, sin permanencia y con dos meses gratis si se paga el año entero.
3. **El Ayuntamiento de Málaga (o Promálaga) no es el cliente, sino el patrocinador del piloto:** un contrato menor de hasta 15.000 € para que 25 pymes de Málaga usen Vigía seis meses.
4. **Inversión necesaria: unos 106.000 € en el escenario base** (91.000 € con el piloto municipal), para llegar al **equilibrio mensual en el mes 16**.
5. **Si a los 6 meses no tenemos 5 gestorías activas y 25 clientes de pago**, estamos en el escenario prudente y hay que cambiar el plan (sección 10).

## 2. ¿A quién vendemos?

Hemos comparado cuatro opciones con los criterios que deciden si una startup de pymes sobrevive: si el cliente tiene el problema y presupuesto, lo que cuesta llegar a él, cuánto tarda en pagar y si se queda.

| | **A. Pymes directamente** | **B. A través de gestorías (elegida)** | **C. Ayuntamiento de Málaga o Promálaga** | **D. Asociaciones y Cámara de Comercio** |
|---|---|---|---|---|
| ¿Tiene el problema? | Sí: es quien pierde clientes y caja | Indirectamente: sus clientes lo tienen y le piden más que impuestos | No: el problema es de las pymes, no del ayuntamiento | No directamente |
| Coste de llegar | **Alto:** hay que convencer a cada pyme una a una, y no confía en un desconocido | **Bajo:** una gestoría trae a muchos clientes que ya confían en ella | Medio, pero el proceso es lento (contratación pública) | Bajo: dan acceso a sus socios |
| Acceso a los datos | Difícil al principio | **Fácil:** la gestoría ya lleva la contabilidad y las facturas, que es lo que necesita el agente de finanzas | — | — |
| Cuánto tarda en pagar | Rápido, pero de una en una | Rápido, y en grupo | **Lento:** expediente de contratación y presupuesto anual | — |
| Si se queda | Riesgo de bajas alto | Más estable: la pyme no deja a su gestoría a la ligera | Un contrato puntual, no recurrente | — |
| Ingreso por cliente | 100 % del precio | 70 % del precio (30 % a la gestoría) | Un contrato menor: máximo 15.000 € (servicios) | Ninguno directo |
| **Papel en el plan** | **Secundario:** entrada directa con el diagnóstico gratuito (25 % de los clientes) | **Principal** (75 % de los clientes) | **Patrocinador del piloto** y credibilidad | **Canal de difusión** (eventos, formación) |

**Por qué no el Ayuntamiento como cliente principal.** La Ley 9/2017 de Contratos del Sector Público solo permite contratos menores de servicios por debajo de 15.000 € [verificado en varias fuentes; conviene confirmar el artículo 118 en el BOE]. Por encima hace falta una licitación, que tarda meses. Además, el presupuesto municipal es anual y no recurrente, y el problema que resolvemos no es del ayuntamiento, sino de las pymes. Como patrocinador de un piloto sí encaja: le da a Málaga un programa visible de IA para su tejido empresarial y a nosotros, los primeros casos reales.

**Por qué las gestorías.**
- **Ganan dinero:** el 30 % recurrente.
- **Ganan valor:** pasan de «presentar impuestos» a «asesorar el negocio», con un producto que ya conecta con lo que llevan (contabilidad, facturas, bancos).
- **Defensa frente a la competencia:** las gestorías online compiten por precio. Una gestoría para una SL cuesta entre 150 y 600 € al mes según volumen y trabajadores [fuente secundaria: tarifas publicadas por gestorías online, 2026].

### Ayudas públicas revisadas: ninguna sirve ahora
- **Kit Consulting** (bonos de 12.000 a 24.000 € para pymes de 10 a 249 empleados): según las fuentes consultadas, **no hay convocatoria abierta** a octubre de 2026 [fuente secundaria]. Si se abre otra, Vigía podría ofrecerse a través de ella; no lo contamos en las cuentas.
- **Programa RedIA del Gobierno (180 millones):** ayudas de 400.000 € a 5 millones para proyectos de desarrollo de IA, **ya resueltas** (31/08/2026) [verificado en la nota de La Moncloa]. No sirve ni a las pymes para pagar Vigía ni a una startup que empieza.
- **Subvenciones de Promálaga a pymes (400.000 €, 2026):** plazo cerrado el 15 de octubre [fuente secundaria]. Hay que vigilar las próximas.

## 3. El cliente objetivo: pequeñas empresas de 10 a 49 empleados

| Dato | Cifra | Estado |
|---|---|---|
| Pequeñas empresas (10–49 asalariados) en España | **181.605** | [verificado] *Cifras PYME*, mayo de 2026 |
| Microempresas (1–9 asalariados) | 1.143.130 | [verificado] misma fuente |
| Empresas de 10 o más empleados que analizan sus propios datos | **34,3 %** | [verificado] INE, encuesta de uso de TIC en las empresas, 22/10/2026 |
| Empresas de 10 o más empleados con CRM | 33,9 % | [verificado] misma fuente |
| Grandes empresas que incumplen el plazo legal de pago | 85 % (plazo medio de 67 días; el legal es de 60) | [verificado a través de PIMEC, miembro de la PMcM] |

**Por qué 10–49 y no las microempresas:**
- tienen datos suficientes (banco, facturas, consultas) para que los agentes encuentren causas;
- pagan una gestoría de 350–600 € al mes [fuente secundaria], así que un plan de 149 € es asumible;
- es justo el grupo del dato del INE (dos de cada tres no analizan sus datos).

Las microempresas quedan para el plan Esencial, más adelante.

**Tamaño del mercado (cálculo nuestro):**
- **Mercado alcanzable en España:** 181.605 pequeñas empresas × 136 € de precio medio × 12 meses = **unos 296 millones de euros al año**.
- **Lo que esperamos captar:** el escenario base llega a 560 clientes en el año 3, es decir, el **0,3 %** de las pequeñas empresas. Es un objetivo modesto, y es a propósito.

**Málaga como mercado de inicio.** Es la cuarta provincia en creación de sociedades en 2025 (6.271) [fuente secundaria: prensa]. **No hemos verificado** el número de pymes con asalariados de la provincia; se puede consultar en la estadística de empresas inscritas en la Seguridad Social del Instituto de Estadística y Cartografía de Andalucía.

## 4. Cuánto cobramos y por qué

| Plan | Precio al mes (sin IVA) | Qué incluye | Para quién | Peso en la mezcla [hipótesis] |
|---|---|---|---|---|
| **Esencial** | **79 €** | Agente de finanzas, coordinador y plan mensual; recordatorios de cobro automáticos | Empresas pequeñas que empiezan | 40 % |
| **Profesional** | **149 €** | Los tres agentes (finanzas, competencia y atención), causas cruzadas, acciones con aprobación y medición mensual | El cliente tipo (10–49 empleados) | 45 % |
| **Avanzado** | **249 €** | Todo lo anterior, más **1 hora al mes de revisión de un asesor humano** en lo financiero y legal, y conectores a su ERP/CRM | Empresas con más volumen o más riesgo | 15 % |

**Precio medio por cliente: 136 € al mes.**

**Por qué estos precios:**
1. **Por debajo de lo que ya paga.** Una pyme de 10–49 empleados paga 350–600 € al mes de gestoría [fuente secundaria]. Vigía es un añadido de entre el 15 % y el 40 % de eso, no una factura del mismo tamaño.
2. **En la franja del software de gestión.** Un programa de gestión como Holded cuesta entre 15 y 199 € al mes [fuente secundaria: comparadores, 2026; la web oficial muestra menos planes]. El cliente ya entiende pagar esto por un software.
3. **Se paga solo.** En la demo, Vigía detecta 10.554 € vencidos y propone reclamarlos; cobrar **una sola factura** de 1.920 € paga más de un año del plan Profesional. *Es un ejemplo de la demo, no un dato del mercado.*
4. **Las cuentas lo piden.** Con estos precios, los costes fijos se cubren con **unos 135 clientes**. Con un precio medio de 81 € (por ejemplo, si casi todos eligieran el plan más barato), el equilibrio se retrasa al mes 25 y hacen falta **unos 173.000 €** (sección 9).

**Por qué por planes y no por uso:** la IA cuesta unos **0,30 $ por empresa y mes**, medido con Claude real [medido por el equipo]. No hace falta cobrar por consumo, y a la pyme le da tranquilidad saber cuánto va a pagar.

**Lo que no sabemos y hay que validar en el piloto:** cuántas pymes dicen que sí a cada precio. El modelo supone que el precio no cambia cuántos clientes entran, y en la realidad sí cambia. En el piloto haremos una encuesta de precio a las pymes de las gestorías (método de Van Westendorp) antes de fijar la tarifa definitiva.

## 5. Cómo cobramos

- **Suscripción mensual con domiciliación bancaria SEPA:** es como pagan las pymes a su gestoría. También con tarjeta.
- **Sin permanencia,** para quitar el miedo a probar. **Pago anual con dos meses gratis**, que adelanta caja y reduce las bajas.
- **Vigía factura directamente a la pyme y paga a la gestoría su 30 % cada mes.** Así:
  - la gestoría no tiene que facturar nada;
  - nosotros tenemos el contrato de tratamiento de datos con la pyme (RGPD);
  - sabemos de primera mano quién se da de baja.

  Más adelante, una **marca blanca** para gestorías grandes.
- **Diagnóstico inicial gratis** (lo público más un cuestionario de 10 minutos): es la puerta de entrada, no un ingreso.
- **Piloto municipal:** contrato menor de **15.000 €** con el Ayuntamiento o Promálaga para **25 pymes durante 6 meses**. Equivale a **100 € por pyme y mes**, en línea con nuestros precios. [hipótesis: hay que proponerlo y negociarlo]

## 6. Cuánto nos cuesta cada cliente

Coste variable por cliente y mes [hipótesis, salvo la IA, que está medida]:

| Concepto | € al mes |
|---|---|
| IA (Claude): 3 veces lo medido (0,30 $), como margen de seguridad | 1 |
| Infraestructura en la UE | 3 |
| Soporte y alta | 8 |
| Cobro (domiciliación o tarjeta, ≈ 1,5 %) | 2 |
| Asesor humano del plan Avanzado (1 h a 40 €, en el 15 % de los clientes) | 6 |
| **Total** | **20** |

| Por cliente y mes | Directo | A través de gestoría |
|---|---|---|
| Ingreso | 136 € | 95,20 € (136 € − 30 %) |
| Margen tras costes variables | **116 €** | **75,20 €** |
| Margen medio (75 % gestoría y 25 % directo) | **85 €** | |

Con unas bajas del 3 % al mes [hipótesis; las referencias del sector para software de pymes dan entre el 3 % y el 5 % mensual, fuente secundaria], un cliente dura de media 33 meses y deja **unos 2.850 € de margen** en ese tiempo. Captarlo cuesta entre **61 €** (solo marketing) y **190 €** (contando un fundador dedicado a ventas). La relación de unos **15 a 1 es probablemente optimista:** depende de cuántos clientes active de verdad cada gestoría, y eso solo lo dirá el piloto.

## 7. Costes fijos

[hipótesis]

| Concepto | € al mes |
|---|---|
| 3 fundadores a 2.200 € brutos (coste para la empresa ≈ bruto × 1,32; aproximado, a confirmar con la gestoría) | 8.712 |
| Infraestructura base, dominios y herramientas | 500 |
| Gestoría propia, seguros y asesoría legal (RGPD, Reglamento de IA) | 450 |
| Espacio (incubadora o coworking) | 300 |
| Marketing con gestorías (eventos, demos, contenido), desde el mes 4 | 1.500 |
| **Total** | **11.462** |
| Desde 150 clientes: una persona de soporte y ventas (1.800 € brutos) | + 2.376 |

**Clientes necesarios para cubrir los costes fijos:** 11.462 € ÷ 85 € ≈ **135 clientes**.

## 8. Inversión inicial y cómo financiarla

**Gastos de arranque [hipótesis]:**

| Concepto | € |
|---|---|
| Constitución de la SL, pacto de socios y notaría | 1.500 |
| Revisión legal inicial (RGPD, Reglamento de IA, contratos con gestorías) | 3.000 |
| Registro de la marca (OEPM y EUIPO) | 1.000 |
| Equipos | 4.500 |
| **Total** | **10.000** |

**Necesidad total de caja** (gastos de arranque más las pérdidas hasta el equilibrio), según el modelo:

| Escenario | Necesidad máxima de caja |
|---|---|
| Base | **106.474 €** |
| Base con piloto municipal | **91.474 €** |
| Prudente | 201.211 € |

**Cómo cubrir la del escenario base con piloto (unos 91.000 €) [hipótesis]:**
- **Fundadores:** 30.000 € (10.000 € cada uno).
- **Préstamo ENISA Jóvenes Emprendedores:** hasta 60.000 €. Esta línea va de 25.000 a 75.000 € y exige que los socios aporten al menos el 50 % del préstamo, así que con 30.000 € propios llega a 60.000 € [fuente secundaria; confirmar en la web de ENISA].
- **Piloto municipal:** 15.000 €.
- **Total: 105.000 €.** Cubre el escenario base con un pequeño colchón.

**En el escenario prudente (unos 200.000 €), con esto no basta.** Habría que conseguir inversores privados (business angels) o reducir los sueldos de los fundadores durante el primer año.

## 9. Plan a 36 meses

Suposiciones de cada escenario [hipótesis]:
- **Meses 1–3:** piloto con 3 gestorías de Málaga.
- **Desde el mes 4:** gestorías nuevas cada mes y clientes directos.
- **Cada gestoría aporta clientes durante 18 meses** y luego se satura.

| Escenario | Bajas al mes | Gestorías nuevas al mes | Mes de equilibrio | Necesidad máxima de caja | Clientes año 1 / 2 / 3 | Ingresos año 1 / 2 / 3 | Resultado año 1 / 2 / 3 |
|---|---|---|---|---|---|---|---|
| **Prudente** | 5 % | 1 | 34 | 201.211 € | 40 / 108 / 150 | 20.508 € / 94.102 € / 159.211 € | −116.504 € / −62.097 € / −12.610 € |
| **Base** | 3 % | 2 | 16 | 106.474 € | 105 / 354 / 560 | 48.664 € / 281.800 € / 557.565 € | −93.888 € / 63.850 € / 278.248 € |
| **Optimista** | 2 % | 3 | 12 | 80.171 € | 191 / 699 / 1.173 | 86.157 € / 542.834 € / 1.143.991 € | −68.274 € / 268.232 € / 746.341 € |
| **Base con piloto municipal** | 3 % | 2 | 16 | 91.474 € | 105 / 354 / 560 | 63.664 € / 281.800 € / 557.565 € | −78.888 € / 63.850 € / 278.248 € |

Clientes nuevos por gestoría activa al mes: 0,5 (prudente), 0,8 (base) y 1,0 (optimista). Clientes directos al mes: 1, 2 y 4.

### Sensibilidad: el precio pesa más que las bajas

Escenario base, cambiando el precio y las bajas. Cada celda indica el mes de equilibrio y la necesidad de caja:

| Precio medio | Bajas del 2 % | Bajas del 3 % | Bajas del 5 % |
|---|---|---|---|
| 81 € (precio × 0,6) | mes 23 · 167.172 € | mes 25 · 173.196 € | mes 28 · 185.621 € |
| 109 € (× 0,8) | mes 18 · 126.736 € | mes 19 · 130.122 € | mes 20 · 135.153 € |
| **136 € (propuesto)** | mes 14 · 104.089 € | **mes 16 · 106.474 €** | mes 15 · 109.150 € |
| 163 € (× 1,2) | mes 13 · 92.859 € | mes 13 · 94.085 € | mes 13 · 96.409 € |

**Lectura de la tabla:**
- Bajar precios para captar más clientes **sale caro**: con un precio medio de 81 € hacen falta 65.000 € más.
- **Una rareza explicada:** con bajas del 5 % el equilibrio llega un mes antes que con el 3 %. Con menos bajas se llega antes a 150 clientes y se contrata a la persona de soporte, lo que retrasa un mes el equilibrio. No es un error del modelo.
- **Lo que de verdad decide** entre el escenario prudente y el base no está en esta tabla: es **cuántas gestorías se activan y cuántos clientes trae cada una**.

## 10. Hitos y decisiones

| Cuándo | Hito | Si no se cumple |
|---|---|---|
| Mes 3 | 3 gestorías del piloto con al menos 10 clientes usando Vigía; encuesta de precio hecha | Revisar la propuesta para las gestorías (comisión, formación) antes de crecer |
| Mes 6 | **5 gestorías activas, 25 clientes de pago y bajas por debajo del 5 % al mes** | Estamos en el escenario prudente: reducir sueldos, buscar business angels o reforzar la venta directa |
| Mes 12 | 100 clientes de pago | Replantear el precio o el segmento |
| Mes 16 | Equilibrio mensual | — |

## 11. Riesgos principales

1. **Que las gestorías no lo empujen.** Es el riesgo número uno. Se mitiga con el 30 % recurrente, formación y un panel propio para la gestoría.
2. **Confianza para dar acceso al banco.** Se mitiga con el diagnóstico gratuito sin acceso a sistemas, la supervisión humana en el plan Avanzado y el cumplimiento del RGPD y del Reglamento de IA.
3. **Competidores grandes** (programas de gestión que añadan IA). Nuestra diferencia es cruzar áreas y comprobar los resultados, más el canal de gestorías.
4. **Errores de la IA en dinero o temas legales.** Las cifras las calculan reglas, no la IA; lo serio lo aprueba una persona y el plan Avanzado incluye a un asesor humano.

## 12. Qué cambia en el canvas y en el pitch (pendiente de aprobar)

- **Ingresos:** de «99 € a 399 €» a **79, 149 y 249 €**. En el pitch: «desde 79 € al mes».
- **Canales:** gestorías como canal principal, con el **30 % recurrente**; el Ayuntamiento o Promálaga como **patrocinador del piloto**.
- **Costes e inversión:** unos 91.000–106.000 € para llegar al equilibrio en el mes 16 (escenario base).

## 13. Fuentes

| Dato | Fuente | Estado |
|---|---|---|
| Pymes por tamaño (181.605 pequeñas, 1.143.130 microempresas, 1.355.023 con asalariados) | Ministerio de Industria, *Cifras PYME*, mayo de 2026: <https://ipyme.org/Publicaciones/Cifras%20PYME/CifrasPyme_mayo_2026.pdf> | Verificado en el PDF |
| Análisis de datos (34,3 %), CRM (33,9 %) e IA (33,6 %) en empresas de 10 o más empleados | INE, nota de prensa de la encuesta de uso de TIC en las empresas, 22/10/2026: <https://www.ine.es/dyngs/Prensa/ETICCE20251T2026.htm> | Verificado |
| Morosidad: 67 días de plazo medio y el 85 % de las grandes empresas incumplen | PMcM, recogido por PIMEC el 05/05/2026: <https://pimec.org/es/actualidad/noticia/n/la-pmcm-reclama-reformar-urgentemente-la-ley-para-combatir-los-retrasos-en-los-pagos> | Verificado a través de PIMEC |
| Programa RedIA (180 millones) | La Moncloa, 31/08/2026: <https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/transformacion-digital-y-funcion-publica/paginas/2026/310826-reparto-fondos-ia-empresas.aspx> | Verificado |
| Contrato menor de servicios por debajo de 15.000 € | Ley 9/2017, art. 118 (por ejemplo, el resumen de la Universidad de Málaga: <https://www.uma.es/media/files/NOTA_INFORMTIVA_UMA-CONTRATOS_MENORES_I.pdf>) | Fuente secundaria; confirmar en el BOE |
| Precio de una gestoría para una SL (150–600 € al mes) | Tarifas publicadas por gestorías online, 2026 (por ejemplo, <https://www.billeo.es/blog/cuanto-cobra-gestoria-llevar-empresa>) | Fuente secundaria (sesgo comercial) |
| Holded, de 15 a 199 € al mes | Comparadores, 2026 (por ejemplo, <https://www.infoautonomos.com/?p=102949>); web oficial: <https://www.holded.com/es/precios> | Fuente secundaria |
| Kit Consulting (12.000–24.000 €), sin convocatoria abierta | Webs de agentes y consultoras (por ejemplo, <https://laayudadigital.com/kit-consulting-2026/>) | Fuente secundaria |
| ENISA Jóvenes Emprendedores (25.000–75.000 €; 50 % de fondos propios) | Por ejemplo, <https://www.bankinter.com/blog/finanzas-personales/programa-jovenes-emprendedores-enisa> | Fuente secundaria; confirmar en enisa.es |
| Bajas en software para pymes (3–5 % al mes) | Por ejemplo, <https://www.saastr.com/which-is-the-churn-benchmark-for-saas>, <https://churnkey.co/blog/whats-a-normal-churn-rate-in-saas/> | Fuente secundaria (sin un estudio de referencia) |
| Subvenciones de Promálaga a pymes (400.000 €, plazo hasta el 15/10) | Ayuntamiento de Málaga: <https://www.malaga.eu/visorcontenido/ANUDocumentDisplayer/179960/COMUNICADO.pdf> | Fuente secundaria (comunicado) |
| Creación de sociedades en Málaga en 2025 (6.271) | El Debate: <https://www.eldebate.com/espana/andalucia/malaga/20260408/malaga-segunda-provincia-espanola-empresas-creo-2025-cada-mil-habitantes_404045.html> | Fuente secundaria (prensa) |
| Coste de la IA (0,30 $ por empresa y mes) | Medido por el equipo con Claude real (`docs/uso-ia.md`) | Medido |
