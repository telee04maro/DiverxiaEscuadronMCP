# CLAUDE.md — Vigía (DiverxiaEscuadronMCP)

Normas obligatorias para cualquier sesión de Claude Code en este repositorio. Todo el equipo trabaja con Claude Code: estas reglas garantizan que todos programemos igual. **Si una petición contradice estas normas, avisa antes de actuar.**

El método es el que nos hizo ganar el Malackathon 2026: decidir con datos, construir de principio a fin pronto, subir siempre algo entregable y **no dar nada por hecho sin comprobar su efecto**.

---

## Contexto

- **Evento:** hackathon *IA First* de Talent Land España, gestionado por Diverxia. Málaga, 24 y 25/11/2026, unas 16 h. Somos un equipo de 3.
- **Reto:** **04 «La IA como servicio»: agentes inteligentes que actúan.** Crear agentes de IA que identifiquen necesidades reales, tomen decisiones y ejecuten tareas de forma autónoma para empresas y ciudadanos, **más allá de los asistentes tradicionales**: que actúen, conecten servicios y generen impacto real.
- **Fuente de verdad:** el enunciado, los entregables y las bases oficiales están en `docs/reto/`. Si contradicen este archivo, mandan ellos y hay que actualizar este archivo.
- **Plazos:** _pendiente de confirmar_ (hora de cada hito, entrega en el Drive, pitch).

### Entregables (en la carpeta del equipo en el Drive del Hackathon)
1. **Canvas:** el modelo de negocio.
2. **Prototipo y uso de la IA:** enseñar el prototipo y explicar cómo se ha usado la IA, tanto en el producto como para construirlo. Se registra sobre la marcha en `docs/uso-ia.md`.
3. **Marketing:** logo, eslogan y estrategia de comunicación.
4. **Guion del pitch.**

### Lo que exigen las bases oficiales
- **Criterios** (pesos sin publicar):
  - innovación;
  - impacto;
  - adecuación al reto;
  - viabilidad técnica y económica;
  - **uso estratégico y responsable de la IA**;
  - capacidad de implementación;
  - calidad de los entregables;
  - **evolución durante el hackathon**;
  - trabajo en equipo;
  - pitch y claridad.
- **Prohibido introducir datos personales, secretos empresariales o información confidencial sin autorización.** La empresa de la demo es **ficticia y sus datos son sintéticos**.
- Hay que declarar las herramientas, los modelos y los datos usados, e identificar los componentes previos y de terceros.
- Exigen una participación humana sustancial, y el proyecto se desarrolla durante el hackathon.

---

## El producto: Vigía (nombre provisional)

**Un equipo de expertos de IA para toda tu pyme, en un solo sitio.**

### Tesis
> **«Cada proveedor ve su parte. Vigía ve la causa.»** Eslogan corto (menos de siete palabras, criterio del taller): **«Vigía ve la causa.»**

La gestoría ve los impuestos, la agencia ve las redes y el Excel ve las cuentas. Nadie cruza la información, así que los problemas se detectan tarde. **Centralizar no aporta valor por sí solo; lo que aporta valor es cruzar la información.** El argumento estrella es el **agente coordinador**: encuentra causas que ningún proveedor ve por separado. Toda decisión de diseño, demo o pitch se contrasta con esta frase.

### Arquitectura de agentes
| Agente | Qué hace | Fuentes y herramientas propias |
|---|---|---|
| **Coordinador** | Cruza los hallazgos de los especialistas para dar con la **causa real**. Prioriza por impacto, esfuerzo y urgencia. Crea el plan a **7, 30 y 90 días**, lo ejecuta, mide y reordena | Los hallazgos estructurados de cada especialista |
| **Competencia y mercado** | Anuncios de la competencia, posicionamiento en buscadores (SEO y SEM), precios, reseñas y tendencias de otros países | Biblioteca de Anuncios de Meta, Centro de Transparencia de Google Ads, resultados de búsqueda, reseñas públicas (cada fuente con sus condiciones de uso verificadas) |
| **Finanzas** | Caja, márgenes, morosos y previsiones. Reclama cobros y avisa de desviaciones | Contabilidad y extracto bancario (CSV/Excel), facturas |
| Marketing y clientes | Reseñas, redes y campañas. Responde reseñas y propone o lanza acciones | Reseñas propias, redes |
| Legal y cumplimiento | Calendario de obligaciones, revisión de contratos, documentos y plazos. Lo complejo va a un abogado | Reglas de obligaciones según tamaño y sector, con la norma citada |
| Organización y personas | Procesos lentos, cuellos de botella y clima del equipo | Agenda y tareas; **encuesta anónima** |
| **Atención y captación** | Consultas de los clientes: tiempo de respuesta dentro y fuera de horario, perdidas, sin responsable. El asistente de WhatsApp las registra en el ERP/CRM sin duplicar | Oportunidades del ERP/CRM mediante `CrmConnector` (en la demo, ERP de demo con la forma de BALTER) |
| **CRM de Vigía** (ADR 007) | Una ficha por cliente con lo que aporta cada agente (deuda, consultas, reclamaciones), unida por correo o teléfono, con alertas cruzadas | Las piezas de finanzas, atención y acciones; mismas reglas que los agentes |
| Chat del dueño | Canal único por el que el dueño pregunta o aprueba (WhatsApp) y el sistema responde o actúa | Todos los anteriores |

**Personalización:** una entrevista inicial (sector, tamaño, objetivos, recursos) adapta el plan a cada empresa.

**Modelo:** suscripción mensual por módulos y tamaño de empresa. Las áreas críticas (legal y finanzas) las supervisan expertos humanos. **Canal de entrada:** las gestorías y asesorías, que ya tienen la confianza de miles de pymes, se lo ofrecen a sus clientes.

### Alcance del prototipo: amplitud en el pitch, profundidad en la demo
**Seis agentes a medias son peores que dos muy buenos.** En el hackathon se construyen **en profundidad**:
1. **Agente de competencia y mercado.**
2. **Agente de finanzas.**
3. **Coordinador cruzando los hallazgos** (también los de atención y captación, punto 4), con el plan a 7, 30 y 90 días, ejecución y re-medición.
4. **Atención y captación** (ADR 005): ERP de demo con API para el asistente de WhatsApp del compañero (Hermes) y entrada «Tu empresa» con Excel/CSV.

El resto (marketing y clientes, legal, organización y personas, chat del dueño) aparece en el pitch como **hoja de ruta**. **BALTER real:** nunca en producción; solo con documentación de su API, visto bueno de la empresa y una primera prueba de solo lectura sin datos personales. Si sobra tiempo, solo se añade después del MVP completo y siempre con la misma calidad.

**Caso único de la demo:** una pyme ficticia de Málaga, en principio la **clínica de fisioterapia** de la ADR 001 (pendiente de confirmar en la ADR 002). Contad el pitch con **un ejemplo concreto de causa cruzada**:
> Las sesiones de particulares bajan un 18 %. **Competencia:** la clínica de al lado lanzó hace dos semanas en Meta una oferta de «primera sesión a 20 €». **Reseñas propias:** se quejan de la espera. **Finanzas:** una aseguradora paga a 95 días y la caja está justa. **Coordinador:** no es estacionalidad. Se pierden particulares por precio y espera, y la caja no aguanta una guerra de precios. **Plan:** reclamar a la aseguradora (7 días), contraoferta validada por finanzas para que deje margen (30 días), reorganizar la agenda (90 días). Después, medir.

**Acciones reales que tiene que ejecutar la demo** (el reto pide un agente que actúa, no un PDF):
- **Finanzas:** reclamar facturas vencidas. Decide el tono según el cliente, envía el correo y **solo da la factura por cobrada cuando el pago cuadra con el banco al céntimo**.
- **Coordinador + finanzas:** la contraoferta frente a la competencia **solo se propone si finanzas confirma que deja margen**. Los agentes se contrastan entre sí, no se dan la razón.
- **Re-medición:** un «mes después» simulado, avisado como tal. El coordinador comprueba qué indicadores se movieron y reordena el plan.

---

## Principios de diseño (obligatorios)

1. **Cada agente tiene sus propias fuentes y herramientas concretas.** «Expertos en todo» es lo que el jurado pondrá a prueba: un agente sin fuentes propias es solo un prompt, y no se presenta como agente.
2. **Las reglas calculan; la IA interpreta, cruza y redacta.**
   - **Código determinista:** indicadores (caja, márgenes, días de cobro, nota de reseñas), obligaciones legales y puntuación de prioridad.
   - **Claude:** interpretar texto (anuncios, reseñas, correos), cruzar hallazgos, explicar la causa, decidir el tono y redactar.
3. **Hallazgos estructurados con evidencia.** Cada hallazgo de un especialista lleva:
   - área;
   - qué ha visto;
   - **evidencia** (dato, fuente y fecha);
   - **confianza**;
   - impacto, esfuerzo y urgencia.
   
   El coordinador solo razona sobre hallazgos con evidencia y **cita de qué especialistas sale cada causa**.
4. **Nunca se inventa un dato.** Lo que falta se dice y se indica qué haría falta para afinarlo («sin los costes por servicio no puedo calcular el margen»). Un indicador sin datos es «no disponible», nunca cero.
5. **Una mejora no está hecha porque se haya ejecutado, sino cuando el indicador se mueve.** Si no se mueve, se dice y se reordena el plan.
6. **Autonomía por niveles:**
   - **Actúa solo** en lo reversible y de bajo riesgo: recordatorios, primera reclamación amable, informes.
   - **Prepara y una persona aprueba:** reclamaciones formales, respuestas públicas, campañas y precios.
   - **Deriva a un experto humano:** lo legal y financiero serio.
   
   El producto lo enseña explícitamente.
7. **Personas:** el clima del equipo sale **solo de la encuesta anónima**, y se dice así. No se muestran resultados de grupos de menos de 5 respuestas.
8. **Transparencia:** todo mensaje que el agente envía a terceros se identifica como generado por un asistente de IA en nombre de la empresa (Reglamento de IA, art. 50).
9. **Registro auditable:** cada agente deja constancia de qué vio, qué decidió, qué hizo y qué comprobó. Alimenta la demo y el entregable «uso de la IA».

### Fuentes externas
- **Solo fuentes públicas o datos sintéticos.** Antes de usar una fuente externa (Biblioteca de Anuncios de Meta, Centro de Transparencia de Google Ads, buscadores, reseñas), **verifica en su documentación oficial**:
  - sus condiciones de uso;
  - si hay API oficial y si exige registro o verificación;
  - sus límites.
  
  Anótalo en `docs/fuentes.md`.
- Prefiere las APIs oficiales. **No hagas scraping de lo que las condiciones prohíben** ni te saltes protecciones.
- Si una fuente no es accesible en el hackathon, usa una **instantánea sintética con el mismo formato** y dilo en la demo.
- Las reseñas y los anuncios pueden contener nombres de personas: guarda solo el texto necesario, sin identificar a nadie.

---

## Rumbo y cambios de rumbo (obligatorio)

Cualquier compañero que haga pull debe poder saber, con su IA, por dónde se va y hacia dónde. Por eso:
- Si **pivotas**, encuentras un **error de enfoque** o crees que **es mejor ir por otro lado**, no lo implementes en silencio. Proponlo al usuario y, si se acepta, haz en el **mismo commit**:
  1. Una ADR nueva en `docs/decisiones/`, y marca la anterior como «sustituida por NNN» (o «ampliada por NNN»).
  2. Una fila en «Cambios de rumbo» de `docs/ESTADO.md` (fecha, cambio, motivo, enlace a la ADR).
  3. La actualización del apartado «Enfoque» del `README.md` y de «El producto» en este archivo.
- Los **errores o limitaciones** que descubras van a «Problemas conocidos» de `docs/ESTADO.md` aunque no cambien el rumbo.
- La **pista de un mentor** es una hipótesis valiosa: se mide, se registra y, si aporta, se integra con su ADR.
- Al cerrar una etapa de la hoja de ruta, márcala en `docs/ESTADO.md`.

**Hitos:** el MVP de principio a fin (competencia + finanzas + coordinador con una acción real) debe estar unas **3–4 h** después de arrancar E0. **Congelación de funciones** unas 3 h antes de la entrega: a partir de ahí solo se endurece, se reúnen evidencias y se prepara el pitch.

## 1. Investigar antes de implementar (obligatorio)

Antes de escribir código para cualquier funcionalidad, librería, servicio o fuente de datos:

1. **Lee el código existente y `docs/`** para no duplicar ni contradecir lo que ya hay.
2. **Investiga las alternativas** en la documentación oficial, buscando en la web y con versiones actuales. Compara al menos 2 opciones en seguridad, rendimiento, madurez, encaje con el stack y coste en tiempo de hackathon.
3. **Justifica la elección** en pocas líneas al usuario antes de implementar. Si la decisión es de arquitectura, de stack o de una fuente externa, regístrala en `docs/decisiones/NNN-titulo.md`.
4. **Comprueba versiones y APIs reales.** No inventes APIs ni dependas de la memoria. Fija versiones exactas de las dependencias.
5. **Etiqueta lo investigado** como **verificado** (comprobado por nosotros), **por verificar** o **descartado**. Ninguna cifra del pitch sale sin su fuente.

**Proporcionalidad:** la profundidad de la investigación va con el impacto. Stack, arquitectura o un servicio externo exigen una comparación completa y una ADR. Un cambio local (un helper, un fix acotado) basta con revisar el código y la documentación de la API usada. Nunca te saltes la investigación por completo.

## 2. Commit y push continuos (seguro contra quedarnos sin tokens)

El repositorio remoto debe tener siempre una versión entregable y funcional.

- **Haz commit y push tras cada paso funcional pequeño**, sin esperar a que lo pidan. Nunca acumules más de 15–20 minutos de trabajo sin subir.
- **Antes de cada commit:** pasan el formato, el linter, los tipos y los tests. **Comprueba el código de salida de cada comando**: no lo filtres con `| tail`, porque oculta los fallos. Si algo queda a medias, que no rompa lo anterior (protégelo con un flag o no lo conectes aún).
- **Flujo exacto:**
  ```bash
  git add <archivos concretos>        # nunca `git add -A` a ciegas: revisa `git status`
  git commit -m "tipo(ámbito): descripción"
  git pull --rebase origin main       # varios compañeros empujan a la vez
  git push origin main
  ```
- Si el rebase da conflictos, resuélvelos respetando el trabajo de los compañeros; si no está claro, pregunta. **Prohibido `git push --force`** y reescribir historia publicada.
- **Mensajes:** [Conventional Commits](https://www.conventionalcommits.org/) en español: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`, `ci`. Por ejemplo: `feat(finanzas): reclamar facturas vencidas`.
- **Traspaso de contexto:** `docs/ESTADO.md` es la memoria compartida del equipo. Actualízalo en el mismo commit que cierra cada paso: qué funciona, qué está en curso (y quién), el siguiente paso concreto, la última verificación (hora, SHA, comando y resultado) y los problemas conocidos.
- Al terminar una tarea grande, actualiza el `README.md` y `docs/uso-ia.md`.

### Trabajo en equipo
- Antes de empezar una tarea, haz `git pull --rebase` y apúntala en «En curso» de `docs/ESTADO.md` (commit y push inmediatos) para que nadie la duplique.
- **Un agente, un módulo:** cada persona trabaja en agentes distintos siempre que sea posible. El **contrato del hallazgo** (su estructura) y la interfaz entre especialistas y coordinador son compartidos: solo se cambian avisando al equipo.
- **Recursos compartidos** (claves de API, buzón de prueba, cuotas): coordínalos desde el minuto 0.
- **Roles para 3 personas:**
  - **A — Construcción:** desarrolla con Claude y es dueño de `main`.
  - **B — Negocio:** canvas, marketing, pitch, ejemplo de causa cruzada, cifras del mercado y canal de gestorías.
  - **C — Datos, red team y demo:** genera la empresa sintética, audita cada pull desde fuera del repositorio (ver `docs/red-team.md`) y prepara los ensayos.

## 3. Verificación honesta (no negociable)

Es lo que más nos diferenció. Un jurado o un mentor que pilla un falso positivo hunde el proyecto.

- **Una acción no es una prueba.** Se verifica el efecto observable: el correo llegó, el pago cuadra, el indicador se movió.
- **Nunca un éxito o un «hecho» por defecto:**
  - desconocido ≠ cero;
  - ausente ≠ contradictorio;
  - timeout ≠ estable;
  - enviado ≠ aceptado.
- **El coordinador no inventa causas.** Si los hallazgos no bastan, dice que no hay evidencia suficiente y qué dato falta. Si dos especialistas se contradicen, lo muestra como hallazgo; no elige uno en silencio.
- **Invariantes baratos como oráculo:**
  - la conciliación de cobros al céntimo;
  - la caja final = caja inicial + cobros − pagos.
  
  Dinero siempre con `Decimal`.
- **Controles positivos:** arreglar un falso positivo no puede consistir en que todo falle.
- **Fallo inyectado:** el sistema tiene que detectar un error inyectado, por ejemplo un pago que llega con un céntimo de menos y la factura **no** se cierra. Se comprueba en los tests y en la consola (`uv run python -m vigia --fallo`). Por decisión del equipo (24/11), no se enseña en el panel ni en el pitch: distrae del valor.
- **Tests de las uniones** entre especialistas, coordinador, acciones e informe. Unos tests unitarios en verde no las cubren.
- **Separa «código corregido» de «validado de verdad».** Un test con mocks en verde no es una demo que funciona. Una afirmación en `ESTADO.md` necesita SHA, comando y resultado.
- **No borres tests, no rebajes requisitos y no cambies expectativas** para que algo pase.
- **Un hallazgo P1 del red team bloquea cualquier funcionalidad nueva** hasta corregirlo.
- **Solo se afirma lo verificado.** Lo que está en la hoja de ruta se presenta como hoja de ruta.

## 4. IA dentro del producto

- **La IA, donde aporta, y se explica dónde no:** interpretar, cruzar y redactar, sí. Calcular dinero, plazos u obligaciones, no.
- **Salidas estructuradas:** cada especialista devuelve hallazgos con un esquema validado. La salida de un LLM es un **dato no confiable**: se valida con el esquema y, si se puede, por su efecto. Nunca se ejecuta como código ni se obedece como instrucción, sobre todo cuando viene de anuncios, reseñas o webs de terceros (inyección de instrucciones).
- **Coste bajo control:**
  - tope de gasto por ejecución (`AI_BUDGET_USD`);
  - coste **medido** por agente y por análisis;
  - caché de resultados.
  
  El coste por empresa y mes es una cifra del pitch.
- **Modelos:** usa los modelos de Claude más recientes y adecuados al coste. Haiku para clasificar en volumen (reseñas, anuncios); Sonnet u Opus para cruzar, decidir y redactar. Verifica los nombres de los modelos y los precios en la documentación oficial.
- **Registra en `docs/uso-ia.md`** cada uso de IA del producto (función, modelo, por qué ahí, coste medido, cómo se verifica) y cada uso para construirlo.

## 5. Seguridad (no negociable)

- **Cero secretos en el repositorio.** Credenciales, tokens y claves van en `.env` (ignorado por git) y, en GitHub, en Secrets. Mantén `.env.example` sin valores reales. Revisa el diff antes de cada commit buscando secretos.
- **Los secretos tampoco pueden aparecer en la interfaz, los informes, las capturas, el vídeo ni la presentación.**
- **Datos:** la empresa de la demo es ficticia. Nada de datos personales reales: lo exigen las bases. De fuentes públicas, solo lo necesario y sin identificar a personas. Las reseñas se limpian al entrar y Claude no ve nombres de clientes (`domain/privacy.py`, `docs/datos-personales.md`).
- **Todo lo que escribe la IA se comprueba contra los datos** (`domain/grounding.py`): cifras con su unidad, fechas, cuentas, enlaces y teléfonos. Lo nuevo que genere texto de la IA tiene que pasar por ahí.
- **Respeta los sistemas de terceros:** sin carga abusiva (concurrencia limitada y esperas razonables), sin saltarse captchas ni protecciones y cumpliendo las condiciones de cada fuente.
- Valida y sanea toda entrada externa: configuración, URLs, respuestas web, salida de modelos.
- **Acciones con efecto real** (enviar correos, publicar respuestas): solo a destinatarios de prueba en la demo. Condiciones previas comprobadas, un tope, sin reintentos ciegos y sin repetir una acción ya hecha.
- Principio de mínimo privilegio. Dependencias: solo las necesarias, mantenidas y con versión fijada; revisa vulnerabilidades (`pip-audit` o equivalente) antes de añadirlas.
- Errores: nunca expongas trazas, rutas internas ni secretos en la interfaz, los logs o los informes.

## 6. Calidad del código

El código no se entrega para revisión, así que la calidad es **proporcional a un prototipo**. Aun así, el jurado puede pedir ver la arquitectura, y las secciones 3 y 5 se cumplen enteras.

### SOLID a rajatabla
- **S — Responsabilidad única:** cada agente, fuente y acción en su propio módulo.
- **O — Abierto/cerrado:** **añadir un especialista nuevo o una fuente nueva se hace extendiendo** (una nueva implementación registrada), sin tocar el coordinador. Es la prueba de que la hoja de ruta es creíble.
- **L — Sustitución de Liskov:** cualquier especialista cumple la misma interfaz y devuelve hallazgos con el mismo contrato.
- **I — Segregación de interfaces:** interfaces pequeñas (fuente, especialista, acción, medición).
- **D — Inversión de dependencias:** la lógica de los agentes depende de abstracciones, no del SDK del modelo, de la librería de correo ni de una API concreta. Las dependencias se inyectan.

### Código limpio y sostenible
- Nombres claros y en inglés en el código; funciones cortas que hacen una sola cosa; sin código muerto, duplicado ni comentado.
- Comentarios solo para explicar el **porqué**.
- Tipado estricto. Linter y formateador obligatorios desde el primer commit.
- **Tests:** toda lógica determinista (indicadores, conciliación, prioridad, reglas) lleva tests unitarios con los datos sintéticos como fixtures. Al menos un test de extremo a extremo del recorrido de la demo, con el modelo sustituido por un doble.
- Gestión de errores explícita: un fallo produce un resultado claro con su motivo, nunca un crash silencioso ni un dato inventado.
- Configuración fuera del código.

### Optimización
- Nada de esperas fijas cuando se puede esperar a una condición. Llamadas a la IA en paralelo cuando sean independientes (los especialistas). Caché.
- Registra las mejoras con su «antes y después» medido: es material para el pitch.

## 7. Mentores, demo y pitch

- **Amplitud en el pitch, profundidad en la demo.** Los seis agentes se cuentan; dos y el coordinador se enseñan funcionando.
- **El ejemplo de causa cruzada es el centro del pitch y de la demo.** Hay que enseñar el razonamiento del coordinador: qué dijo cada especialista y cómo llegó a la causa.
- **Respuestas preparadas:**
  - *«¿Cómo conseguiréis clientes?»* → las gestorías como canal.
  - *«¿Y si se equivoca en lo legal o financiero?»* → supervisión humana y autonomía por niveles.
  - *«¿En qué se diferencia de ChatGPT?»* → conectado a los datos, fuentes propias por agente, actúa y mide.
- **Los mentores pueden evaluar durante el día:** enseñadles avances pronto. Las bases puntúan la evolución durante el hackathon.
- `docs/DEMO.md` en cuanto exista el MVP: checklist, guion con tiempos, plan B (vídeo o captura de respaldo) y preguntas del jurado.
- **Cifras grandes con fuente:** coste por empresa y mes, tiempo del análisis frente a una consultora y precio frente a gestoría + agencia + consultora.
- **Antes de entregar:** el repositorio que ve el jurado contiene el producto. Decide qué documentos internos salen (las ideas descartadas ya salieron; quedan en el historial de git) y que solo haya un README.

## 8. Flujo de trabajo de cada sesión

1. Haz `git pull --rebase origin main`. Lee este archivo, `docs/ESTADO.md`, `README.md`, `docs/reto/` y los `docs/decisiones/` relevantes.
2. Entiende la tarea; si es ambigua, pregunta. Apúntala en «En curso» de `docs/ESTADO.md` (commit y push).
3. **Investiga** (sección 1) y propón el enfoque.
4. Implementa en pasos pequeños: **código → tests → lint y tipos → revisión del propio diff (seguridad, SOLID, limpieza, secretos) → commit → push** (sección 2).
5. Al acabar, actualiza `docs/ESTADO.md` (y `docs/uso-ia.md` si aplica), haz commit y push, y resume al usuario qué se hizo, qué falta, qué está verificado y cómo probarlo.

## Estructura del repositorio

```
CLAUDE.md              Normas para Claude Code (este archivo)
.claude/               Permisos compartidos (settings.json) y arranque del panel (launch.json)
README.md              Descripción, instalación y uso (único README de contenido)
src/vigia/            Código: domain, data (incl. intake), specialists, finance, coordinator, actions, connectors, llm,
                       crm.py (ficha única), remeasure.py, pipeline.py, app.py (panel) y __main__.py (consola)
tests/                 Tests unitarios y de extremo a extremo (sobre la clínica sintética)
data/demo/             Clínica sintética: mes-0 (antes) y mes-1 (un mes después)
docs/ESTADO.md         Estado del proyecto y traspaso entre sesiones
docs/reto/             Enunciado, entregables y bases oficiales (fuente de verdad)
docs/decisiones/       Registro de decisiones de arquitectura (ADR)
docs/negocio/          Entregables: canvas, marketing (con logo) y guion del pitch
docs/uso-ia.md         Cómo usamos la IA (entregable 2)
docs/fuentes.md        Fuentes externas: condiciones de uso, acceso y límites
docs/DEMO.md           Guía práctica de la demo
docs/red-team.md       Protocolo de auditoría independiente
docs/datos-personales.md  Qué datos personales se tratan, qué llega a Claude y cómo se borran
```

## Comandos

```bash
uv sync                                       # instalar (Python 3.13, versiones de uv.lock)
uv run ruff format . && uv run ruff check .   # formato y lint
uv run mypy src tests                         # tipado estricto
uv run pytest                                 # tests (incluye el recorrido de extremo a extremo)
uv run streamlit run src/vigia/app.py        # panel de la demo (http://localhost:8501)
uv run python -m vigia --fallo               # recorrido completo en la consola
uv run python -m vigia.data.synthetic        # regenerar la clínica sintética
uv run python -m vigia.connectors.http_api   # API del ERP de demo (VIGIA_ERP_TOKEN obligatorio)
uv run python -m vigia.connectors.balter_probe --autorizado  # prueba de la clave de BALTER (solo con visto bueno; ADR 006)
```

Antes de cada commit tienen que pasar el formato, el lint, los tipos y los tests. La CI (`.github/workflows/ci.yml`) los ejecuta en cada push, en Linux y en Windows.
