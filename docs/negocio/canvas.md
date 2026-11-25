# Entregable 1 · Lienzo del reto: Pymbrain (versión 1)

Plantilla oficial del Hackathon IA First («Lienzo del reto: del reto a la solución validada con IA»). Une la propuesta del equipo con lo construido en el prototipo. Frases cortas para que quepan a mano.

- **Equipo:** EscuadronMCP · **Proyecto:** Pymbrain (nombre provisional)
- **Reto:** 04 – La IA como servicio
- **Fecha:** 24–25/11/2026

## Clientes (quién paga)
- Pymes tradicionales de 10 a 49 empleados (clínicas, hostelería, comercio, talleres, despachos).
- Gestorías y asesorías, que lo ofrecen a sus clientes.

## Usuarios (quién lo usa)
- El dueño o gerente: pregunta y aprueba desde el panel o por WhatsApp.
- Los responsables de cada área.
- El asesor de la gestoría, que supervisa.

## Problemas
1. La gestión está repartida entre proveedores que no se comunican: se decide sin el contexto completo. Solo **una de cada tres** empresas de 10 o más empleados analiza sus propios datos (INE, 2026; fuente 4).
2. No detectan a tiempo dónde pierden dinero (cobros, caja) ni clientes, ni en qué les supera la competencia. El **85 %** de las grandes empresas incumple el plazo legal de pago (PMcM, 2025; fuente 3).
3. No tienen dinero ni tiempo para una consultora ni para tener departamentos propios.

## Soluciones (con la IA como herramienta)
- Agentes especialistas con sus propias fuentes. **Ya funcionan:** finanzas (banco y facturas), competencia (anuncios, precios, reseñas, Google) y atención y captación (consultas del ERP/CRM y WhatsApp).
- Un coordinador con IA que cruza los hallazgos, encuentra la causa y prioriza por impacto, esfuerzo y urgencia.
- Plan a 7, 30 y 90 días: ejecuta lo seguro, lo delicado lo aprueba una persona, y mide si funcionó.
- Entra con sus Excel o con su ERP/CRM. **Hoja de ruta:** marketing, legal, RR. HH. y organización.

## Propuesta de valor
**«Tu negocio grita, nosotros escuchamos.»** Cada proveedor ve su parte; Pymbrain ve la causa. Todos los departamentos de tu pyme decidiendo juntos, con todo el contexto… y ejecutando.
- Te dice por qué pierdes dinero o clientes.
- Plan priorizado y adaptado a cada pyme.
- Actúa y comprueba el resultado: no es un informe que se queda en un cajón.

## Ventaja competitiva
- Decide cruzando todas las áreas, algo que los proveedores por separado no pueden hacer.
- **Los datos que acumula de cada empresa:** cuanto más tiempo lleva, mejores son sus decisiones.
- **La red de gestorías** como canal de confianza.
- **Ciclo cerrado y verificable:** un cobro solo cuenta si aparece en el banco; expertos humanos supervisan lo legal y lo financiero.

## Actividades clave
- Desarrollar y mejorar los agentes.
- Conectarlos con las herramientas de la empresa (contabilidad, banco, CRM, reseñas, anuncios).
- Entrevista inicial y diagnóstico de cada empresa.
- Mantener al día la normativa (RGPD, Reglamento de IA, obligaciones de las pymes).
- Revisión humana de las recomendaciones delicadas.

## Recursos
- **IA:** Claude (Opus 5.5 para cruzar y redactar; Haiku 5.5 para clasificar), con orquestación propia en Python.
- **Datos:** los de la propia pyme y fuentes públicas (Biblioteca de Anuncios de Meta, reseñas, BOE).
- **Equipo:** técnico, de negocio y expertos en legal y finanzas.
- Alojamiento en la UE (RGPD) y la IA por API, sin entrenar con los datos de la pyme.

## Aliados
- Gestorías y asesorías.
- Asociaciones empresariales y Cámara de Comercio.
- Promálaga e incubadoras.
- Abogados y economistas colaboradores.
- Integraciones: banca, ERP y CRM.

## Canales
- Venta a través de gestorías.
- Diagnóstico gratuito online como gancho.
- Ferias y asociaciones (piloto en Málaga).
- LinkedIn y contenido («la causa cruzada de la semana»).

## Fidelización
- Plan que se actualiza cada mes.
- Informe mensual de resultados: dinero recuperado, clientes recuperados.
- Cuanto más tiempo lleva la empresa, más afinado es el servicio; dejarlo supone perder ese conocimiento.
- Nuevos módulos a medida que crece.

## Costes
- Uso de los modelos de IA: **0,04 $ por análisis, medido** (0,07 $ con los correos de reclamación); unos 0,30 $ por empresa y mes con un análisis semanal. Tope de gasto por ejecución.
- Infraestructura y seguridad (UE).
- Desarrollo.
- Expertos humanos.
- Captación de clientes y comisiones a las gestorías.

## Ingresos
- Suscripción mensual en tres planes: **79 €, 149 € y 249 € al mes** (sin IVA), sin permanencia (hipótesis del plan de negocio: hay que validarla con el piloto).
- Diagnóstico inicial gratis como gancho; el plan con ejecución es de pago.
- Licencia en marca blanca para gestorías; la gestoría que recomienda Pymbrain se lleva un 30 % recurrente.

---

**Aviso para el pitch:** el jurado se fijará sobre todo en la ventaja competitiva. Copiar los agentes es fácil; lo que no se puede copiar son **los datos acumulados de cada empresa** y **la red de gestorías**. Hay que defender esas dos cosas, con el ciclo verificable como prueba de que funciona.

## Caso de la demo (versión 1, datos sintéticos)
- Caja para 9 días.
- 10.554,10 € vencidos; Mutua Beta paga a 95 días.
- Las sesiones de particulares caen un 15,4 %, y el año pasado no bajaron.
- La clínica de al lado ofrece la primera sesión a 20 € y promete «sin esperas»; el 86 % de las reseñas recientes se quejan de la espera.
- El 59 % de las consultas por WhatsApp llegan fuera de horario: tardan 12 h en contestarse (0,4 h en horario) y se pierde el 41 %.
- **Causa cruzada** (finanzas + competencia + atención): se pierden particulares por precio y por espera, también cuando escriben fuera de horario, y la caja no aguanta una guerra de precios.
- **Plan:**
  - reclamar lo vencido (un recordatorio enviado solo y una reclamación formal aprobada);
  - contraoferta validada por finanzas: 30 € y no 20 €;
  - cita en 48 horas;
  - activar el asistente de WhatsApp fuera de horario, con aprobación.
- **Un mes después** (simulado): de la aseguradora que paga tarde, **2 de 3 facturas** cobradas, y la otra aseguradora, al completo (3 de las 4 facturas reclamadas), comprobado con el banco; la respuesta fuera de horario pasa de 12 h a minutos y las quejas por la espera, del 86 % al 50 % (coincide en el tiempo, no lo demuestra); lo que no funcionó vuelve al plan.

## Fuentes
1. Ministerio de Industria, *Cifras PYME*, mayo de 2026 (1,36 millones de pymes con asalariados; exactamente 1.355.023). **Verificado** en el PDF: <https://ipyme.org/Publicaciones/Cifras%20PYME/CifrasPyme_mayo_2026.pdf>
2. INE, DIRCE a 1/1/2025 (62.234 empresas de contabilidad, asesoría y gestoría), citado por Legalitas: <https://www.legalitas.com/actualidad/futuro-gestorias>. **Por verificar** (25/11/2026): no se encontró la tabla del INE y otras fuentes dan cifras distintas (unas 54.000–61.000 empresas en el grupo 69.2). No usar esta cifra en el pitch.
3. Plazo medio de pago de 67 días, frente a los 60 legales, y el 85 % de las grandes empresas lo incumple (Plataforma Multisectorial contra la Morosidad, *Estudio Plazos de Pago en España 2025*). **Verificado** el 25/11/2026 a través de PIMEC, miembro de la PMcM: <https://pimec.org/es/actualidad/noticia/n/la-pmcm-reclama-reformar-urgentemente-la-ley-para-combatir-los-retrasos-en-los-pagos>
4. INE, *Encuesta sobre el uso de TIC y del comercio electrónico en las empresas* 2025 (nota de 22/10/2026): solo el 34,3 % de las empresas de 10 o más empleados analiza sus datos con su propio personal y el 33,9 % usa CRM. **Verificado**: <https://www.ine.es/dyngs/Prensa/ETICCE20251T2026.htm>
