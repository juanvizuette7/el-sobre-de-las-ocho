# Evidencia de etapa 5 — defensas y verificaciones

Fecha: 10 de noviembre de 2026. Se trabajó en bases temporales y en la imagen local; no se modificaron cuentas, TOTP, documentos, reloj ni volumen principal. No se tocaron los PDF originales. Sin commits ni push; etapa 6 pendiente.

| Comprobación | Resultado observado |
|---|---|
| SQL Injection y consulta parametrizada | La entrada ficticia `' OR '1'='1' --` devolvió dos filas en la consulta concatenada y cero en la parametrizada. SQLite `:memory:`; al salir, los datos desaparecen. |
| Consultas del portal | Revisión de `app/`: los valores externos se envían como parámetros; no se encontró inyección en las rutas de producción. |
| Limitación y auditoría | Cinco fallos de prueba, sexto bloqueado con HTTP 429; evento `limite_intentos`; tras adelantar el reloj de prueba 301 s se recuperó el resultado normal. Base y contraseña aleatorias efímeras. |
| Bandit 1.9.4 | High/Critical: 0. Un Medium B608 intencional en la concatenación vulnerable didáctica. B310 suprimidos solo en tres verificadores HTTPS locales de origen/rutas cerrados. Comando devuelve código 1 por el B608 esperado. |
| Trivy 0.76.2, Python en Debian 12 previo | Dos registros críticos: `CVE-2025-7458` (SQLite) y `CVE-2023-45853` (zlib, `will_not_fix`). |
| Trivy 0.76.2, imagen runtime Python/Debian 13.7 antes del ajuste | 49 registros High, todos paquetes Debian: 47 sin versión corregida y 2 de zlib con corrección disponible. 0 críticos. `requirements.txt`: 0 vulnerabilidades. |
| Corrección y escaneo dirigido | Se fijó `zlib1g=1:1.3.dfsg+really1.3.1-1+deb13u1`; los 2 CVE de zlib ya no aparecen. La imagen actual conserva 47 High, todos sin versión corregida en el informe. |
| Trivy, Nginx Alpine 3.24.4 | 0 hallazgos High/Critical. |
| Trivy filesystem | 1 Low DS-0026 en Dockerfile aislado. Los healthchecks están en Compose y fueron verificados en ambos servicios. |
| Secretos preparados para Git | `git ls-files` no muestra claves, certificados privados, SQLite, tokens ni capturas. `.gitignore` cubre `certs/`, `data/` y `.qa/`. |
| Regresión | `pytest`: 129 passed. TLS/red: 22 passed. Infraestructura: 27 passed. Navegador: estudiante/docente/TOTP, RBAC/ABAC, límites de las 08:00, publicación, descarga byte a byte, detección GCM/SHA y restauración correctos. |
| Interfaz | 1440, 768, 390 y 320 px: sin desbordamiento, axe A/AA sin infracciones; errores/timeout, teclado y salud verificados. |

Los dos cambios puntuales fueron actualizar el digest fijado de `python:3.12-slim-bookworm` a `python:3.12-slim-trixie` para eliminar los críticos del escaneo anterior e instalar la versión corregida disponible de zlib. No se cambiaron dependencias Python ni lógica de autorización. De los 47 High restantes, las tres alertas de SQLite tienen mayor relevancia por el uso real del motor, pero Trivy no indica versión corregida. El resto afecta paquetes de la imagen base, sin correcciones listadas; queda riesgo residual pendiente de nuevas versiones del proveedor.

## Revisión de reducción de hallazgos (10 de noviembre de 2026)

| Imagen | Resultado de comparación | Decisión |
|---|---|---|
| `python:3.12-slim-trixie` oficial actual | Resuelve al mismo digest fijado en Dockerfile; no hay imagen más reciente en esa etiqueta. | Mantener. |
| `python:3.12-alpine3.23` | Trivy: 0 High/Critical; Python reporta SQLite 3.53.4. | Rechazada: SQLite es menor que 3.54.0 y el cambio glibc→musl requiere validación adicional. |
| `python:3.12-alpine3.24` | Trivy: 0 High/Critical; `apk policy` y Python confirman SQLite 3.53.4. | Rechazada: el cero del escáner no descarta las tres CVE de SQLite; no se construyó la aplicación sobre esta base. |
| Debian Sid | El tracker Debian lista SQLite 3.54.1 corregida; Trixie y Forky siguen vulnerables. No se encontró el tag oficial `python:3.12-slim-sid`. | Rechazada por ser distribución inestable. |

El [tracker oficial Debian de SQLite](https://security-tracker.debian.org/tracker/source-package/sqlite3) clasifica como vulnerables en Trixie las versiones de SQLite del portal. No se reemplazó ni reconstruyó la aplicación. El contenedor actual siguió saludable y `https://127.0.0.1:8443/health` respondió `200` con la CA existente. Las 47 alertas High del escaneo actual permanecen: 3 son de SQLite sin parche en la distribución estable y las otras 44 tampoco tienen versión corregida indicada por Trivy. No se ejecutó la suite completa porque ninguna candidata superó el criterio de seguridad previo a la prueba funcional; no hubo cambios funcionales.
