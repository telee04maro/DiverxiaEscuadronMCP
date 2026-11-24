# Ficheros para el Drive del Hackathon

Cada entregable se sube a la carpeta del equipo con este nombre:

| Entregable | Ficheros |
|---|---|
| 1 · Canvas (modelo de negocio) | `1-lienzo.pdf` (plantilla oficial rellena), `1-lienzo.png`; detalle con fuentes en `1-canvas-detalle.pdf` |
| 2 · Prototipo y uso de la IA | `2-prototipo.pdf` (capturas de las 8 pestañas del panel, incluida la ficha única de cliente, y cómo probarlo), `2-uso-de-la-ia.pdf`, `2-datos-personales.pdf` (qué datos se tratan y qué llega a Claude), carpeta `capturas/`, enlace al repositorio y `vigia-prototipo-codigo.zip` (código completo, sin secretos) |
| 3 · Marketing (logo, eslogan, estrategia) | `3-marketing.pdf`, `3-logo.png` |
| 4 · Guion del pitch | `4-guion-del-pitch.pdf` |

**El ZIP del código no está en el repositorio** (no se guarda un ZIP del repositorio dentro de sí mismo). Se genera fuera, junto a la carpeta del proyecto, desde la última versión de `main`:

```powershell
git archive --format=zip --prefix=Vigia/ -o ..igia-prototipo-codigo.zip origin/main
```

`2-prototipo.pdf` se genera desde `docs/negocio/prototipo.html`, recortando las capturas de `capturas/` (sin la barra lateral y en trozos de una página). El resto se genera desde `docs/negocio/*.md`, `docs/uso-ia.md` y `docs/negocio/lienzo.html`. Si se cambia el texto, hay que volver a exportarlos.
