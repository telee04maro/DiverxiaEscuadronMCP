# 002. Vigía: equipo de agentes especialistas con un coordinador que cruza la información

- **Fecha:** 2026-11-24
- **Estado:** aceptada (idea del equipo). Sustituye a la [ADR 001](001-idea-y-enfoque.md).
- **Origen:** el equipo concreta y reorienta la idea del consultor de IA permanente.

## Contexto

La ADR 001 planteaba un consultor de IA que diagnostica cinco áreas, actúa y mide. El equipo la reorienta a **Vigía**: una plataforma con un **agente especialista por área** y un **agente coordinador** que los une.

**El problema:** las pymes tienen la gestión repartida (gestoría, agencia, Excel) y nadie cruza la información. El dueño no tiene una visión global y los problemas se detectan tarde.

**Riesgos identificados:**
- «Centralizar» por sí solo suena a una carpeta compartida.
- «Expertos en todo» es una promesa que el jurado pondrá a prueba.
- En 16 h no da para seis agentes bien hechos.

## Opciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| Consultor único de cinco áreas (ADR 001) | Simple de construir | Suena a «ChatGPT con un cuestionario»; no explica por qué es mejor que una consultora |
| **Equipo de especialistas + coordinador, con dos especialistas en profundidad (elegida)** | La causa cruzada es un valor que nadie más ofrece; cada agente tiene fuentes propias, lo que da credibilidad; la arquitectura escala a más especialistas | Más piezas: se mitiga construyendo solo dos especialistas y el coordinador |
| Seis especialistas superficiales | Enseña amplitud | «Seis agentes a medias son peores que dos muy buenos» |

## Decisión

- **Tesis (candidata):** «Cada proveedor ve su parte. Vigía ve la causa».
- **Especialistas:**
  - competencia y mercado;
  - marketing y clientes;
  - finanzas;
  - legal y cumplimiento;
  - organización y personas;
  - atención al cliente (canal único con el dueño).
- **Coordinador:** cruza los hallazgos para encontrar la causa real, prioriza por impacto, esfuerzo y urgencia, crea el plan a 7, 30 y 90 días, lo ejecuta, mide y reordena.
- **Personalización:** una entrevista inicial sobre sector, tamaño, objetivos y recursos.
- **Modelo de negocio:** suscripción mensual por módulos y tamaño. Supervisión humana experta en legal y finanzas. **Canal: las gestorías y asesorías.**
- **Prototipo del hackathon:** **competencia y mercado + finanzas, en profundidad, y el coordinador cruzando los dos.** El resto es hoja de ruta.
- **Acciones reales de la demo:**
  - reclamación de facturas vencidas, conciliada con el banco al céntimo;
  - contraoferta frente a la competencia, solo si finanzas confirma el margen;
  - re-medición con un «mes después» simulado.
- **Caso de la demo:** se mantiene la **clínica de fisioterapia ficticia de Málaga** de la ADR 001, con datos sintéticos (pendiente de que el equipo lo confirme).
- **Principios:** los de la ADR 001 y los de `CLAUDE.md` («Principios de diseño»):
  - fuentes propias por agente;
  - las reglas calculan y la IA interpreta;
  - hallazgos con evidencia y confianza;
  - nunca se inventa un dato;
  - la mejora se da por hecha cuando el indicador se mueve;
  - autonomía por niveles.

## Consecuencias

- **A favor:**
  - El pitch tiene un argumento que nadie más puede dar: el ejemplo de la causa cruzada.
  - La hoja de ruta es creíble porque añadir un especialista es extender, sin tocar el coordinador.
  - El canal de gestorías responde a «¿cómo conseguiréis clientes?».
- **En contra:** las fuentes del agente de competencia (Biblioteca de Anuncios de Meta, Centro de Transparencia de Google Ads, buscadores, reseñas) pueden exigir registro, tener límites o no tener API oficial. Antes de codificarlas hay que **verificar sus condiciones** y anotarlo en `docs/fuentes.md`. Si una no es accesible hoy, se usa una instantánea sintética con el mismo formato y se dice en la demo.
- **Cambia respecto a la ADR 001:** el documento legal sale de la demo y pasa a la hoja de ruta del agente legal. Entra el agente de competencia.
- **Pendiente:**
  - stack (ADR 003);
  - confirmar el caso de la clínica;
  - nombre definitivo («Vigía» es provisional: hay que comprobar la marca).
