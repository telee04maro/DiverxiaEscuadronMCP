<p align="center"><img src="docs/negocio/logo.svg" alt="Vigía" width="520"></p>

# Vigía: un equipo de expertos de IA para toda tu pyme

> **Cada proveedor ve su parte. Vigía ve la causa.**

Proyecto del equipo EscuadronMCP para el hackathon **IA First** de Talent Land España (Málaga, 24/11/2026), reto **04 «La IA como servicio: agentes inteligentes que actúan»**.

Las pymes tienen la gestión repartida: la gestoría lleva los impuestos, una agencia las redes y las cuentas están en un Excel. **Nadie cruza la información**, así que los problemas se detectan tarde. Vigía tiene un **agente especialista por área**, cada uno con sus fuentes, y un **agente coordinador** que cruza lo que ve cada uno. Con eso encuentra la causa real, prioriza un plan a 7, 30 y 90 días, **ejecuta** lo que puede hacer solo y **mide si funcionó**.

## 1. Cómo usarlo

### Requisitos
- [uv](https://docs.astral.sh/uv/getting-started/installation/), que instala Python 3.13 y las dependencias exactas.
- Opcional: una clave de Anthropic. **Sin clave, Vigía funciona igual en modo reglas.**

### Instalación
```bash
git clone https://github.com/telee04maro/DiverxiaEscuadronMCP.git
cd DiverxiaEscuadronMCP
uv sync
cp .env.example .env      # en Windows (PowerShell): Copy-Item .env.example .env
```

### Arrancar la demo
```bash
uv run streamlit run src/vigia/app.py      # panel en http://localhost:8501
uv run python -m vigia --fallo             # el mismo recorrido, en la consola
uv run python -m vigia.connectors.http_api # API del ERP de demo (para el asistente de WhatsApp)
```
La guía paso a paso de la demo está en [`docs/DEMO.md`](docs/DEMO.md).

### Configuración (`.env`)
| Variable | Para qué |
|---|---|
| `ANTHROPIC_API_KEY` | Activa Claude (si no está, se usan reglas) |
| `AI_BUDGET_USD` | Tope de gasto de IA por ejecución (0,50 $ por defecto) |
| `VIGIA_USE_AI=0` | Fuerza el modo reglas aunque haya clave |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` y `DEMO_RECIPIENT` | Correo real, **siempre redirigido al buzón de prueba** `DEMO_RECIPIENT`. Sin estas variables, los correos se guardan en `outbox/` |
| `VIGIA_ERP_DB`, `VIGIA_ERP_TOKEN` | Base de datos del ERP de demo y token obligatorio de su API (al menos 16 caracteres) |
| `LATE_INTEREST_RATE_PCT` | Tipo de interés de demora legal vigente. Si no se indica, el importe de los intereses no se calcula ni se inventa |

## 2. Qué hace

| Agente | Fuentes | Qué detecta | Qué hace |
|---|---|---|---|
| **Finanzas** | Facturas, extracto bancario, sesiones por mes | Caja (días de gasto cubiertos), cobros vencidos, clientes que pagan tarde, caída de ingresos y si es estacional | Reclama lo vencido con el tono adecuado y **solo da una factura por cobrada si cuadra con el banco al céntimo**. Valida si una oferta compensa |
| **Competencia y mercado** | Biblioteca de Anuncios de Meta, precios, reseñas, resultados de búsqueda | Ofertas nuevas de la competencia, diferencia de precios, quejas en reseñas, visibilidad en Google | Propone respuestas: contraoferta, visibilidad |
| **Atención y captación** | Oportunidades del ERP/CRM (en la demo, ERP de demo con la forma de BALTER, donde escribe el asistente de WhatsApp) | Consultas fuera de horario que tardan en contestarse, consultas perdidas, oportunidades sin responsable | Propone activar el asistente de WhatsApp fuera de horario y asignar lo pendiente. El asistente registra cada consulta **sin duplicar contactos** |
| **Coordinador** | Los hallazgos de los especialistas | **La causa cruzada**, que ningún especialista ve solo, y las hipótesis descartadas | Plan a 7, 30 y 90 días con niveles de autonomía; ejecuta, mide y reordena |

**Niveles de autonomía:**
- **Actúa solo:** recordatorios amables.
- **Propone y una persona aprueba:** reclamaciones formales, precios y campañas.
- **Lo hace una persona, con fecha.**
- **Deriva a un experto:** legal y financiero serio.

**Cómo entra una empresa:** en la pestaña «1 · Empresa», opción «Tu empresa». Rellena la entrevista inicial y sube sus Excel o CSV (facturas, banco, ventas, consultas, reseñas, competidores) con plantillas en español. Cada fila se valida, y lo que no suba aparece como «lo que me falta», nunca como cero. Con ERP o CRM, se conecta mediante la interfaz `CrmConnector` ([ADR 005](docs/decisiones/005-conectores-y-captacion.md); contrato en [`docs/integracion-whatsapp-erp.md`](docs/integracion-whatsapp-erp.md)).

**Hoja de ruta:** agentes de marketing y clientes, legal y cumplimiento, organización y personas (con encuesta anónima), chat del dueño por WhatsApp y conector BALTER real (pendiente de documentación y permiso; ver [`docs/integracion-balter.md`](docs/integracion-balter.md)).

### Uso de la IA
Las reglas calculan y la IA interpreta. Claude Haiku 5.5 lee anuncios y reseñas, y Claude Opus 5.5 cruza hallazgos y redacta. **Todo lo que propone la IA se verifica:**
- un precio que no está en el anuncio, se rechaza;
- una causa que cita un hallazgo inexistente, se rechaza;
- un correo con un importe inventado, se rechaza.

Detalle completo: [`docs/uso-ia.md`](docs/uso-ia.md).

### Datos
**Todos son sintéticos.** La clínica de fisioterapia, las aseguradoras y los competidores son ficticios, porque las bases prohíben datos personales. Los datos de la competencia imitan el formato oficial de cada API; las condiciones de acceso están verificadas en [`docs/fuentes.md`](docs/fuentes.md).

## 3. Entregables

| Entregable | Archivo |
|---|---|
| 1 · Canvas del modelo de negocio | [`docs/negocio/canvas.md`](docs/negocio/canvas.md) |
| 2 · Prototipo y uso de la IA | este repositorio y [`docs/uso-ia.md`](docs/uso-ia.md) |
| 3 · Marketing (logo, eslogan, estrategia) | [`docs/negocio/marketing.md`](docs/negocio/marketing.md), [`docs/negocio/logo.svg`](docs/negocio/logo.svg) |
| 4 · Guion del pitch | [`docs/negocio/pitch.md`](docs/negocio/pitch.md) |

## 4. Para el equipo técnico

### Calidad
```bash
uv run ruff format . && uv run ruff check .   # formato y lint
uv run mypy src tests                         # tipado estricto
uv run pytest                                 # tests (también de extremo a extremo)
```
La CI (`.github/workflows/ci.yml`) los ejecuta en cada push, en Linux y en Windows.

### Estructura
```
src/vigia/
  domain/          Contrato del hallazgo, dinero (Decimal), prioridad
  data/            Modelo de datos de la empresa, carga desde CSV/JSON y clínica sintética
  specialists/     Agentes especialistas (finanzas, competencia); interfaz común
  finance/         Conciliación al céntimo y validación de ofertas
  coordinator/     Causa cruzada y plan a 7, 30 y 90 días
  actions/         Reclamaciones de cobro y envío de correo
  connectors/      Contrato ERP/CRM, ERP de demo (SQLite) y su API HTTP para el asistente de WhatsApp
  llm/             Claude tras una interfaz (salidas estructuradas, tope de gasto, modo sin IA)
  remeasure.py     Un mes después: ¿se movió el indicador?
  pipeline.py      El ciclo completo
  app.py           Panel de la demo (Streamlit)
data/demo/         Clínica sintética: antes (mes-0) y un mes después (mes-1)
docs/              Reto, decisiones (ADR), fuentes, uso de la IA, demo y negocio
```

### Decisiones
- [001 · Idea inicial](docs/decisiones/001-idea-y-enfoque.md) (sustituida)
- [002 · Vigía: especialistas y coordinador](docs/decisiones/002-vigia-equipo-de-agentes.md)
- [003 · Stack del prototipo](docs/decisiones/003-stack-del-prototipo.md)
- [004 · Cambio de nombre a Vigía](docs/decisiones/004-nombre-vigia.md)
- [005 · Conectores ERP/CRM, atención y captación, y entrada de datos](docs/decisiones/005-conectores-y-captacion.md)

Para añadir un especialista, se implementa la interfaz `Specialist` (`src/vigia/specialists/base.py`) y se registra en `pipeline.default_specialists()`. El cruce de causas con IA recoge sus hallazgos sin cambios; solo hay que añadir sus acciones al catálogo del plan (`coordinator/plan.py`) y, si se quiere, sus reglas de cruce.
