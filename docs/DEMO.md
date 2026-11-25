# Guía de la demo

Pensada para que cualquier miembro del equipo pueda presentarla sin conocer el código. El guion del pitch está en [`negocio/pitch.md`](negocio/pitch.md); aquí está la parte práctica.

## Antes de empezar (10 minutos antes)

- [ ] `uv sync` hecho y `uv run pytest` en verde.
- [ ] Panel abierto: `uv run streamlit run src/vigia/app.py` → <http://localhost:8501>, con la ventana ancha (diseño amplio).
- [ ] Pulsa **«Reiniciar la demo»** en la barra lateral para empezar limpio. Si has cambiado código, **reinicia el proceso de Streamlit**: no recarga los módulos.
- [ ] Decide el modo de IA. Con `ANTHROPIC_API_KEY` en `.env`, Claude lee, cruza y redacta. Sin clave, se usan reglas y la demo es idéntica y reproducible. **Si la red falla, la demo sin IA es el plan B.**
- [ ] Respaldo: `uv run python -m vigia` imprime todo el recorrido en la consola.

## Recorrido (unos 2 minutos de demo)

| Paso | Pestaña | Qué hacer | Qué señalar |
|---|---|---|---|
| 1 | 1 · Empresa | «Analizar con el equipo de agentes» | La clínica es ficticia; estas son las fuentes conectadas |
| 2 | 2 · Especialistas | Abrir un hallazgo de cada agente | Cada hallazgo lleva **evidencia y fuente**. Y «Lo que me falta para afinar»: no inventa datos |
| 3 | 3 · Coordinador | Leer la causa cruzada en voz alta | **Finanzas + Competencia + Atención**. «Es la temporada» queda descartado con datos. Plan en 7, 30 y 90 días con niveles de autonomía |
| 4 | 4 · Acciones | «Ejecutar…» → «Aprobar y enviar» → marcar las tareas hechas (no la campaña) | El recordatorio sale solo; la reclamación formal espera aprobación. **Enviar no es cobrar** |
| 5 | 5 · Un mes después | «Medir un mes después» | Cobros **comprobados con el banco** (2 de 3 facturas de la aseguradora); las quejas por la espera bajan del 86 % al 50 %. Dice «coincide», no «lo causó». Lo que no se hizo no se mide. El plan se reordena |
| 6 | 6 · Registro | Enseñar el registro y el coste de IA | Qué vio, qué decidió, qué hizo y qué comprobó cada agente |
| 7 | 7 · ERP y WhatsApp | «Simular mensaje de WhatsApp» dos veces con el mismo teléfono (o que escriba Hermes de verdad) | La 1.ª vez crea la oportunidad **sin responsable**; la 2.ª la añade como **nota**, sin duplicar. Al acabar: «Borrar todos los datos» |
| 8 | 7 → 8 · Clientes (CRM) | En la pestaña 7, nombre «Mutua Beta (ficticia)», **teléfono vacío** y correo `pagos@mutuabeta.example`; «Simular mensaje». Después, pestaña 8 (el interruptor «Incluir también las consultas del ERP» de la pestaña 1 viene activado) | **La ficha única:** finanzas (debe 8.633,50 €, paga a 95 días) y atención (consulta sin responsable) en el mismo cliente, con la alerta «contéstale antes de reclamarle». Ningún agente lo ve solo |
| 9 | 1 · Empresa → «Tu empresa» | Descargar una plantilla y subir un Excel | **Así entra cualquier pyme:** con sus Excel; lo que no sube sale como «lo que me falta» |

## Asistente de WhatsApp real (opcional)
Solo si la organización acepta Hermes y Zernio como componentes previos declarados. Guía completa: `whatsapp-hack/README.md` (ADR 008).
1. Arrancar la API del ERP de demo: `uv run python -m vigia.connectors.http_api --port 8765` con `VIGIA_ERP_TOKEN` (`--host 0.0.0.0` solo si el asistente corre en otro portátil de la misma red).
2. En el portátil del asistente: `HACK-Instalar.ps1` (destino por defecto, el ERP de Vigía), `-ActivarProduccion` y `-ActivarFondo -Segundos 10`.
3. Escribir desde un móvil del equipo empezando por `HTEST:`. Al dar nombre y correo, la consulta aparece en la pestaña 7 y el agente de atención y captación la cuenta.
4. Si escribe alguien del jurado: el bot le pide datos inventados. **No proyectar `-Monitor`** (muestra nombres y correos). Al acabar, «Borrar todos los datos» y `-Parar`.
5. Si falla WhatsApp, Zernio o Hermes: «Simular mensaje de WhatsApp» en la pestaña 7 hace lo mismo.

## Si algo falla en directo

- **Sin red o sin clave de IA:** la app pasa sola a modo reglas y el recorrido es el mismo.
- **La app no arranca:** ejecutar `uv run python -m vigia` en la terminal.
- **Sale algo «sin efecto» o «no se ejecutó»:** es la prueba de que Vigía no da nada por hecho sin evidencia.

## Preguntas probables del jurado

Están en [`negocio/pitch.md`](negocio/pitch.md#preguntas-probables-del-jurado).
