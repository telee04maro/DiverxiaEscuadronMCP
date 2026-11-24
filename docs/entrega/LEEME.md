# Ficheros para el Drive del Hackathon

Cada entregable se sube a la carpeta del equipo con este nombre:

| Entregable | Ficheros |
|---|---|
| 1 · Canvas (modelo de negocio) | `1-lienzo.pdf` (plantilla oficial rellena), `1-lienzo.png`; detalle con fuentes en `1-canvas-detalle.pdf` |
| 2 · Prototipo y uso de la IA | `2-prototipo.pdf` (capturas de las 7 pestañas del panel y cómo probarlo), `2-uso-de-la-ia.pdf`, carpeta `capturas/`, enlace al repositorio y `vigia-prototipo-codigo.zip` (código completo, sin secretos) |
| 3 · Marketing (logo, eslogan, estrategia) | `3-marketing.pdf`, `3-logo.png` |
| 4 · Guion del pitch | `4-guion-del-pitch.pdf` |

**El ZIP del código no está en el repositorio** (no se guarda un ZIP del repositorio dentro de sí mismo). Se genera fuera, junto a la carpeta del proyecto, desde la última versión de `main`:

```powershell
git archive --format=zip --prefix=Vigia/ -o ..igia-prototipo-codigo.zip origin/main
```

Se generan desde `docs/negocio/*.md`, `docs/uso-ia.md` y `docs/negocio/lienzo.html`. Si se cambia el texto, hay que volver a exportarlos.
