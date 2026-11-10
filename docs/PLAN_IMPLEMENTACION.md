# Plan de implementación

**Estado: etapas 1 y 2A implementadas; 2B y etapas posteriores pendientes.** Fuente principal: `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf` (F3), especialmente pp. 5–7. Se conservan nombres, orden y estimaciones de sus seis etapas. Evidencias: [etapa 1](evidencias/etapa-01.md) y [2A](evidencias/etapa-02a.md). P1 tiene cobertura parcial de identidad; P2–P10 pendientes.

El alcance actual incorpora 2A: identidad y control de acceso, sin ejecutar 2B. Las rutas iniciales son propuestas en ARQUITECTURA; README e IDENTIDAD_ACCESO recogen las existentes. Las fuentes docentes y cobertura están en MATRIZ_CLASES. El seguimiento de seis etapas permanece documental.

## Etapa 1 · Preparar — 3–4 h

Objetivo F3 p. 5: portal mínimo local que vuelve a abrir después de reiniciar servicios y expone solo la entrada prevista.

Decisiones ejecutadas: FastAPI/Uvicorn/Jinja2, HTTP inicial `127.0.0.1:8080`, dos servicios, Python sin puerto publicado, Nginx con entrada y red interna. Se crearon pruebas de contrato y verificadores de infraestructura/interfaz. La verificación y límites del cierre se detallan en la ficha de evidencia. Adaptaciones a las tareas originales: no se necesita `app/config.py` ni `.env.example` porque aún no hay parámetros secretos; no se inventa un secreto obligatorio. La guía se entrega en CMD según la petición actual. SQLite sigue siendo la persistencia prevista, sin base creada en esta etapa.

| Tarea pequeña | Entregable futuro | Aceptación / comprobación |
|---|---|---|
| 1.1 Inventariar versiones y recursos sin instalar aún lo que ya exista | Registro en `docs/GUIA_WINDOWS.md` | Windows, Docker Desktop/Compose, Git, Python, OpenSSL, puertos y espacio disponibles identificados. Herramientas ausentes anotadas; no presumir instalación. |
| 1.2 Confirmar framework, servidor, dependencias mínimas y puerto libre | `requirements.txt`, decisión en arquitectura | Python/SQLite/Nginx preservados, sin servidor extra ni framework frontend innecesario. Versiones fijadas al preparar entorno. |
| 1.3 Preparar estructura y configuración de secretos | `Dockerfile`, `app/config.py`, `.env.example` sin valores secretos | Configuración falla con mensaje claro si falta secreto obligatorio; Git no incluye secretos ni material académico privado nuevo. |
| 1.4 Levantar dos servicios y página de estado mínima | `compose.yaml`, `app/__init__.py`, `infra/nginx/default.conf` | Página responde por Nginx en `127.0.0.1`; Python sin puerto publicado. Reiniciar servicios y volver a consultar. |
| 1.5 Definir identidad visual y estructura de dos vistas | `app/templates/`, `app/static/styles.css` | Diseño de sobre coherente, tipografía y foco legibles, navegación por teclado y vista estrecha; contenido aún marcado como prototipo. |
| 1.6 Documentar ejecución y parada en PowerShell | `docs/GUIA_WINDOWS.md` | Comandos de la etapa reproducidos en el portátil; registrar resultado observado y recursos requeridos. |

Pruebas: comprobar configuración Compose, respuesta HTTP mínima a través del proxy, reinicio, puerto/host de escucha y ausencia de acceso directo a Python. Son comprobaciones de infraestructura; no equivalen a aprobar P1–P10. En esta etapa puede existir HTTP temporal **solo local** sin credenciales; el cierre final exige HTTPS en etapa 4. No declarar segura una pantalla de estado por su apariencia.

## Etapa 2 · Identificar — 5–7 h

Objetivo F3 p. 5: distinguir rechazos por sesión, rol y horario; pasar a aceptación a las 08:00.

### Subetapas de Identificar

**2A entregada:** dos cuentas SQLite inicializadas localmente, Argon2id con sal, login/logout, sesión previa/MFA/completa con rotación, CSRF, límites persistentes, TOTP real y anti-repetición, RBAC, paneles privados y auditoría de identidad. No se implementa recuperación de cuentas ni un panel administrativo de usuarios. Evidencia y límites en IDENTIDAD_ACCESO y ficha 2A.

**2B pendiente de autorización:** modelo de asignaciones, política ABAC de recurso y horario, reloj didáctico independiente de TOTP/sesiones, rechazos reproducibles por fecha/hora y sus pruebas. La etapa 2 completa no se declara cerrada. Cifrado, publicación/descarga real y laboratorios conservan sus etapas posteriores.

| Tarea pequeña | Entregable futuro | Aceptación / comprobación |
|---|---|---|
| 2.1 Crear dos cuentas ficticias y persistencia mínima | `app/db.py`, `app/auth.py` | Sal por cuenta y función de derivación; nunca contraseña en claro. Consultas parametrizadas. |
| 2.2 Crear sesiones separadas, cierre y expiración real | `app/auth.py`, `tests/test_auth.py` | Login/logout verificables; expiración produce 401; ninguna sesión hereda el rol de la otra. |
| 2.3 Exigir TOTP docente con secreto independiente | `app/auth.py`, `app/config.py` | Contraseña sin OTP no completa acceso docente; incorrecto/expirado denegado, correcto aceptado; no exponer secreto en UI/log. Definir ventana y evitar reutilización del mismo paso aceptado. |
| 2.4 Aplicar rol y asignación en servidor | `app/policy.py`, `tests/test_policy.py` | Publicación estudiante 403; parcial no asignado 403; URL directa usa las mismas reglas. |
| 2.5 Añadir reloj didáctico para apertura | `app/clock.py`, `scripts/demo.py` | Fecha y zona Bogotá; 07:59:59 rechaza y 08:00:00 permite; Windows, TOTP y sesión no se alteran. |
| 2.6 Escribir auditoría básica y presentar estados reales | `app/audit.py`, plantillas, `tests/test_audit.py` | Cada decisión registra actor/acción/motivo y tiempos; vista sin secretos, mensajes de error accesibles. |

Pruebas: P1 completo y regla horaria de P2 con texto ficticio controlado; P2 con sobre cifrado definitivo se repetirá en etapa 3. Añadir sesión expirada, OTP incorrecto, asignación errónea, fecha distinta y acceso por URL. Comparar reloj real/OTP antes y después de adelantar ensayo. No anunciar protección criptográfica todavía. Si se demuestra con datos de login antes de TLS, son únicamente cuentas desechables locales y se repetirá por HTTPS.

## Etapa 3 · Sellar — 5–6 h

Objetivo F3 p. 5: recuperar original idéntico, bloquear copia modificada y volver a funcionar al restaurar.

| Tarea pequeña | Entregable futuro | Aceptación / comprobación |
|---|---|---|
| 3.1 Preparar RSA local y formato versionado del sobre | `app/crypto.py`, guía de claves | Clave privada fuera de Git; RSA-OAEP envuelve clave AES; no cifrar documento con RSA. Parámetros documentados. |
| 3.2 Publicar texto con SHA-256 y AES-GCM | `app/storage.py`, `app/crypto.py` | Bytes originales recuperables exactamente, nonce/clave no reutilizados, almacén no público. |
| 3.3 Proteger referencia y persistir de forma coherente | `app/db.py`, `app/storage.py` | La cuenta web no reescribe la referencia; fallo entre archivo y metadatos deja denegación, no documento incoherente. |
| 3.4 Verificar todo antes de enviar documento | `app/policy.py`, `tests/test_crypto.py` | Hash/tag incorrectos impiden entrega completa; no emisión parcial; falta de archivo/referencia bloquea y audita. |
| 3.5 Preparar y seleccionar copia con una letra distinta | `scripts/demo.py` | Cifrado válido y huella de referencia intacta; motivo por hash distinguible de error GCM. |
| 3.6 Restaurar y revisar flujo visual docente/estudiante | Plantillas y `tests/test_demo.py` | Publicación con validaciones; descarga sin caché, estados obtenidos del servidor; restauración no elimina evidencia. |

Pruebas: P2/P3 completos; comparar bytes además de hashes. Casos adicionales de tag corrupto, clave equivocada, archivo/referencia ausente y fallo de persistencia. Repetir por URL directa y confirmar cuerpo sin bytes del parcial en errores. Elegir y documentar códigos adicionales no fijados por F3 antes de cerrar etapa. Guardar resultados sin claves ni texto privado.

## Etapa 4 · Proteger la red — 5–7 h

Objetivo F3 p. 5: distinguir HTTP de HTTPS y explicar acceso permitido/denegado en red.

| Tarea pequeña | Entregable futuro | Aceptación / comprobación |
|---|---|---|
| 4.1 Preparar certificado local y HTTPS Nginx | `infra/nginx/default.conf`, `docs/GUIA_WINDOWS.md` | SAN y confianza para URL elegida, cookie Secure; certificado y claves no publicados. |
| 4.2 Activar cabeceras y retirar versión del banner | Configuración Nginx | SAMEORIGIN/nosniff en éxitos y errores; iframe de origen distinto bloqueado. |
| 4.3 Preparar ensayo HTTP con marca ficticia | `labs/http/`, `labs/compose.labs.yaml` | Solo loopback o red aislada; no sirve repositorio, secretos ni archivo de trabajo real. |
| 4.4 Capturar HTTP y HTTPS propios | Ficha P4 y capturas privadas | Marca visible solo en HTTP sin claves TLS; identificar IP, puerto e inicio TCP; registrar interfaz Windows usada. |
| 4.5 Construir maqueta WPA2/VLAN/RADIUS | `labs/network/topologia.pkt` | VLAN 10/20/30, puertos acceso/troncal y política permitida/denegada; AAA válido/inválido. Soporte y comandos comprobados en Packet Tracer. |
| 4.6 Crear modelo NAC con zonas, herencia y estado | `labs/nac/model.py`, `tests/test_nac.py` | Herencia correcta, regla local no visible fuera, default deny y equipo no verificado denegado; etiquetar simulación. |

Pruebas: P4, P5 y P6; repetir P1–P3 por HTTPS. Separar evidencia Packet Tracer de modelo NAC y portal. F3 no exige VPN desplegada ni firewall de producción; dibujar VPN y explicar diferencias stateful/stateless. No afirmar que las VLAN o NAC del simulador protegen los contenedores reales.

## Etapa 5 · Auditar y corregir — 7–9 h

Objetivo F3 p. 5: corregir SQL, conservar informes antes/después y medir carga con cuota.

| Tarea pequeña | Entregable futuro | Aceptación / comprobación |
|---|---|---|
| 5.1 Aislar copia SQL y activar solo bajo perfil explícito | `labs/sql/`, `labs/compose.labs.yaml` | Sin cuentas, claves, red de aplicación ni volúmenes del portal; apagada por defecto; datos ficticios. |
| 5.2 Reconocer objetivo propio con Nmap/NSE y validar manualmente | Informe P7 | Alcance y puerto explícitos; guardar hallazgos y ausencias; no deducir SQLi de un puerto. |
| 5.3 Corregir consulta y repetir el mismo caso | `labs/sql/`, `tests/test_labs.py` | Acceso indebido antes, rechazado después; credencial válida funciona en corregida. Portal usa siempre parametrización. |
| 5.4 Automatizar controles locales y condición de promoción | `scripts/security_checks.ps1` | Pruebas, Bandit y Trivy devuelven códigos que bloquean el avance al fallar; guardar commit y configuración. No requiere GitHub Actions. |
| 5.5 Elegir CVE con parche y comparar | Informes P8, versiones/digests | Misma base Trivy y configuración; HIGH/CRITICAL bloquea; explicar CVE tras actualización y aprobar todos los controles antes de promover. |
| 5.6 Preparar dos clientes y carga base | Perfil de carga y ficha P9 | Dos IP distintas verificadas por Nginx; sesiones válidas, original y apertura constantes. Máximo 100 peticiones con concurrencia 5. |
| 5.7 Aplicar cuota y medir de nuevo | `infra/nginx/default.conf`, logs | 5 r/s/IP, burst 5, 429 explícito; medir latencia legítima, CPU, códigos y porcentaje real; alumno autorizado obtiene 200. |
| 5.8 Integrar trazabilidad de proxy y aplicación | Exportación/ficha saneada | 429 conservado en Nginx aunque no exista evento Python; no filtrar cookies o secretos. |

Pruebas: P7, P8 y P9. La base Trivy debe estar descargada antes del ensayo sin Internet. No elegir ahora un CVE imaginario ni comprometer una imagen histórica sin comprobarla. Si actualizar un CVE deja otros fallos altos/críticos, aún no se promueve. No se exige porcentaje de rechazo fijo ni caída del servicio.

## Etapa 6 · Repetir y sustentar — 5–7 h

Objetivo F3 p. 5: demo dos veces desde 07:59, una ficha por clase y restauración sin ayuda.

| Tarea pequeña | Entregable futuro | Aceptación / comprobación |
|---|---|---|
| 6.1 Preparar simulación ARP y ficha de incidente | `labs/network/arp.md`, ficha saneada | Tablas normal/alterada y desvío explicado; no se modifica ARP de Windows. Prevención/detección/corrección identificadas. |
| 6.2 Ejecutar P1–P10 y completar fichas | `docs/evidencias/`, matriz actualizada | Resultado esperado y observado, fuentes/páginas y artefactos por prueba; conservar fallos y correcciones. |
| 6.3 Restaurar copia, reloj y datos de ensayo | `scripts/demo.py`, `tests/test_demo.py` | P10: mismas condiciones repiten P2/P3; conserva tiempos reales, claves necesarias y auditoría. No borrar volúmenes para ocultar fallos. |
| 6.4 Ensayar dos recorridos individuales | Guion y fichas de dos ejecuciones | 403 → 200 original → 409 alterado → 200 restaurado, controlado por una persona. |
| 6.5 Revisar accesibilidad, errores y arranque Windows | Guía y revisión manual | Teclado, foco, etiquetas, móvil/escritorio, contraste y mensajes coherentes; repetir desde servicios reiniciados. |
| 6.6 Revisar trazabilidad, privacidad y dependencias offline | Matriz y guía final | Cada clase tiene modalidad explícita; sin secretos/material privado nuevo en cambios; herramientas e imágenes preparadas. |

Guion F3 p. 7: minuto 0–1 problema y cuentas; 1–4 rechazo horario, original y copia alterada; 4–6 tráfico y corrección; 6–8 carga, límites de maqueta y restauración. Informe extenso y diapositivas quedan para la fase académica 5; no confundirla con la etapa 5 de esta tabla.

## Verificación y cierre

Pruebas unitarias/integración previstas para reglas críticas: identidad/MFA, política horaria y asignación, cifrado e integridad antes de salida, auditoría, NAC y restauración. Usar reloj de apertura inyectable y fixtures ficticios, no esperas reales hasta las 08:00. Pruebas HTTP a través de Nginx para TLS, cabeceras y cuota; revisión manual para diseño, Packet Tracer y captura de tráfico. No escribir pruebas que solo comprueben que un archivo existe o reflejen sin criterio la implementación.

Una etapa solo se cierra con resultados observados y evidencia. La matriz distingue pendiente, implementado sin verificar, verificado y fallido. Etapas 1 y 2A cuentan con sus fichas; la siguiente acción requiere autorización de **2B**, sin marcar la etapa 2 completa como terminada.
