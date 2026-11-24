# DiverxiaEscuadronMCP

Proyecto del equipo EscuadronMCP para el hackathon **IA First** de Diverxia (24/11/2026).

> **Estado:** en desarrollo. El reto es el 04, «La IA como servicio: agentes inteligentes que actúan».

## Enfoque

**Centra** (nombre provisional): **un equipo de expertos de IA para toda tu pyme, en un solo sitio.**

> Cada proveedor ve su parte. Centra ve la causa.

Las pymes tienen la gestión repartida entre la gestoría, la agencia y un Excel, y nadie cruza la información. Centra tiene **un agente especialista por área** (competencia y mercado, marketing y clientes, finanzas, legal, organización y personas, y atención al cliente) y **un agente coordinador** que los une. Los agentes detectan problemas, el coordinador encuentra la causa real cruzando lo que ve cada uno y prioriza un plan a 7, 30 y 90 días. Después se **ejecuta** y se **mide** el resultado.

El prototipo demuestra en profundidad los agentes de **competencia** y **finanzas** y el **coordinador**, con una clínica de fisioterapia ficticia de Málaga y datos sintéticos. Decisión completa: [ADR 002](docs/decisiones/002-centra-equipo-de-agentes.md).

## Para el equipo

| Documento | Para qué |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Normas de trabajo con Claude Code (obligatorias) |
| [`docs/ESTADO.md`](docs/ESTADO.md) | Estado del proyecto, hoja de ruta y traspaso entre sesiones: **léelo primero** |
| [`docs/reto/`](docs/reto/) | Enunciado y bases oficiales |
| [`docs/decisiones/`](docs/decisiones/) | Decisiones de arquitectura (ADR) |
| [`docs/DEMO.md`](docs/DEMO.md) | Guion de la demo |
| [`docs/red-team.md`](docs/red-team.md) | Protocolo de auditoría independiente |

### Empezar a trabajar

```bash
git clone https://github.com/telee04maro/DiverxiaEscuadronMCP.git
cd DiverxiaEscuadronMCP
cp .env.example .env      # en Windows (PowerShell): Copy-Item .env.example .env
```

Después abre Claude Code en la carpeta: leerá `CLAUDE.md` automáticamente.
