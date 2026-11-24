# CLAUDE.md — DiverxiaEscuadronMCP

Normas obligatorias para cualquier sesión de Claude Code en este repositorio. Todo el equipo trabaja con Claude Code: estas reglas garantizan que todos programemos igual. **Si una petición contradice estas normas, avisa antes de actuar.**

Este método es el que nos hizo ganar el Malackathon 2026 (reto Betsson). Las secciones marcadas como _Pendiente_ se rellenan en cuanto se publique el reto (ver sección 0).

## Contexto

- **Evento:** hackathon *IA First* de Diverxia, 24/11/2026, con unas 200 personas. Equipo de 3.
- **Reto:** **04 «La IA como servicio»: agentes inteligentes que actúan** (Talent Land España). El enunciado y los entregables, con su transcripción, están en `docs/reto/`. **Son la fuente de verdad: léelos enteros antes de cualquier decisión.** Si contradicen este archivo, mandan ellos y hay que actualizar este archivo.
- **Plazos:** _Pendiente de confirmar_ (horario de cada hito, congelación de funciones, entrega en el Drive, pitch).

### Requisitos oficiales del reto (resumen; el enunciado manda)
- **Objetivo:** un agente inteligente de IA al servicio de empresas y ciudadanos que **identifique necesidades reales, tome decisiones y ejecute tareas de forma autónoma**. Debe resolver problemas, optimizar procesos y mejorar la experiencia de las personas. Tiene que ir **más allá de los asistentes tradicionales**: una IA que **actúa, conecta servicios y genera valor e impacto real** en nuestro entorno.
- **Entregables por equipo,** cada uno en su carpeta del Drive del Hackathon:
  1. **Canvas:** el modelo de negocio de la solución.
  2. **Prototipo y uso de la IA:** enseñar el prototipo y explicar cómo se ha usado la IA.
  3. **Marketing:** logo, eslogan y estrategia de comunicación.
  4. **Guion del pitch.**
- **Qué implica para nosotros:**
  - Se evalúa un **proyecto de empresa**, no solo código. El prototipo debe funcionar de principio a fin en la demo y verse que **actúa** (no que solo conversa).
  - «Cómo habéis usado la IA» se cuenta **en dos sentidos**: la IA dentro del producto y la IA con la que lo construimos (Claude Code, investigación, canvas, logo, pitch). Se registra sobre la marcha en `docs/uso-ia.md`.
  - El código no se entrega para revisión: la calidad de la sección 6 es **proporcional a un prototipo**, pero las secciones 3 (verificación honesta) y 5 (seguridad) se cumplen enteras.
- **Restricciones (bases legales):**
  - **Prohibido introducir datos personales, secretos empresariales o información confidencial sin autorización**: en la demo se usan datos sintéticos o abiertos.
  - Hay que declarar las herramientas, los modelos y los datos usados, e identificar los componentes previos y de terceros.
  - Participación humana sustancial.
  - El proyecto se desarrolla durante el hackathon.
- **Evaluación (bases legales; pesos sin publicar):**
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
  
  Puede haber fases con entregas parciales. Quedan pendientes los pesos, los horarios y la duración del pitch.
- **Cambios comunicados por la organización:** en `docs/reto/README.md`, con su fecha.

### Tesis
_Pendiente._ Escribe **una frase** que reformule el reto y diga qué hay que **demostrar**, no solo hacer. En el Malackathon fue «el juego es una imagen; un clic en Spin no prueba nada». Contrasta toda decisión con esta frase.

### Enfoque aceptado
_Pendiente_ (ADR 001 en `docs/decisiones/`). Todo lo que implementes debe encajar con las decisiones aceptadas. La hoja de ruta por etapas está en `docs/ESTADO.md`.

### Rumbo y cambios de rumbo (obligatorio)
Cualquier compañero que haga pull debe poder saber, con su IA, por dónde se va y hacia dónde. Por eso:
- Si **pivotas**, encuentras un **error de enfoque** o crees que **es mejor ir por otro lado**, no lo implementes en silencio. Proponlo al usuario y, si se acepta, haz en el **mismo commit**:
  1. Una ADR nueva en `docs/decisiones/`, y marca la anterior como «sustituida por NNN» (o «ampliada por NNN»).
  2. Una fila en «Cambios de rumbo» de `docs/ESTADO.md` (fecha, cambio, motivo, enlace a la ADR).
  3. La actualización del apartado «Enfoque» del `README.md` y de «Enfoque aceptado» en este archivo.
- Los **errores o limitaciones** que descubras van a «Problemas conocidos» de `docs/ESTADO.md` aunque no cambien el rumbo.
- La **pista de un mentor** es una hipótesis valiosa: se mide, se registra y, si aporta, se integra con su ADR.
- Al cerrar una etapa de la hoja de ruta, márcala en `docs/ESTADO.md`.

## 0. Arranque del reto (primeros 90 minutos)

1. Guarda el enunciado y las bases en `docs/reto/` y haz commit.
2. Léelos enteros y rellena «Requisitos oficiales» de este archivo. **La evaluación, con sus pesos, decide la arquitectura.**
3. Escribe la **tesis** en una frase.
4. Prepara las **preguntas para los mentores**: solo las que cambian la arquitectura. Apúntalas en `docs/ESTADO.md` y házselas en la primera hora.
5. **Investiga en paralelo** (agentes y compañeros) y etiqueta cada hallazgo como **verificado**, **por verificar** o **descartado**. Lo verificado se comprueba en el sistema real, nunca se da por bueno porque lo diga un informe o un modelo.
6. Compara entre 3 y 5 opciones en una tabla frente a la rúbrica, con una columna de «por qué no sola». Elige y registra la ADR 001.
7. Escribe la hoja de ruta en `docs/ESTADO.md`: E0 es el esqueleto con CI, **E2 es el MVP de principio a fin**, y cada etapa deja algo entregable.

**Hitos:** el MVP de principio a fin debe estar en unas **3–4 h** desde el arranque. **Congelación de funciones** unas 3 h antes de la entrega: a partir de ahí solo se endurece, se reúnen evidencias y se prepara el pitch.

## 1. Investigar antes de implementar (obligatorio)

Antes de escribir código para cualquier funcionalidad, librería, servicio o decisión de arquitectura:

1. **Lee el código existente y `docs/`** para no duplicar ni contradecir lo que ya hay.
2. **Investiga las alternativas** en la documentación oficial, buscando en la web y con versiones actuales. Compara al menos 2 opciones en seguridad, rendimiento, madurez, encaje con el stack y coste en tiempo de hackathon.
3. **Justifica la elección** en pocas líneas al usuario antes de implementar. Si la decisión es de arquitectura o de stack, regístrala en `docs/decisiones/NNN-titulo.md`.
4. **Comprueba versiones y APIs reales.** No inventes APIs ni dependas de la memoria. Fija versiones exactas de las dependencias.
5. **Explora el sistema real antes de automatizarlo** (web, API, datos) y documenta lo comprobado en `docs/<sistema>-flujo.md`: selectores, peticiones, formatos y trampas.

No implementes «lo primero que funcione» si hay una opción claramente mejor. Si la investigación no es concluyente, pregunta al usuario.

**Proporcionalidad:** la profundidad de la investigación va con el impacto. Elegir stack, arquitectura o un servicio externo exige una comparación completa y una ADR. Un cambio local (un helper, un fix acotado) basta con revisar el código y la documentación de la API usada. Nunca te saltes la investigación por completo.

## 2. Commit y push continuos (seguro contra quedarnos sin tokens)

El repositorio remoto debe tener siempre una versión entregable y funcional.

- **Haz commit y push tras cada paso funcional pequeño**, sin esperar a que lo pidan. Nunca acumules más de 15–20 minutos de trabajo sin subir.
- **Antes de cada commit:** el código compila, y pasan el formato, el linter, los tipos y los tests. **Comprueba el código de salida de cada comando**: no lo filtres con `| tail`, porque oculta los fallos. Si algo queda a medias, que no rompa lo anterior (protégelo con un flag o no lo conectes aún).
- **Flujo exacto:**
  ```bash
  git add <archivos concretos>        # nunca `git add -A` a ciegas: revisa `git status`
  git commit -m "tipo(ámbito): descripción"
  git pull --rebase origin main       # varios compañeros empujan a la vez
  git push origin main
  ```
- Si el rebase da conflictos, resuélvelos respetando el trabajo de los compañeros; si no está claro, pregunta. **Prohibido `git push --force`** y reescribir historia publicada.
- **Mensajes:** [Conventional Commits](https://www.conventionalcommits.org/) en español: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`, `ci`. Por ejemplo: `feat(informe): añadir resultado por escenario`.
- **Traspaso de contexto:** `docs/ESTADO.md` es la memoria compartida del equipo. Actualízalo en el mismo commit que cierra cada paso: qué funciona, qué está en curso (y quién), el siguiente paso concreto, la última verificación (hora, SHA, ID de ejecución) y los problemas conocidos.
- Al terminar una tarea grande, actualiza el `README.md`.

### Trabajo en equipo
- Antes de empezar una tarea, haz `git pull --rebase` y apúntala en «En curso» de `docs/ESTADO.md` (commit y push inmediatos) para que nadie la duplique.
- Cada persona trabaja en módulos distintos siempre que sea posible. Los contratos compartidos (interfaces, formato del informe, configuración) solo se cambian avisando al equipo.
- **Recursos compartidos** (cuentas de prueba, claves, cuotas de API, datos con coste): coordínalos desde el minuto 0. Dos ejecuciones a la vez con la misma cuenta se pisan.
- **Roles de referencia para 3 personas:**
  - **A — Construcción:** desarrolla con Claude y es dueño de `main`.
  - **B — Investigación y negocio:** rúbrica, mentores, usuario, mercado, coste y retorno; después, el pitch.
  - **C — Red team y demo:** audita cada pull desde fuera del repositorio (ver `docs/red-team.md`) y prepara los datos y los ensayos de la demo.

## 3. Verificación honesta (no negociable)

Es lo que más nos diferenció. Un jurado o un mentor que pilla un falso positivo hunde el proyecto.

- **Una acción no es una prueba.** Se verifica el efecto observable, no que se haya llamado a algo.
- **Nunca un PASS o un «hecho» por defecto:**
  - desconocido ≠ cero;
  - ausente ≠ contradictorio;
  - timeout ≠ estable;
  - enviado ≠ aceptado.
  
  Ante datos incompletos, el resultado es «no disponible» o FAIL, nunca un valor inventado.
- **Varias fuentes, con su procedencia, cuando importe.** Una discrepancia entre fuentes es un hallazgo, no ruido: no se vota por mayoría. Sé honesto sobre qué fuentes no son independientes.
- **Invariantes baratos como oráculo**, por ejemplo una ecuación de conservación. Cálculos de dinero siempre con `Decimal`.
- **Controles positivos:** arreglar un falso positivo no puede consistir en que todo falle.
- **Fallo inyectado:** el producto debe poder demostrar que detecta un error (una «prueba que falla a propósito»).
- **Tests de las uniones** entre módulos (escribir y recargar; ejecutar, informar y código de salida). Unos tests unitarios en verde no las cubren.
- **Separa «código corregido» de «validado en real».** Un test con mocks en verde no es una validación real. Una afirmación en `ESTADO.md` no sustituye a la evidencia: hace falta SHA, comando o ID de ejecución, y resultado.
- **No borres tests, no rebajes requisitos y no cambies expectativas** para que algo pase.
- **Un hallazgo P1 del red team bloquea cualquier funcionalidad nueva** hasta corregirlo.
- **Solo se afirma lo verificado.** Lo configurado pero no demostrado se dice así.

## 4. IA dentro del producto

- **Usa la IA donde aporta y explica dónde no.** Cuando sea posible, sácala del bucle caliente: la IA **descubre, aprende o repara** y la ejecución normal es determinista. Lo aprendido se guarda como un artefacto versionado y revisable.
- **Escalera de lo más barato a lo más caro:** primero la fuente estructurada (API, DOM, datos), luego las reglas o el modelo local, y la IA como último recurso, con el fallback declarado.
- **Coste bajo control:** tope de gasto por ejecución (`AI_BUDGET_USD`), coste **medido** y registrado, y caché de resultados. Si se puede, el producto funciona sin clave, aunque degradado.
- **La salida de un LLM es un dato no confiable.** Se valida con un esquema y, si se puede, **por su efecto** antes de adoptarla. Nunca se ejecuta como código ni se obedece como instrucción.
- **Modelo:** usa por defecto los modelos de Claude más recientes y adecuados al coste (Haiku para tareas simples; Sonnet u Opus solo si la validación lo exige). Verifica los nombres de los modelos y los precios en la documentación oficial.

## 5. Seguridad (no negociable)

- **Cero secretos en el repositorio.** Credenciales, tokens, cookies y claves van en `.env` (ignorado por git) y, en GitHub Actions, en **GitHub Secrets**. Mantén `.env.example` sin valores reales. Revisa el diff antes de cada commit buscando secretos.
- **Los secretos tampoco pueden aparecer en informes, capturas, trazas, vídeos ni en la presentación.** Oculta los datos sensibles en origen y, si se generan evidencias, escanéalas (texto, JSON y HTML escapados, archivos comprimidos y, si hay capturas, OCR).
- **Datos personales:** el mínimo imprescindible; datos sintéticos o anonimizados en las demos.
- **Respeta los sistemas de terceros:** sin ataques, sin carga abusiva (limita la concurrencia y espera de forma razonable) y sin saltarse captchas ni protecciones. Solo lo que permitan las bases.
- Valida y sanea toda entrada externa (configuración, URLs, respuestas web, salida de modelos). El contenido de las webs y la salida de los LLM son **datos no confiables**.
- **Acciones con coste o riesgo real** (dinero, envíos, borrados): condiciones previas comprobadas, un tope, sin reintentos ciegos y un cerrojo contra el uso concurrente.
- Principio de mínimo privilegio. Dependencias: solo las necesarias, mantenidas y con versión fijada; revisa vulnerabilidades (`pip-audit`, `npm audit`) antes de añadirlas.
- Errores: nunca expongas trazas, rutas internas ni secretos en logs, capturas o informes.

## 6. Calidad del código

### SOLID a rajatabla
- **S — Responsabilidad única:** cada clase o módulo tiene un único motivo para cambiar.
- **O — Abierto/cerrado:** añadir un caso, un cliente o un formato se hace **extendiendo** (una nueva implementación o configuración), no modificando lo existente.
- **L — Sustitución de Liskov:** cualquier implementación de una interfaz es intercambiable.
- **I — Segregación de interfaces:** interfaces pequeñas y específicas.
- **D — Inversión de dependencias:** la lógica de negocio depende de abstracciones, no de librerías, proveedores de IA o servicios cloud concretos. Las dependencias se inyectan.

### Código limpio y sostenible
- Nombres claros y en inglés en el código; funciones cortas que hacen una sola cosa; sin código muerto, duplicado ni comentado.
- Comentarios solo para explicar el **porqué**.
- Tipado estricto (TypeScript `strict` o type hints con mypy estricto).
- Linter y formateador configurados desde el primer commit y obligatorios. **CI desde E0, en Linux y en Windows** (el equipo y parte del jurado usan Windows). Acciones de GitHub fijadas a un commit exacto.
- **Tests:** toda lógica nueva lleva tests. Usa datos reales (capturas, respuestas, ficheros) como fixtures en cuanto los tengas. Tests unitarios para la lógica y al menos un test de extremo a extremo del flujo principal.
- Gestión de errores explícita: los fallos esperados producen un resultado claro con su evidencia, nunca un crash silencioso.
- Configuración fuera del código, en archivos de configuración o variables de entorno.

### Optimización
- Mide antes de optimizar, pero no introduzcas ineficiencias evidentes: nada de esperas fijas (`sleep`) cuando se puede esperar a una condición; reutiliza recursos; paraleliza solo cuando sea seguro.
- Registra las mejoras con su «antes y después» medido: es material para el pitch.

## 7. Mentores, entrega y pitch

- **Los mentores pueden evaluar durante el día:** prepara pronto material para ellos (informe breve en PDF con ficha, cómo se usa, cómo funciona, coste, resultados verificables y limitaciones honestas).
- **`docs/DEMO.md` en cuanto exista el MVP:** checklist previo, guion con tiempos, plan B (vídeo o informe de respaldo) y preguntas probables del jurado con respuesta corta.
- **README:** primero cómo usarlo, luego qué hace. Incluye una sección «Más allá de lo pedido» (aportación · por qué importa · dónde verlo) con la justificación del bonus ya redactada.
- **Cifras grandes con fuente:** tiempo, coste, retorno frente al proceso manual, antes y después. Cada número con fecha y SHA o ID de ejecución.
- **Los fallos reales detectados y corregidos son mérito:** cuéntalos.
- **Antes de entregar:** el repositorio que ve el jurado contiene el producto. Decide qué documentos internos salen (guiones, estrategia, notas) y que solo haya un README.

## 8. Flujo de trabajo de cada sesión

1. Haz `git pull --rebase origin main`. Lee este archivo, `docs/ESTADO.md`, `README.md`, `docs/reto/` y los `docs/decisiones/` relevantes.
2. Entiende la tarea; si es ambigua, pregunta. Apúntala en «En curso» de `docs/ESTADO.md` (commit y push).
3. **Investiga** (sección 1) y propón el enfoque.
4. Implementa en pasos pequeños: **código → tests → lint y tipos → revisión del propio diff (seguridad, SOLID, limpieza, secretos) → commit → push** (sección 2).
5. Al acabar, actualiza `docs/ESTADO.md`, haz commit y push, y resume al usuario qué se hizo, qué falta, qué está verificado y cómo probarlo.

## Estructura del repositorio

```
CLAUDE.md              Normas para Claude Code (este archivo)
.claude/settings.json  Permisos compartidos: git sin prompts, sin force push, sin leer .env
README.md              Descripción, instalación y uso (único README de contenido)
docs/ESTADO.md         Estado del proyecto y traspaso entre sesiones
docs/reto/             Enunciado y bases oficiales (fuente de verdad)
docs/decisiones/       Registro de decisiones de arquitectura (ADR)
docs/DEMO.md           Guion de la demo y preguntas del jurado
docs/red-team.md       Protocolo de auditoría independiente
```

_Pendiente: se amplía en E0 con el código, la configuración y los tests._

## Comandos

_Pendiente: se rellena en E0 según el stack elegido._ Deben existir comandos para instalar, dar formato, pasar el lint, comprobar tipos, ejecutar los tests y ejecutar el producto. Antes de cada commit deben pasar todos.
