# Registro de decisiones (ADR)

Un archivo por decisión de arquitectura o de stack: `NNN-titulo-corto.md`. Una decisión nueva puede **ampliar** otra (por ejemplo, «concreta la 001») o **sustituirla** («sustituida por NNN»). Las decisiones no se borran.

## Plantilla

```markdown
# NNN. Título

- **Fecha:** AAAA-MM-DD
- **Estado:** propuesta | aceptada | ampliada por NNN | sustituida por NNN
- **Origen:** quién o qué la motivó (equipo, mentor, fallo real, auditoría)

## Contexto
Qué problema hay y qué restricciones o criterios de evaluación importan.

## Opciones evaluadas
| Opción | Resumen | A favor | En contra / por qué no sola |
|---|---|---|---|

## Decisión
Qué se elige, cómo funciona y por qué. Si es una combinación, qué papel tiene cada parte.

## Consecuencias
- A favor:
- En contra:
- Riesgos abiertos y cómo se mitigan:
- Coste (tiempo, dinero, IA), medido si es posible:
```

## Índice

| Nº | Decisión | Estado |
|---|---|---|
| 001 | [Idea: consultor de IA permanente para pymes que diagnostica, actúa y mide](001-idea-y-enfoque.md) | sustituida por 002 |
| 002 | [Vigía: equipo de agentes especialistas con un coordinador que cruza la información](002-vigia-equipo-de-agentes.md) | aceptada |
| 003 | [Stack del prototipo](003-stack-del-prototipo.md) | aceptada |
| 004 | [Cambio de nombre: de Centra a Vigía](004-nombre-vigia.md) | aceptada |
