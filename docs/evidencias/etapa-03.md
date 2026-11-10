# Evidencia de etapa 3 — sobre cifrado

Fecha: 10 de noviembre de 2026, America/Bogota. Modalidad: implementación y pruebas reales en el equipo local, con datos ficticios. Fuentes: F3 pp. 1–3 y 5–7; C1 pp. 7, 9–13; C4 pp. 4–7 y 15 según MATRIZ_CLASES. Se releyó F3 completo y las páginas citadas de criptografía de C1 mediante extracción de texto local; no se modificaron materiales originales. No se generaron PDF, commits ni push.

## Condiciones

Dos servicios normales, Nginx y FastAPI, HTTP local 127.0.0.1:8080. SQLite y volumen `identidad` preexistentes; migración aditiva de `documentos`. Las cuentas/contraseñas/TOTP del portal principal no se inicializaron ni se utilizaron para el recorrido automatizado. No se provocaron alteraciones en su volumen. La privada RSA se crea solo al publicar el primer documento y persiste con los sobres.

La suite se ejecutó en imagen `el-sobre-de-las-ocho-tests:etapa3`, sin red, raíz de solo lectura y `/tmp` temporal. El navegador utilizó `sobre-identidad-qa`, 127.0.0.1:8081 y un volumen **datos_prueba** propio, temporal y eliminado al finalizar. El volumen permite comprobar un reinicio real; no se usa tmpfs para datos persistentes en este ensayo. Contraseñas y TOTP aleatorios de prueba, nunca los del portal principal. No se interceptaron respuestas exitosas de publicación, autorización o descarga. Solo el caso de error de transporte del botón aborta deliberadamente una solicitud.

## Comandos ejecutados y resultados

| Comprobación | Resultado observado |
|---|---|
| `docker compose up -d --build --wait --wait-timeout 120` | Reconstrucción correcta; dos servicios saludables |
| `docker build --target test -t el-sobre-de-las-ocho-tests:etapa3 .` | Imagen de pruebas construida con cryptography 50.0.2 |
| `docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa3 python -m pytest -q -p no:cacheprovider --tb=line` | **120 passed in 84.92s**; 73 casos anteriores y 47 nuevos |
| `python scripts/verificar_etapa1.py` | **27 comprobaciones aprobadas**: proxy/HTTP, salud, recursos, aislamiento, usuario, raíz y puertos |
| `docker compose exec -T nginx nginx -t` | Sintaxis y configuración correctas |
| `node scripts/verificar_identidad.cjs` | Recorrido completo aprobado, incluidas 2A/2B, cuatro comprobaciones del botón y publicación/entrega/alteraciones/restauración de etapa 3 |
| `python -m app.demo sobre preparar/estado/alterar-gcm/alterar-hash/restaurar/auditoria` | Cada subcomando ejecutado realmente en contenedor aislado con `/data` temporal: GCM/hash/restauración y ausencia del original en ciphertext comprobados; muestra publicada sin tocar el volumen principal |
| Regresión dirigida tras actualizar los textos de portada | **9 passed in 2.19s**, en la imagen final; son repetición de casos incluidos en la suite, no nueve casos adicionales |
| `node scripts/verificar_interfaz.cjs` tras reconstrucción final | Portada 1440/768/390/320, axe A/AA, teclado, salud real, errores/timeout controlados, movimiento reducido y alternativa sin JS aprobados; sin recursos externos ni excepciones JS |

## Criptografía, validación y autorización observadas

| Caso | Resultado real |
|---|---|
| TXT publicado por docente con MFA | POST multipart real por Nginx; 303 y confirmación; metadatos en panel |
| Subida anónima / estudiante / docente sin MFA | 401 / 403 / 401; sin archivo publicado |
| CSRF o origen incorrectos | 403 |
| Extensión ajena, UTF-8 inválido, controles binarios, vacío, ruta relativa o exceso de tamaño | Rechazo 400/413 según el límite; sin publicación nueva |
| Nombre Windows recibido por multipart | El parser lo normaliza a basename y se almacena únicamente `parcial.txt`; el validador directo rechaza rutas restantes |
| Almacén, secretos y original por URL directa | 404, sin contenido; Nginx no monta `/data` |
| AES-GCM y RSA-OAEP | AES de 32 bytes diferente por cifrado, nonce de 12 bytes; original no presente en ciphertext; recuperación idéntica; otra privada o AAD de otro recurso/versión rechazados |
| SHA de referencia | Vector conocido SHA-256 y comparación con original publicados comprobados |
| 07:59:59, estudiante asignado | Descarga 403 sin documento; no se llama a descifrado antes de horario |
| 08:00:00 inclusivo / 08:01 | 200; attachment/nosniff/no-store; bytes idénticos al original |
| Sin asignación después de apertura / documento ajeno / docente | 403 sin documento |
| Sesión ausente o vencida | 401 sin documento |
| Cifrado/tag alterados | InvalidTag en primitivas; caso A por CLI produce 409, sin attachment ni original, motivo `autenticacion_gcm_fallida` |
| Contenido distinto con cifrado válido | GCM correcto, SHA calculado distinto y referencia original intacta; 409 sin archivo, motivo `discrepancia_sha256` |
| Restauración | Vuelve al original cifrado aprobado; 200 con bytes originales, sin cambiar cuentas, secreto TOTP, sesión o reloj |
| Archivo/clave/hash/metadatos ausentes o inválidos | 409 sin documento; clave perdida no se regenera si hay documentos |
| Reemplazo y limpieza | Nueva versión; sobres antiguos no referenciados retirados; misma privada |
| Interrupción de escritura o cuota agotada | 503; versión anterior permanece recuperable |
| Falla de escritura de auditoría en entrega | 503 sin documento |
| Reinicio real de ambos servicios QA | Misma sesión y documento descargable, huella original conservada; prueba de factoría adicional sobre misma base también aprobada |
| Conservación 2A/2B | Todos los casos anteriores pasan; TOTP real aceptado con reloj de evaluación en 2035; mismos comandos de reloj/asignación |

Las primeras ejecuciones tuvieron **111 aprobadas y 1 fallida** en la expectativa de rechazo de un nombre Windows. Se confirmó que tanto el cliente como el parser multipart normalizan el nombre. Se ajustó el ensayo para enviar el encabezado explícito y comprobar que solo se conserva basename seguro, además del rechazo directo de rutas por el validador. No se eliminó el control de rutas ni se alteraron permisos para aprobar. La suite final incluye también cinco casos nuevos de escritura/cuota/identificadores hostiles.

La última revisión añadió tres casos: carga con Content-Type incorrecto/ausente y copia distinta que conserva UTF-8 válido con BOM/letra acentuada. Estos forman parte de los 120 casos finales. La suite completa precedió únicamente al ajuste textual de portada; se reconstruyeron las imágenes finales y se repitieron los nueve casos de portada después de cambiar su expectativa textual. No se alteró lógica tras el resultado completo.

## Interfaz y evidencias locales

Revisadas capturas de docente y estudiante en 1440 y 390 px: formulario real, nombre del documento, publicación con fecha española, reloj existente, descarga autorizada y rechazo de integridad. No hay desbordamiento ni infracciones automáticas axe WCAG A/AA en las vistas probadas; no se afirma certificación universal de accesibilidad. La comprobación del botón conserva 600 ms mínimos de indicación visual, una sola petición ante pulsaciones repetidas, confirmación sin hora real visible y error sin presentar estado anterior como recién verificado.

Artefactos locales no publicados: `.qa/identidad-resultados.txt`, `.qa/capturas/sobre-docente-{1440,390}.png`, `sobre-estudiante-{1440,390}.png`, `sobre-alterar-gcm-390.png`, `sobre-alterar-hash-390.png`. Sin campos de contraseña/código rellenados ni claves/cookies en las capturas. Se verificó que las credenciales/código de QA no aparezcan en los logs del recorrido. Los registros exportados seleccionan campos y omiten secretos/contenido.

## Alcance y límites

P1–P3 quedan verificados para esta aplicación local. P4–P10 y etapas 4–6 siguen pendientes. HTTP continúa sin TLS; el cifrado en reposo no protege el tránsito. Privada RSA sin contraseña en disco, protegida por permisos y volumen privado; administrador Docker/equipo fuera del modelo. No hay KMS, rotación de claves, bitácora inmutable ni antivirus. SHA-256 no sustituye una referencia confiable ni protege contra modificación simultánea por el administrador. TXT ficticio hasta 512 KiB; no PDF/DOCX. Restaurar una copia cifrada no recupera una privada perdida.

El portal principal queda operativo con sus identidades y referencia horaria existentes. Las pruebas no publican una muestra ni alteran documentos allí; el docente puede cargar su TXT desde el panel. Para una muestra local voluntaria, usar `app.demo sobre preparar`, que sustituye el documento del caso de ensayo: detalle y comandos en [CRIPTOGRAFIA_SOBRE.md](../CRIPTOGRAFIA_SOBRE.md).

Consulta final sin datos sensibles: dos cuentas existentes, cero documentos publicados en el portal principal y referencia fija `2026-11-09T08:00:00-05:00`. No se cambió esa referencia durante esta etapa. La demostración automatizada y sus alteraciones quedaron en el volumen QA eliminado.
