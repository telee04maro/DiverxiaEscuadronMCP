# Entregable 1 · Lienzo del reto: Centra (versión 1)

Plantilla oficial del Hackathon IA First («Lienzo del reto: del reto a la solución validada con IA»).

- **Equipo:** EscuadronMCP
- **Reto:** 04 · La IA como servicio
- **Fecha:** 24/11/2026

> **Cada proveedor ve su parte. Centra ve la causa.**

| Bloque | Contenido |
|---|---|
| **Clientes** (quién paga) | Pymes de servicios de 5 a 50 empleados (clínicas, despachos, academias, talleres, comercio) sin director financiero ni de marketing: unas **1,36 millones de pymes con asalariados** en España¹. Gestorías y asesorías (**62.234**²), que lo revenden a sus clientes |
| **Usuarios** (quién lo usa) | **El dueño o gerente**: pregunta y aprueba desde WhatsApp o desde el panel. **Su equipo**: recibe tareas con fecha. **Los clientes de la pyme**: el agente los atiende por WhatsApp. **La gestoría**: supervisa |
| **Problemas** | 1) **La gestión está repartida** (gestoría, agencia, Excel, WhatsApp): nadie cruza la información y los problemas se ven tarde. 2) **Se pierde dinero sin verlo**: cobros vencidos (el plazo medio de pago son 67 días, frente a los 60 legales³), consultas de WhatsApp sin responder, clientes que se van a la competencia. 3) **El dueño no tiene tiempo ni presupuesto** para analizar, decidir y comprobar si lo que hace funciona; una consultora es cara y puntual |
| **Soluciones** (con la IA como herramienta) | **Agentes especialistas con sus propias fuentes:** **Finanzas** (banco y facturas: caja, cobros, reclamaciones conciliadas al céntimo), **Competencia** (anuncios, precios, reseñas, Google) y **Atención y captación** (WhatsApp → ERP/CRM sin duplicados). **Coordinador con IA** (Claude): cruza los hallazgos, encuentra la causa y crea un plan a 7, 30 y 90 días. **Actúa con autonomía por niveles** (solo hace lo seguro; lo serio lo aprueba el dueño o un experto) y **vuelve a medir** al mes. Las reglas calculan y la IA interpreta y redacta; todo se verifica |
| **Propuesta de valor** | **Un equipo de expertos de IA para toda tu pyme, en un solo sitio.** Te dice por qué pierdes dinero o clientes, qué hacer esta semana, lo hace por ti y comprueba si ha funcionado. Por menos de lo que cuesta un día de consultoría al mes |
| **Ventaja competitiva** (difícil de copiar) | **La causa cruzada:** ve lo que gestoría, agencia y CRM no ven por separado. **Cierra el ciclo:** actúa y mide el efecto (un cobro solo cuenta si cuadra con el banco al céntimo), no se queda en un informe. **Confianza verificable:** IA verificada, registro auditable y supervisión humana. **Canal de gestorías** y aprendizaje acumulado de cada empresa. **IA fuera del bucle caliente:** céntimos por análisis |
| **Actividades clave** | Desarrollar agentes y conectores (banco, ERP/CRM, WhatsApp, Meta Ad Library, Google). Mantener las reglas financieras y legales y verificar el efecto de cada acción. Cumplir el RGPD y el Reglamento de IA. Pilotos y alianzas con gestorías |
| **Aliados** (objetivo) | Gestorías y asesorías. Asociaciones empresariales y cámaras de comercio (piloto en Málaga). ERP, CRM y programas de facturación (integraciones). Bancos y agregadores de open banking. Anthropic (modelos Claude). Meta (WhatsApp Business) y su pasarela. Asesores financieros y abogados para la supervisión |
| **Recursos** | **Modelos de IA:** Claude Opus 5.5 (cruzar y redactar) y Haiku 5.5 (clasificar). **Datos:** banco, facturas, ERP/CRM y WhatsApp de la pyme, más fuentes públicas (Meta Ad Library, Search Console, Google Places). **Tecnología:** Python, motor de reglas, conectores, panel e infraestructura en la UE. **Equipo:** producto e IA, integraciones, negocio, y una red de expertos humanos |
| **Canales** | Gestorías, como marca blanca o servicio añadido. Pilotos en Málaga con asociaciones y cámaras. Contenido «la causa cruzada de la semana» (LinkedIn) y eventos. Prueba directa: la pyme conecta su WhatsApp y ve resultados en la primera semana |
| **Fidelización** | **Valor medido cada mes:** «lo que has recuperado» (euros cobrados, clientes, nota en reseñas). **Plan vivo** que se reordena con cada medición. **Crecimiento por módulos** (marketing, legal, personas). Referidos entre gestorías (un mes gratis) |
| **Costes** (incluidas la IA y la infraestructura) | **IA:** ≈ 0,10–0,15 $ por análisis completo (estimación; se mide en cada ejecución y hay un tope de gasto), unos 0,50–0,60 $ al mes por empresa con un análisis semanal, más la atención por WhatsApp por conversación. **Mensajería de WhatsApp Business** (las plantillas proactivas se pagan; *tarifas por verificar*). **APIs de datos** (Google Places, a partir de su cuota gratuita). **Infraestructura en la UE.** Equipo de producto e integraciones. Supervisión experta. Comisión a gestorías |
| **Ingresos** | **Suscripción por módulos y tamaño:** base de 79 €/mes hasta 10 empleados y 149 €/mes de 10 a 50. **Módulos** a 39 €/mes cada uno: captación por WhatsApp, marketing, legal, personas. **Supervisión experta** en un plan superior o por horas. **Gestorías:** precio mayorista o reparto de ingresos |

## Versión 1 (lo que enseña la demo)

**Construido y verificado en modo reglas:** Finanzas, Competencia y Coordinador, con acciones reales (reclamaciones con aprobación) y re-medición. Datos sintéticos de una clínica ficticia de Málaga.

**Módulo de captación por WhatsApp:** en integración. Se apoya en la infraestructura de un compañero, que se declarará como componente previo tras confirmarlo con la organización.

**Caso de la demo:**
- Caja para 9 días.
- 10.554,10 € vencidos; Mutua Beta paga a 95 días.
- Las sesiones de particulares caen un 15,4 %, y el año pasado no bajaron.
- La clínica de al lado ofrece la primera sesión a 20 € y promete «sin esperas».
- El 86 % de las reseñas recientes se quejan de la espera.
- **Causa cruzada:** se pierden particulares por precio y espera, y la caja no aguanta una guerra de precios.
- **Plan:**
  - reclamar lo vencido (un recordatorio enviado solo y una reclamación formal aprobada);
  - contraoferta validada por finanzas: 30 € y no 20 €, porque a 20 € cada paciente nuevo dejaría un 21 % menos;
  - cita en 48 horas.
- **Un mes después:** cobradas al céntimo 3 de las 4 facturas reclamadas, y lo que no funcionó vuelve al plan.

## Fuentes

1. Ministerio de Industria, *Cifras PYME*, mayo de 2026: <https://ipyme.org/Publicaciones/Cifras%20PYME/CifrasPyme_mayo_2026.pdf>
2. INE, DIRCE a 1/1/2025, citado por Legalitas: <https://www.legalitas.com/actualidad/futuro-gestorias>
3. Plataforma Multisectorial contra la Morosidad, 2025, vía Forbes: <https://forbes.es/economia/907227/el-85-de-las-grandes-empresas-incumple-los-plazos-legales-de-pago-segun-pmcm/>
