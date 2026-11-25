# Protocolo de red team (auditoría independiente)

Una persona (con su propio agente de IA) audita cada versión **desde fuera del repositorio** y nunca escribe en el producto. En proyectos anteriores encontró falsos PASS que nos habrían hundido delante del jurado.

## Dónde trabaja

- Una carpeta hermana del checkout (por ejemplo `../auditoria/`) con sus tests, sus resultados y su checklist. **No se suben al repositorio.**
- Una subcarpeta por ronda, `revisiones/RNN-<sha7>/`, con los logs, los resultados (JUnit o JSON) y el informe de la ronda. Nunca se sobrescribe una ronda anterior.

## Cada ronda (unos 30 minutos)

1. **Pull controlado:** árbol limpio, `git pull --ff-only`, anotar el SHA anterior y el nuevo, y **leer el diff entero**, no solo los mensajes de commit. No se ejecuta nada con coste o riesgo real (dinero, IA de pago, envíos) por el mero hecho de recibir un pull.
2. **Puertas oficiales:** formato, lint, tipos y tests, comprobando el código de salida de cada una.
3. **Tests propios de auditoría:**
   - Adversariales: valores por defecto, nulos, negativos, NaN, entradas malformadas, datos de otra procedencia.
   - De uniones entre módulos.
   - De extremo a extremo con datos sintéticos.

   Siempre con **controles positivos**.
4. **Informe de la ronda** con los hallazgos en el formato de abajo, ordenados por prioridad, y las tres correcciones siguientes recomendadas.
5. **Reverificación** en la ronda siguiente, separando los casos «conservados» de los «nuevos» para que el recuento no engañe.

## Formato de cada hallazgo (para pasárselo a Claude)

```markdown
### RNN-XX — P1: <qué falla, en una frase>
- **Código:** ruta/archivo:línea
- **Reproducción:** entrada exacta que lo provoca
- **Contrato que debe cumplirse:** comportamiento correcto, sin atajos
- **Aceptación:** nombre del test que debe pasar + casos frontera + control positivo
- **Prohibido:** cambiar la expectativa, borrar el test o convertir el error en éxito
```

**Prioridades:**
- **P1:** falso positivo, riesgo real (dinero, datos, secretos) o entregable roto. Bloquea cualquier funcionalidad nueva hasta corregirlo.
- **P2:** robustez.
- **Opcional:** no bloquea.

## Dónde mirar primero (lo que más ha fallado en proyectos anteriores)

- **Éxitos por defecto:**
  - desconocido tratado como cero;
  - `None == None` tratado como «no cambió»;
  - timeout tratado como estable;
  - un éxito duplicado que oculta un fallo;
  - código de salida 0 con un fallo dentro.
- **Uniones:** guardar y recargar, ejecución → informe → código de salida, configuración inválida.
- **Procedencia:** datos de otra fuente (otro iframe, otro dominio, otra sesión) aceptados como propios; un error HTTP leído como una respuesta válida.
- **Secretos:** tokens en URLs de error, en JSON o HTML escapados, en los resúmenes y en las capturas.
- **Acciones reales:** condiciones previas, topes, reintentos, uso concurrente.
- **Portabilidad:** rutas y finales de línea en Windows.

## Checklist de entrega

Entre 60 y 100 criterios como máximo, con un ID estable (`ENT-001`, `SEC-003`…). Las reglas:

- `[x]` solo con una evidencia identificable: ID, SHA, prueba, resultado y ruta. Que lo diga Claude no basta.
- Si un cambio invalida algo, se vuelve a `[ ]` como «reabierto» y se conserva la historia.
- Lo que no aplica queda como «N/A justificado».
- Sin porcentajes: **un solo bloqueo P1 impide declarar lista la entrega**.
- Los tests locales, la CI remota, la ejecución real y la demo son evidencias distintas; nunca se cuenta una como otra.
