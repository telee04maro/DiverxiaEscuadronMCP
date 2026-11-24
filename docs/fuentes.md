# Fuentes externas

Cada fuente que use un agente se registra aquí **antes de codificarla**, comprobada en su documentación oficial (ver `CLAUDE.md`, «Fuentes externas»). Si una fuente no es accesible durante el hackathon, se usa una instantánea sintética con el mismo formato y se dice en la demo.

Verificación del 24/11/2026, solo con documentación oficial. Lo marcado *(por verificar)* no se pudo confirmar.

## Resumen

| Fuente | Agente | Acceso oficial | Condiciones | En el prototipo |
|---|---|---|---|---|
| **Biblioteca de Anuncios de Meta** | Competencia | API `GET graph.facebook.com/<versión>/ads_archive`, gratuita. Exige confirmar identidad en Facebook (puede tardar días), cuenta de Meta for Developers, una app y un token | Cubre anuncios **de cualquier tipo entregados en la UE** el último año (`ad_type=ALL`, `ad_reached_countries=['ES']`). **Scraping prohibido** sin permiso escrito (Automated Data Collection Terms, 7/10/2024) | **Instantánea sintética con los campos reales de la API:** `page_name`, `ad_creative_bodies`, `ad_delivery_start_time`, `ad_delivery_stop_time`, `publisher_platforms`, `ad_snapshot_url`. En producción, la API con identidad verificada |
| **Centro de Transparencia de Google Ads** | Competencia | Sin API pública documentada para desarrolladores *(por verificar)*. Hay un dataset público en BigQuery, `bigquery-public-data.google_ads_transparency_center`, que cubre el EEE con retraso | Uso solo «para información o investigación», sin monetizar. Scraping no recomendado | **Instantánea sintética** (en los resultados de búsqueda, anuncio patrocinado de la competencia) |
| **Posiciones en Google (SEO/SEM)** | Competencia | Scraping de resultados **prohibido** por la política de spam de Google. La Custom Search JSON API está cerrada a nuevos clientes y se apaga el 1/1/2027. Search Console API: solo datos del **propio** sitio | Search Console: OAuth y propiedad verificada | **Posiciones sintéticas.** En producción, Search Console para el negocio propio; la competencia, con un proveedor autorizado *(por elegir)* |
| **Reseñas de Google (Places API)** | Competencia | `GET places.googleapis.com/v1/places/PLACE_ID` con máscara de campos. Necesita API key y facturación activada | **Máximo 5 reseñas** por sitio. **No se pueden almacenar** ni redistribuir: se consultan en vivo y se muestran con la atribución al autor y a Google Maps. Cuota gratuita de 1.000 llamadas al mes por SKU | **Reseñas sintéticas.** En producción: consulta en vivo con atribución, o las reseñas que la propia empresa exporta de su ficha |
| Contabilidad, facturas, banco y sesiones (CSV) | Finanzas | Datos de la propia empresa | Datos sintéticos (las bases prohíben datos personales) | Clínica ficticia generada en `vigia.data.synthetic` |

## Consecuencias para el producto

- **En la demo se dice claramente** que los datos de la competencia son instantáneas sintéticas en el formato oficial. El agente de competencia trabaja igual sobre la API real porque el formato es el mismo.
- **Las reseñas de terceros no se guardan:** el agente las analiza al consultarlas y guarda solo las conclusiones (temas y notas medias), nunca el texto ni el autor.
- **Ruta a producción:**
  - Meta Ad Library API con identidad verificada.
  - Search Console del cliente.
  - Places API con facturación.
  - Para posiciones de competencia en buscadores, un proveedor con licencia (pendiente de elegir).
