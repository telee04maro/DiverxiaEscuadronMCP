# Ficheros para el Drive del Hackathon

Cada entregable se sube a la carpeta del equipo con este nombre:

| Entregable | Ficheros |
|---|---|
| 1 · Canvas (modelo de negocio) | `1-lienzo.pdf` (plantilla oficial rellena), `1-lienzo.png`; detalle con fuentes en `1-canvas-detalle.pdf` |
| 2 · Prototipo y uso de la IA | `2-prototipo.pdf` (capturas de las 8 pestañas del panel, incluida la ficha única de cliente, y cómo probarlo), `2-uso-de-la-ia.pdf`, `2-datos-personales.pdf` (qué datos se tratan y qué llega a Claude), carpeta `capturas/`, enlace al repositorio y `vigia-prototipo-codigo.zip` (código completo, sin secretos, con el asistente de WhatsApp de `whatsapp-hack/`) |
| 3 · Marketing (logo, eslogan, estrategia) | `3-marketing.pdf`, `3-logo.png` |
| 4 · Guion del pitch | `4-guion-del-pitch.pdf`, el audio del inicio (`../negocio/pitch-audio-gancho.mp3`) y la imagen de respaldo «antes y después» (`../negocio/recorrido-antes-despues.png`) |
| Plan de negocio (apoyo al canvas) | `5-plan-de-negocio.pdf` |
| Diapositiva final: herramientas de IA (la piden las bases) | `6-herramientas-de-ia.png` y `6-herramientas-de-ia.pdf` |

**El ZIP del código no está en el repositorio** (no se guarda un ZIP del repositorio dentro de sí mismo). Se genera fuera, junto a la carpeta del proyecto, desde la última versión de `main`:

```powershell
git archive --format=zip --prefix=Vigia/ -o ..\vigia-prototipo-codigo.zip origin/main
```

`2-prototipo.pdf` se genera desde `docs/negocio/prototipo.html` con las capturas de `capturas/` (panel con la marca nueva, en modo reglas). El resto se genera desde `docs/negocio/*.md`, `docs/uso-ia.md` y `docs/negocio/lienzo.html`. Si se cambia el texto, hay que volver a exportarlos.

**Marca:** un logo («Atalaya», `docs/negocio/logo*.svg`), dos colores (azul petróleo `#1D5C7A` y terracota `#D9824E`) y una tipografía (Inter) en todo, como pide la organización. Eslogan: «Vuelve a lo que importa.»
