# Guía de la demo

Pensada para que cualquier miembro del equipo pueda presentarla sin conocer el código. El guion del pitch está en [`negocio/pitch.md`](negocio/pitch.md); aquí está la parte práctica.

## Antes de empezar (10 minutos antes)

- [ ] `uv sync` hecho y `uv run pytest` en verde.
- [ ] Panel abierto: `uv run streamlit run src/vigia/app.py` → <http://localhost:8501>, con la ventana ancha (diseño amplio).
- [ ] Pulsa **«Reiniciar la demo»** en la barra lateral para empezar limpio. Si has cambiado código, **reinicia el proceso de Streamlit**: no recarga los módulos.
- [ ] Decide el modo de IA. Con `ANTHROPIC_API_KEY` en `.env`, Claude lee, cruza y redacta. Sin clave, se usan reglas y la demo es idéntica y reproducible. **Si la red falla, la demo sin IA es el plan B.**
- [ ] Respaldo: `uv run python -m vigia --fallo` imprime todo el recorrido en la consola.

## Recorrido (unos 2 minutos de demo)

| Paso | Pestaña | Qué hacer | Qué señalar |
|---|---|---|---|
| 1 | 1 · Empresa | «Analizar con el equipo de agentes» | La clínica es ficticia; estas son las fuentes conectadas |
| 2 | 2 · Especialistas | Abrir un hallazgo de cada agente | Cada hallazgo lleva **evidencia y fuente**. Y «Lo que me falta para afinar»: no inventa datos |
| 3 | 3 · Coordinador | Leer la causa cruzada en voz alta | **Finanzas + Competencia**. «Es la temporada» queda descartado con datos. Plan en 7, 30 y 90 días con niveles de autonomía |
| 4 | 4 · Acciones | «Ejecutar…» → «Aprobar y enviar» → marcar las tareas hechas (no la campaña) | El recordatorio sale solo; la reclamación formal espera aprobación. **Enviar no es cobrar** |
| 5 | 5 · Un mes después | Activar en la barra lateral «Fallo inyectado» → «Medir un mes después» | El pago con **1 céntimo de menos no se da por cobrado**. El plan se reordena |
| 6 | 6 · Registro | Enseñar el registro y el coste de IA | Qué vio, qué decidió, qué hizo y qué comprobó cada agente |
| 7 | 7 · ERP y WhatsApp | «Simular mensaje de WhatsApp» dos veces con el mismo teléfono (o que escriba Hermes de verdad) | La 1.ª vez crea la oportunidad **sin responsable**; la 2.ª la añade como **nota**, sin duplicar. Al acabar: «Borrar todos los datos» |
| 8 | 1 · Empresa → «Tu empresa» | Descargar una plantilla y subir un Excel | **Así entra cualquier pyme:** con sus Excel; lo que no sube sale como «lo que me falta» |

## Asistente de WhatsApp real (opcional)
Solo si la organización acepta Hermes y Zernio como componentes previos declarados:
1. Arrancar `uv run python -m vigia.connectors.http_api --host 0.0.0.0 --port 8765` con `VIGIA_ERP_TOKEN` (ver `docs/integracion-whatsapp-erp.md`).
2. Escribir desde **móviles del equipo**. Si escribe alguien del jurado, avisar de la privacidad y borrar los datos después.

## Si algo falla en directo

- **Sin red o sin clave de IA:** la app pasa sola a modo reglas y el recorrido es el mismo.
- **La app no arranca:** ejecutar `uv run python -m vigia --fallo` en la terminal.
- **Sale algo «sin efecto» o «no se ejecutó»:** es la prueba de que Vigía no da nada por hecho sin evidencia.

## Preguntas probables del jurado

Están en [`negocio/pitch.md`](negocio/pitch.md#preguntas-probables-del-jurado).
