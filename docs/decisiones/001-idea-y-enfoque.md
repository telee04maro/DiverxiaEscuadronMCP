# 001. Idea: consultor de IA permanente para pymes que diagnostica, actúa y mide

- **Fecha:** 2026-11-24
- **Estado:** sustituida por [002](002-vigia-equipo-de-agentes.md)
- **Origen:** reto 04 «La IA como servicio» (`docs/reto/`). Sustituye a las propuestas anteriores de este mismo archivo, que siguen en el historial de git y en `docs/ideas.md`.

## Contexto

El reto pide un agente que **identifique necesidades reales, decida y ejecute tareas de forma autónoma** para empresas y ciudadanos, más allá de los asistentes tradicionales. Las bases oficiales puntúan, entre otros criterios:
- innovación;
- impacto;
- adecuación al reto;
- viabilidad técnica y económica;
- **uso estratégico y responsable de la IA**;
- implementación;
- evolución durante el evento;
- pitch.

Además, prohíben usar datos personales sin autorización.

La entidad gestora, Diverxia, es una consultora de emprendimiento y agente digitalizador del Kit Digital: conoce de primera mano el problema de las pymes.

## Opciones evaluadas

| Opción | Por qué no |
|---|---|
| v1: cobros, reclamaciones, licitaciones, ayudas, luz | El equipo las descartó por básicas: partían de la tecnología, no del problema |
| v2: TERRAL (calor y mayores), dependencia, citas perdidas | Con base sólida, pero el equipo prefirió su propia idea |
| **Consultor de IA permanente para pymes (idea del equipo)** | **Elegida** |

## Decisión

Un **consultor de IA permanente para pymes** que sigue cinco pasos:
1. Se conecta a los datos que ya tiene la empresa, o los recibe en Excel o CSV.
2. **Diagnostica cinco áreas:** finanzas, organización, equipo, legal, y clientes y competencia.
3. **Prioriza** un plan en tres bloques: esta semana, este mes y este trimestre.
4. **Ejecuta** las mejoras que puede hacer solo.
5. **Vuelve a medir** si funcionaron y reordena el plan.

**Tesis (candidata):** «Una consultora te deja un informe. Nosotros te dejamos resultados medidos».

### Alcance del prototipo del hackathon
- **Caso único de demo:** una **clínica de fisioterapia ficticia de Málaga** con unos 15 empleados. Activa las cinco áreas:
  - aseguradoras que pagan tarde;
  - citas perdidas y agenda;
  - rotación de fisioterapeutas;
  - datos de salud (RGPD);
  - reseñas frente a la competencia cercana.
- **Tres acciones reales en la demo** (elegidas por el equipo):
  1. **La auditoría:** diagnóstico de las cinco áreas y plan priorizado. Cada hallazgo lleva su evidencia, su grado de confianza y lo que falta para afinarlo.
  2. **Reclamar facturas vencidas:** decide el tono según el cliente y su historial, envía el correo a un buzón de demo y **solo da la factura por cobrada cuando el pago cuadra con el extracto del banco, al céntimo**.
  3. **Generar el documento legal que falta:** las reglas detectan la obligación incumplida, el agente redacta el documento citando la norma y lo deja **pendiente de validación por un asesor**.
- **Volver a medir:** con un «mes después» simulado, avisado como tal, el agente compara los indicadores y reordena el plan.
- **Profundidad por áreas:**
  - **A fondo:** Finanzas (cobros) y Legal, que son las áreas de las acciones.
  - **En el diagnóstico:** Clientes y competencia (reseñas), Organización (agenda y tareas) y Equipo (encuesta anónima).

### Principios de diseño
- **Las reglas calculan; la IA interpreta y redacta.** Indicadores (días de cobro, márgenes, inasistencia, nota media), obligaciones legales según tamaño y sector, y prioridad (impacto × urgencia ÷ esfuerzo): todo con código determinista. Claude interpreta texto (reseñas, comentarios de la encuesta, correos), explica los hallazgos, decide el tono y redacta.
- **Nunca inventa un dato.** Lo que falta se dice («no tengo los costes por servicio: con ellos calcularía el margen»).
- **Equipo:** sale **solo de la encuesta anónima**. No se muestran resultados de grupos de menos de 5 respuestas.
- **Autonomía por niveles:**
  - actúa solo en lo reversible (recordatorios y reclamaciones amables);
  - en lo serio, prepara y una persona decide (reclamación formal, documentos legales, decisiones financieras).
- **Comprobar el efecto:** una mejora no está hecha porque se haya ejecutado, sino cuando el indicador se mueve.
- **Datos sintéticos:** toda la clínica de la demo la generamos nosotros. Las bases prohíben usar datos personales sin autorización.

## Consecuencias

- **A favor:**
  - Encaja con el reto: detecta, decide, actúa y mide.
  - Tiene un pagador claro: la pyme, por suscripción, con asesorías y consultoras como canal.
  - Aprovecha nuestra seña de verificación (el cobro cuadra al céntimo; la mejora se da por hecha solo si el indicador se mueve).
- **En contra:** riesgo de parecer «consultora genérica» o «ChatGPT con un cuestionario». Para mitigarlo, el pitch se cuenta con un único caso, al menos dos acciones reales en la demo y la re-medición.
- **Encaje con Diverxia:** el producto se presenta como algo que **multiplica a consultores y asesorías**, no como su sustituto.
- **Riesgo legal:** el agente detecta y recomienda, pero no decide en lo legal ni en lo financiero: lo serio va a un asesor.
- **Pendiente:**
  - nombre del producto;
  - stack (ADR 002);
  - comprobar las obligaciones legales concretas de una clínica (RGPD con datos de salud, registro de jornada, etc.) en la fuente oficial antes de codificarlas.
