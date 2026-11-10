# Etapa 1 — portal y entorno local

**Modalidad:** implementación y comprobación reales de infraestructura/portada. **Fecha local:** 9 de noviembre de 2026, Bogotá. **Estado:** etapa 1 verificada dentro del alcance descrito. Etapas 2–6 y pruebas P1–P10 pendientes. No se hicieron commits: la ejecución corresponde al árbol de trabajo entregado; no se inventa un SHA de commit.

## Fuentes y condiciones iniciales

Fase 3: `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf`, pp. 1–2 y 5. Clases relacionadas: C2 pp. 4, 9–10, 16–18; C5 pp. 4, 8–14; C6 pp. 5–8; C7 pp. 4, 6–7, 13–14. Nombres completos en [MATRIZ_CLASES.md](../MATRIZ_CLASES.md). La petición de etapa 1 fija FastAPI y HTTP local en 8080 y permite completar y corregir autónomamente esta etapa.

Equipo Windows 11 Pro con Docker Desktop activo, motor Linux; sin otros contenedores/imágenes al inicio y puerto 8080 libre. Versiones y recursos observados: [GUIA_WINDOWS.md](../GUIA_WINDOWS.md). Datos: ningún usuario/examen real; no se cargan documentos ni credenciales. No se leen de nuevo los PDF para construir esta etapa.

## Procedimiento y resultados observados

Comandos completos reproducibles en [README.md](../../README.md).

| Comprobación ejecutada | Esperado | Resultado observado |
|---|---|---|
| `docker compose config --quiet` | Compose válido | Salida 0 |
| `docker compose up -d --build --wait --wait-timeout 120` | Construcción e inicio de dos servicios | Imágenes construidas/descargadas; `app` y `nginx` saludables tras corregir red de entrada |
| `docker compose ps` e inspección de contenedores | Únicamente Nginx publica entrada local | FastAPI sin `PortBindings`; Nginx `127.0.0.1:8080:8080`; dos servicios |
| `python scripts/verificar_etapa1.py` | Políticas de despliegue y respuestas válidas | 27 comprobaciones correctas: salud, usuarios no root, raíz solo lectura, redes, publicación local, recursos, cabeceras y rutas no publicadas |
| `GET /health` desde Windows por Nginx | 200 y contrato estable | `{"status":"ok","servicio":"el-sobre-de-las-ocho","etapa":1}` |
| `GET /` y CSS/JS/favicon | 200 y tipos de contenido adecuados | Los cuatro recursos respondieron correctamente |
| `GET /.env`, `/docs/RESUMEN_PROYECTO.md`, `/docente`, `/descargar` | No publicar secretos/documentación ni funciones futuras | 404 en todos los casos; no se crean archivos secretos para probar |
| `docker compose exec nginx nginx -t` | Sintaxis válida | Configuración correcta; salida 0 |
| `docker build --target test ...` y ejecución de imagen test sin red | pytest pasa, sin añadir servicios al portal | 9 pruebas aprobadas; ejecución con `--network none --read-only --tmpfs /tmp` |
| `docker compose restart` seguido de `up --wait` | Recuperar portal después del reinicio | Ambos servicios volvieron a `healthy`; verificador completo volvió a aprobar |
| Recreación de aplicación al reconstruir | Nginx resuelve la aplicación actual | Portal/estáticos/salud respondieron después de recrear Python; resolución Docker dinámica activa |
| Revisión Chrome a 1440, 768, 390 y 320 px | Página accesible y sin desbordamiento horizontal | 200 y ancho correcto en las cuatro vistas; capturas inspeccionadas de escritorio y móvil |
| Navegación de teclado/anclas | Saltar a contenido y navegar | Primer Tab enfoca salto; Enter llega a contenido; enlace principal lleva a áreas |
| Botón salud real | No fingir estado conectado | Consulta real correcta y mensaje HTTP 200 |
| Fallo 503, JSON incompleto y espera mayor a 5 s, interceptados en navegador | Error comprensible; botón utilizable al terminar | Tres escenarios mostraron error y recuperaron el control; no se cambió ni detuvo backend |
| Preferencia de movimiento reducido | Desactivar animación | Animación del sobre desactivada mediante media query |
| Navegador sin JavaScript | Contenido y alternativa de salud | Portada visible; enlace `noscript` abrió JSON de salud |
| Excepciones JS y peticiones externas | Ninguna | No detectadas en recorrido normal; recursos propios únicamente |
| axe WCAG 2/2.1 A/AA en cuatro anchos | Sin infracciones automáticas | Cero infracciones detectadas después de corregir contraste/etiquetas; no equivale a certificación de accesibilidad |

Herramientas de navegador: Chrome instalado en Windows, Playwright 1.65.0, `@axe-core/playwright` 4.14.0. Se instalaron temporalmente en `.qa/`, excluida de Git y de Docker. Prettier 3.9.10 se usó solo para dar formato legible a CSS/JS; no es dependencia de la aplicación. Resultados y capturas locales: `.qa/interfaz-resultados.txt` y `.qa/capturas/portal-{1440,768,390,320}.png`. No se publican artefactos crudos por defecto.

## Incidencias encontradas y corregidas

1. **Salud interna sin acceso Windows:** la configuración inicial conectaba Nginx solo a una red Docker `internal`. Los healthchecks pasaban, pero la conexión desde Windows era rechazada y el puerto no se publicaba como se esperaba. Corrección: Nginx en red `entrada` y red interna `portal`, FastAPI solo en `portal`. Inspección y peticiones desde Windows confirmaron publicación únicamente en loopback.
2. **Cliente de pruebas desactualizado:** la primera ejecución de pytest falló al recolectar por deprecación de httpx en Starlette 1.10.0, al tratar advertencias como errores. Se fijó httpx2 2.16.0 para TestClient y se regeneró `requirements-dev.txt`. La ejecución posterior aprobó las nueve pruebas sin ignorar advertencias.
3. **Accesibilidad:** el análisis automático señaló etiqueta en elemento sin rol adecuado, nombre accesible de marca incoherente y contraste insuficiente en estados pendientes. Se corrigieron rol/etiqueta y colores. El verificador de navegador también se ajustó para usar contexto explícito de Playwright y medir al terminar la animación; no se desactivaron reglas de contraste para ocultar hallazgos.

## Límites de verificación

La salud demuestra que el proceso responde a través del proxy. Las cabeceras son medidas básicas reales, pero falta el laboratorio de iframe para P6. No se ha hecho comparación Wireshark/TLS P4, NAC/VLAN/RADIUS P5, análisis Bandit/Trivy/CVE P8, carga P9 ni ninguno de los controles de entrega P1–P3. Los casos de error de interfaz son interceptaciones locales del verificador, no ataques o simulaciones de seguridad incorporados al portal.

La revisión automática y de capturas no sustituye pruebas con lector de pantalla, todas las versiones de navegador o una auditoría de seguridad. HTTP no cifra el tráfico; aquí no se envían contraseñas ni exámenes. El diseño del sobre no certifica controles futuros.

## Revisión de presentación de etapa 1

Fecha de referencia local: 9 de noviembre de 2026. Alcance: lenguaje, organización y legibilidad; sin cambios de arquitectura, dependencias, rutas de aplicación ni funcionalidades de etapas posteriores.

Se sustituyeron lemas pedagógicos por lenguaje de gestión de evaluaciones y disponibilidad del servicio. Se conservaron el titular «Cada examen, a su debido tiempo», la ilustración, los colores y los componentes reutilizables. La sección de seis etapas y su indicador lateral se retiraron del producto; el plan permanece en Markdown. La navegación contiene inicio, áreas y estado del servicio. Las tres áreas previstas son portal docente, portal estudiante y laboratorio de seguridad administrativo, todos pendientes. El laboratorio no tiene enlaces, rutas ni controles operativos. Las tarjetas no presentan indicadores de acción; las notas funcionales y el estado tienen mayor tamaño de texto.

| Verificación repetida | Resultado observado |
|---|---|
| Validación Compose, actualización de imagen y espera de salud | Salida 0; exactamente dos servicios saludables; misma configuración de redes y publicación |
| Nueve pruebas existentes, con aserciones de portada actualizadas | **9 passed in 0.53s**; se comprueban además ausencia del recorrido y 404 en `/laboratorio`, `/admin`, `/admin/laboratorio` |
| `python scripts/verificar_etapa1.py` | Las 27 comprobaciones vuelven a aprobar: red interna, sin publicación FastAPI, Nginx solo en `127.0.0.1:8080`, respuestas/cabeceras/recursos correctos |
| `docker compose exec nginx nginx -t` | Configuración válida, salida 0 |
| Chrome a 1440, 768, 390 y 320 px | HTTP 200, sin desbordamiento horizontal; revisión visual de capturas de escritorio y móvil |
| axe WCAG 2/2.1 A/AA en los cuatro tamaños | Cero infracciones automáticas detectadas; conserva los límites de la revisión automática |
| Teclado, anclas, movimiento reducido y modo sin JavaScript | Comprobaciones aprobadas |
| Salud real y errores/timeout interceptados en navegador | Consulta real aprobada; error HTTP, JSON incompleto y espera agotada recuperan el botón y no muestran éxito falso |
| Recursos externos y excepciones JavaScript | Ninguno detectado en el recorrido |

Las pruebas y verificadores ya existentes se reutilizaron sin instalar nuevas dependencias. Las capturas y el resultado de navegador actualizados permanecen en `.qa/`, excluida de Git. El contrato de `/health` no cambia; la interfaz traduce el resultado correcto como «El portal está disponible».

La revisión contra los requisitos documentados de F3 no identifica cambios de alcance: Python/FastAPI, Nginx, dos servicios Compose y acceso local se conservan; SQLite, AES-GCM/RSA-OAEP, SHA-256, roles/TOTP, reloj didáctico, auditoría, TLS y laboratorios siguen en sus etapas previstas. No se marca P1–P10 como ejecutado ni se afirma autorización administrativa implementada. Los originales PDF y el historial de Git se conservan; sin commits ni push.
