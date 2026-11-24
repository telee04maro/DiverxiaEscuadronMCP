# Conectar el BALTER real

Hoy Vigía lee las consultas de un **ERP de demo con la forma de BALTER** ([ADR 005](decisiones/005-conectores-y-captacion.md)). Para conectarlo al BALTER de verdad hacen falta las tres cosas de abajo. **Sin las tres no se conecta**: BALTER tiene datos de clientes reales, y las bases del hackathon prohíben usarlos sin autorización.

## Lo que tiene que aportar el equipo

| # | Qué | Dónde va | Cómo |
|---|---|---|---|
| 1 | **Documentación de la API de BALTER**: URL base, cómo se autentica (token, usuario y contraseña, OAuth…), endpoints de contactos y oportunidades, formato de las respuestas y límites de uso | `docs/balter/` (PDF o enlace) | Se puede compartir con Claude: no es un secreto. Si incluye ejemplos con datos reales de clientes, quítalos antes |
| 2 | **Visto bueno por escrito** de la empresa dueña de BALTER para una prueba **de solo lectura** | Una línea en la tabla «Cambios de rumbo» de `docs/ESTADO.md`: quién lo da, fecha y alcance | Basta un correo o un mensaje. Si existe un **entorno de pruebas**, mejor que producción |
| 3 | **Credenciales** | `.env` (nunca en el chat, nunca en `.env.example`, nunca en un commit) | Rellenar `BALTER_URL`, `BALTER_USER` y `BALTER_TOKEN`. Si la autenticación es de otro tipo, se añade la variable que diga la documentación |

Comprobar que `.env` no se sube:

```powershell
git check-ignore -v .env
```

Tiene que responder con una línea de `.gitignore`. Si no responde nada, **no hagas commit** y avisa.

## Lo que hará Claude después (en este orden)

1. **Leer la documentación** y apuntar en una ADR nueva qué endpoints se usan y cuáles no.
2. **Prueba mínima de solo lectura**: autenticarse y pedir un recuento o un catálogo, sin descargar datos personales. Resultado en `docs/ESTADO.md` (fecha, comando y respuesta, sin secretos).
3. **`BalterConnector`**: una implementación nueva de `CrmConnector` (`src/vigia/connectors/`), **solo con `list_opportunities`**. Los agentes y el coordinador no cambian.
4. **Tests** con respuestas grabadas y anonimizadas, nunca contra producción en la CI.
5. **Nunca** se escribe en BALTER desde Vigía (crear contactos, notas u oportunidades) sin un segundo visto bueno explícito y un entorno de pruebas.

## Qué se gana

El agente de atención y captación medirá las consultas reales: tiempo de respuesta fuera de horario, consultas perdidas y oportunidades sin responsable. El coordinador las cruzará con finanzas y competencia como hoy hace con la demo. La demo del hackathon **no depende de esto**: funciona igual con el ERP de demo.
