# DiverxiaEscuadronMCP

Proyecto del equipo EscuadronMCP para el hackathon **IA First** de Diverxia (24/11/2026).

> **Estado:** en desarrollo. El reto es el 04, «La IA como servicio: agentes inteligentes que actúan».

## Enfoque

**Un consultor de IA permanente para pymes.** Se conecta a los datos que ya tiene la empresa, diagnostica qué la frena en cinco áreas (finanzas, organización, equipo, legal, y clientes y competencia) y prioriza un plan de mejora. Después **ejecuta** las mejoras que puede hacer solo y **vuelve a medir** si funcionaron.

> Una consultora te deja un informe. Nosotros te dejamos resultados medidos.

El prototipo se demuestra con una clínica de fisioterapia ficticia de Málaga, con datos sintéticos. Decisión completa: [ADR 001](docs/decisiones/001-idea-y-enfoque.md).

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
