# Arquitectura del proyecto

## Estado vigente de etapa 3

Etapas 1, 2A, 2B y 3 implementadas. El flujo vigente se detalla en [CRIPTOGRAFIA_SOBRE.md](CRIPTOGRAFIA_SOBRE.md), con resultados en [evidencia 3](evidencias/etapa-03.md). Las secciones de diseño inicial más abajo conservan propuestas históricas; para cifrado y entrega prevalece esta especificación implementada.

Se añade `documentos` a la SQLite existente, sin borrar identidades, sesiones, reloj ni eventos. El mismo volumen privado `identidad` conserva `/data/sobres/*.gcm` y `/data/secrets/sobre-rsa.pem`, además de SQLite/TOTP. No se añade servicio o montaje en Nginx. `crypto.py` realiza AES-256-GCM/RSA-3072-OAEP-SHA256/SHA-256; `storage.py` administra versiones, escrituras atómicas, originales y copias de ensayo; `documents.py` aplica la política existente antes de verificar/entregar.

POST y GET `/evaluaciones/{id}/documento` implementan publicación docente con MFA/CSRF/origen y descarga estudiantil con sesión/asignación/apertura e integridad. Solo TXT UTF-8 hasta 512 KiB. El GET construye una respuesta attachment después de autenticar GCM, comparar SHA y registrar la entrega. La disponibilidad y el panel integran esos resultados; el reloj grande y la confirmación sin hora real visible se conservan. La bitácora docente distingue hora real y referencia del recurso.

Las acciones locales `app.demo sobre` preparan una muestra, inspeccionan huellas, activan cifrado dañado o texto distinto válidamente cifrado y restauran el original. No se exponen por HTTP. Los comandos de 2B conservan su comportamiento. La privada persiste; su pérdida bloquea y no causa regeneración sobre documentos existentes. La migración no reinicializa TOTP.

La red sigue usando HTTP local. TLS, Wireshark, Packet Tracer y NAC pertenecen a etapa 4, pendiente. P1–P3 tienen verificación de aplicación; no se extiende al resto de prácticas.

## Contexto histórico y diseño de etapas anteriores

**Estado: etapas 1, 2A y 2B implementadas; protección/entrega de exámenes pendiente.** F3 = `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf`, páginas físicas. Requisitos y respuestas HTTP: [RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md). Fuentes docentes: [MATRIZ_CLASES.md](MATRIZ_CLASES.md). Resultados: [etapa 1](evidencias/etapa-01.md) y [etapa 2A](evidencias/etapa-02a.md).

## Disponibilidad implementada en 2B

La especificación vigente está en [AUTORIZACION_HORARIO.md](AUTORIZACION_HORARIO.md). Evaluaciones, asignaciones y reloj se incorporan a la misma SQLite mediante migración aditiva; no se cambian cuentas, sesiones, secretos o servicios de 2A.

Los módulos app/clock.py y app/demo.py proporcionan reloj fijo persistente o normal y controles exclusivamente por CLI. El arranque no sustituye un reloj perdido por tiempo normal si hay evaluaciones; deniega hasta una configuración local explícita.

app/policy.py separa RBAC de paneles y decidir_disponibilidad, reutilizada por consultar_disponibilidad: sesión vigente, rol estudiante, asignación y apertura inclusiva. app/evaluations.py expone GET /evaluaciones/{id}/disponibilidad, con 401/403/200 y 503 ante configuración inválida. No entrega archivos. Los paneles y su JavaScript presentan la decisión recibida; no comparan fechas del navegador.

La auditoría conserva instante real y referencia didáctica ISO en columnas separadas, junto a evaluación, cuenta, acción, resultado y motivo. TOTP, límites y caducidad continúan usando tiempo real. Resultados en [evidencia 2B](evidencias/etapa-02b.md).

## Identidad implementada en 2A

La especificación operativa y de seguridad vigente está en [IDENTIDAD_ACCESO.md](IDENTIDAD_ACCESO.md): SQLite en volumen privado `identidad`, Argon2id con sal, sesiones de servidor y rotación, desafío TOTP, RBAC, CSRF y auditoría. `app/config.py`, `db.py`, `security.py`, `sessions.py`, `auth.py`, `policy.py`, `audit.py` y `manage.py` ya existen. No se incorpora otro servicio Compose ni se publica Python. Solo `/data` añade almacenamiento escribible persistente a la aplicación; Nginx no lo monta. 2B integra ABAC de asignación y apertura de metadatos sobre esta base.

Las reglas de cifrado y descarga siguen siendo diseño futuro; la disponibilidad horaria ya está implementada. La contraseña usa Argon2id en lugar de la propuesta inicial scrypt; ambos cubren derivación y sal, y la implementación concreta está probada. Tiempo de identidad: reloj real, independiente del reloj didáctico de evaluaciones. El secreto TOTP se conserva como archivo privado 0600, no cifrado en reposo; la protección no cubre al administrador del portátil/Docker.

## Implementación actual de etapa 1

La implementación utiliza FastAPI + Uvicorn (ASGI), Jinja2 y `http://127.0.0.1:8080`, conforme a la especificación de etapa 1. Los requisitos centrales de F3 se mantienen. HTTPS se reserva para la etapa 4; el diagrama y las reglas del examen de abajo describen el **objetivo futuro**, todavía pendiente de implementación.

La interfaz conserva el producto y su identidad visual, añade acceso y paneles privados, y mantiene el laboratorio administrativo sin rutas ni controles. El seguimiento de construcción permanece fuera de las pantallas.

Rutas públicas conservadas: `GET /`, `GET /health`, `/static`. Nuevas rutas de identidad: GET/POST `/acceso`, GET/POST `/acceso/totp`, POST `/salir`; paneles GET `/docente` y `/estudiante`, protegidos en servidor. Documentación interactiva API desactivada. No hay rutas web para publicar, modificar asignaciones/reloj, descargar o administrar el laboratorio. La consulta de disponibilidad sí está implementada. El campo `etapa: 1` de salud se conserva como contrato heredado de infraestructura; no expresa cobertura funcional.

```text
Windows/navegador → 127.0.0.1:8080 → Nginx:8080 → app:8000 → FastAPI/Uvicorn
                                      │              │
                                 red entrada    red interna portal
                                 + red portal   (solo esta red)
```

Nginx requiere una red de entrada para publicar correctamente el puerto en Docker Desktop. La primera prueba con ambos contenedores solo en red interna dio conexión rechazada desde Windows pese a healthchecks correctos; se corrigió sin publicar Python. El DNS interno de Docker resuelve `app`; Nginx renueva esa resolución para recuperarse si cambia la IP del contenedor al recrearlo.

Ambos contenedores ejecutan sin root, con capacidades retiradas, `no-new-privileges`, raíz de solo lectura y `/tmp` temporal. Límites: Python 256 MiB/1 CPU, Nginx 64 MiB/0,5 CPU. No son garantías contra todos los ataques. Cabeceras básicas ya activas: `SAMEORIGIN`, `nosniff`, versión oculta, Referrer-Policy y CSP del mismo origen. Esto anticipa buenas prácticas, sin dar por realizado P6 (falta el taller de iframe) ni el bastionado completo. No hay cuotas ni TLS todavía.

Dependencias directas y transitivas fijadas en `requirements.txt`; pytest y httpx2 están solo en el destino `test` del Dockerfile. Python/Nginx se fijan por digest. `.dockerignore` permite solo código, pruebas y requisitos: PDF, Git y secretos quedan fuera del contexto. No se monta Docker socket ni la carpeta del proyecto en la aplicación. Véase [README](../README.md) para comandos CMD y mapa de archivos existentes.

## Componentes y comunicación

```mermaid
flowchart LR
    B[Windows: navegador docente y estudiante] -->|HTTPS en 127.0.0.1| N[Nginx]
    N -->|HTTP en red privada Docker| A[Aplicación Python]
    A --> D[(SQLite: cuentas, metadatos, eventos)]
    A --> V[Volumen privado: sobres cifrados]
    K[Secretos locales fuera de Git] --> A
    C[Terminal: utilidad local de ensayo] -->|Control interno sin ruta web| A
    N --> L[Logs de Nginx]
    PT[Packet Tracer: VLAN, WiFi, RADIUS]
    NAC[Python: modelo NAC separado]
    LAB[Perfil de laboratorio aislado: SQL y clientes de prueba]
```

La aplicación normal tiene **dos servicios Compose**, Nginx y Python; SQLite es una biblioteca dentro de Python, no otro servidor (F3 p. 2). Nginx es la única entrada publicada en `127.0.0.1`; propuesta de URL final: `https://127.0.0.1:8443`. Puerto definitivo sujeto a comprobar disponibilidad. No publicar el puerto Python ni montar su almacén en Nginx. Una red privada une proxy y aplicación. La conectividad de contenedores no implementa las VLAN de Packet Tracer.

| Pieza | Tecnología y responsabilidad | Decisión / fuente |
|---|---|---|
| Interfaz | HTML generado en servidor, CSS y JavaScript mínimo. Dos vistas según rol y bitácora docente. | Propuesta de sencillez; vistas en F3 p. 1. |
| Aplicación | Python con FastAPI, Jinja2 y Uvicorn ASGI; sin debug/recarga automática. | Especificación de etapa 1; implementada en `app/main.py`. |
| Proxy | Nginx, HTTPS, cabeceras y cuotas. | F3 pp. 2–3; TLS/cabeceras en etapa 4 y cuota en 5. |
| Persistencia | SQLite, archivo local en volumen; consultas parametrizadas y transacciones. | SQLite en F3 pp. 2–3; detalles propuestos. |
| Criptografía | Biblioteca `cryptography` propuesta; AES-GCM, RSA-OAEP y SHA-256. | Variantes exigidas por petición y previstas por F3 p. 3. No criptografía artesanal. |
| Contraseña | Argon2id con sal aleatoria y parámetros embebidos; implementación 2A. | F3 p. 3 exige derivación y sal, sin imponer algoritmo. |
| MFA | TOTP local; secreto distinto de contraseñas, clave AES y clave RSA. | F3 p. 3. Autenticador local separado de la pantalla de acceso. |
| Ensayo | Utilidad de terminal ejecutada dentro del servicio, sin endpoint administrativo público. | Control local en F3 pp. 1–3. |
| Herramientas | Git, OpenSSL, Wireshark, Packet Tracer, Bandit, Trivy, Nmap/NSE y ApacheBench. | F3 pp. 2–4. No deben ser servicios permanentes del portal. |

Las versiones de la etapa 1 están registradas en [GUIA_WINDOWS.md](GUIA_WINDOWS.md) y las imágenes fijadas por digest. Se consultaron documentación oficial y metadatos de paquetes/imágenes para construir esta etapa; los PDF no se reprocesaron. Las bibliotecas criptográficas y herramientas futuras se elegirán al implementarlas. La demostración final debe funcionar sin Internet una vez preparadas imágenes, herramientas y base Trivy.

## Fronteras de confianza

El navegador y todos los datos enviados por él son no confiables. Ni botones ocultos ni una hora enviada por JavaScript autorizan la descarga. Python vuelve a comprobar identidad, rol, asignación y hora ante cada URL directa (F3 pp. 1, 3).

La sesión docente solo se considera autenticada después de contraseña y TOTP correctos. Propuesta: sesión de servidor identificada por cookie opaca; cookie `HttpOnly`, `SameSite=Lax`, `Secure` en HTTPS, expiración real, renovación al autenticar y anulación al salir. Proteger formularios de publicación con CSRF, validar tamaño/tipo del texto y usar identificadores internos para rutas de archivos. La captura no debe incluir cookies reutilizables. Son medidas propuestas para concretar seguridad y validaciones solicitadas.

Las cuentas web nunca reciben claves, rutas del almacén ni capacidad de actualizar directamente la referencia. Solo el flujo de publicación docente establece una nueva referencia para una nueva versión del parcial. La utilidad de copia alterada conserva la referencia aprobada. El propietario del portátil y un administrador del contenedor quedan fuera de la protección frente a modificación del almacenamiento: SHA-256 no impide que alguien con esos privilegios cambie archivo **y** referencia. No se afirma inviolabilidad ni auditoría inmutable.

## Ciclo del sobre

1. **Publicar:** autenticar docente con TOTP; validar texto, asignación y fecha; calcular SHA-256 sobre bytes exactos. No normalizar saltos de línea durante recuperación.
2. Generar clave AES nueva por publicación y nonce GCM aleatorio; propuesta AES-256 y nonce de 96 bits. No reutilizar el par clave/nonce. Cifrar con tag de autenticación.
3. Envolver únicamente la clave AES con RSA-OAEP; propuesta RSA de al menos 2048 bits y OAEP con SHA-256. RSA no cifra el documento completo. Guardar versión del formato, identificador de clave RSA, nonce, tag/ciphertext y clave envuelta.
4. Persistir sobre y metadatos coherentemente. SQLite y sistema de archivos no comparten transacción: propuesta archivo temporal privado, renombrado atómico y transacción de metadatos con limpieza/recuperación ante fallo. Estado incompleto nunca habilita entrega.
5. **Descargar:** respetar el orden de F3 p. 3: cuota en Nginx; sesión; rol/asignación; apertura; integridad. Desenvolver clave, verificar GCM y comparar SHA-256 de bytes recuperados con referencia protegida.
6. Solo después de todas las verificaciones devolver el documento completo y auditar 200. No usar streaming previo a validación; texto ficticio pequeño con límite de tamaño hace viable validar en memoria. Propuesta `Content-Disposition: attachment`, tipo explícito y `Cache-Control: no-store` también en errores de descarga.
7. **Ensayar:** utilidad local modifica una letra y vuelve a cifrar con material criptográfico nuevo; mantiene hash aprobado. Seleccionar esa copia produce 409 por hash, aun siendo válido el tag. Corromper tag/ciphertext es una prueba adicional distinta. Restaurar selecciona el original conservado.

Fuente del ciclo: F3 pp. 1–3. Tamaños de claves, formato, persistencia y cabeceras de descarga son propuestas. Validar claves/certificados con OpenSSL y biblioteca cuando se implemente; no guardar texto plano original en directorios web.

## Tres nociones de tiempo

| Tiempo | Uso | Quién lo cambia |
|---|---|---|
| Real | TOTP, expiración de sesiones y hora real del evento | Reloj normal del sistema; la demo no lo altera |
| Didáctico | Evaluar fecha y apertura a las 08:00 inclusive | Utilidad local controlada por el presentador |
| Evidencia | Relacionar evento con condiciones de la prueba | Registrar tiempo real y tiempo didáctico etiquetados |

F3 p. 3 exige independencia. Propuesta: proveedor de reloj inyectable solo en la política de apertura; timestamps con zona y comparación de instantes conscientes de zona. La utilidad no recibe la hora desde el navegador. Cambiar de fecha no debe permitir abrir un parcial de otra fecha por comparar solo horas.

## Datos y permisos

Modelo mínimo propuesto, no esquema implementado:

| Entidad | Campos esenciales | Restricción |
|---|---|---|
| Cuenta | ID, nombre ficticio, rol, derivado de contraseña, sal y parámetros | Dos cuentas de ensayo; sin claves en respuestas/logs |
| Sesión | ID opaco, cuenta, MFA completado, creación/expiración real | Invalida o expirada produce 401 |
| Parcial / versión | ID, docente, estudiante asignado, fecha de apertura, hash de referencia, ID de sobre y clave | Un parcial activo; hash no editable desde formularios genéricos |
| Sobre | Bytes cifrados, nonce/tag, clave AES envuelta, versión de formato | Volumen privado, fuera de estáticos |
| Evento | ID, hora real, hora didáctica si aplica, actor/anónimo, acción, decisión, motivo, ID de solicitud | Sin cuerpo, contraseña, OTP, cookie o claves |
| Estado de ensayo | Hora/offset y selector de copia | Modificable únicamente por utilidad local |

Secreto TOTP y privada RSA: archivos de secretos locales con permisos del sistema; montaje de solo lectura donde sea posible. Propuesta separar volumen de SQLite, sobres y logs; Nginx no accede a SQLite ni sobres. Las claves TLS solo se montan en Nginx. Las copias de seguridad también son privadas. No confundir «fuera de Git» con cifrado automático de un secreto en disco.

Propuestas operativas: un proceso inicial para SQLite, transacciones cortas, timeout de bloqueo, directorios escribibles mínimos, ejecución sin root donde sea viable y configuración sin privilegios Docker. Resolverlos con pruebas del equipo antes de declarar bastionado.

## Auditoría y errores

Python registra rechazos 401/403/409 y entregas 200, accesos MFA, publicación y cambios de ensayo. Nginx registra el exceso 429 y un ID correlacionable. La UI docente mostrará eventos de aplicación; una exportación combinará o adjuntará por separado el log Nginx para cubrir **todos** los intentos. No se presentará SQLite como fuente de los 429 si Python nunca recibió esas peticiones.

En 401/403 no se lee el parcial; después de apertura, hash distinto o tag inválido bloquean sin bytes del documento. Si faltan archivo/referencia, se deniega y registra un motivo específico. Código adicional propuesto en RESUMEN; errores internos no muestran traceback ni rutas. Propuesta: si no puede registrarse una decisión de entrega, no entregar y responder indisponibilidad; confirmar y probar el fallo de auditoría durante construcción.

## Red, TLS y laboratorios

El certificado local tendrá SAN para el host/IP elegido. Documentar su confianza en Windows y navegador; una excepción aceptada sin validación no equivale a una identidad TLS verificada. TLS termina en Nginx y el salto interno HTTP es privado del portátil (F3 p. 2), no cifrado extremo a extremo hasta Python. La captura HTTPS de P4 se hará del lado navegador–Nginx y sin claves de sesión.

Nginx: `server_tokens off`, `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, incluidas respuestas de error. La cabecera puede seguir diciendo `Server: nginx`; ocultar versión no corrige vulnerabilidades. Propuesta CSP ajustada a las plantillas. HSTS se explica junto a TLS; activarlo exige comprobar confianza y comportamiento local, sin afirmar que está implementado (F3 p. 4).

| Entorno | Separación y finalidad |
|---|---|
| Portal protegido | Dos servicios normales; único puerto del portal en loopback |
| HTTP de ensayo | Perfil explícito y temporal, solo marca ficticia; nunca servir la carpeta del proyecto o datos reales |
| SQL vulnerable | Perfil Compose separado, red y base propias, sin claves, cuentas ni volúmenes del portal; desactivado por defecto |
| Carga | Dos clientes Docker de IP distinta conectados a Nginx para P9; sin publicar Python ni usar la red universitaria |
| Packet Tracer | Maqueta WiFi WPA2, VLAN 10 docentes, 20 servidores, 30 alumnado, acceso/troncal y políticas entre zonas; RADIUS para administración del switch |
| NAC y ARP | Modelo Python de reglas/estado y tablas ARP ilustrativas; no filtran paquetes reales ni atacan Windows |

Las herramientas transitorias no cambian los dos servicios normales. Los perfiles de laboratorio no se levantan con el portal por defecto. Cualquier servicio de ensayo publicado en el host también se enlaza solo a `127.0.0.1`.

P9 exige como máximo 100 peticiones, concurrencia 5, cuota de 5 r/s/IP y margen 5, con código 429 explícito (F3 p. 7). Verificar las IP que ve Nginx; el NAT de Docker Desktop puede agrupar clientes del host. Usar clientes internos con IP distintas, no cabeceras `X-Forwarded-For` inventadas. Registrar latencia del cliente legítimo, CPU y distribución de códigos; no predecir un porcentaje fijo ni atribuir un DDoS real a esta prueba.

## Mapa de archivos futuros

El mapa inicial se complementa con IDENTIDAD_ACCESO y README. Autenticación, configuración, política RBAC, SQLite y auditoría de identidad ya están implementados. Reloj didáctico y ABAC de disponibilidad ya están implementados; criptografía del examen, almacén de sobres y laboratorios siguen pendientes.

| Ruta propuesta | Responsabilidad |
|---|---|
| `compose.yaml`, `Dockerfile`, `requirements.txt` | Servicios normales, empaquetado y dependencias fijadas |
| `infra/nginx/default.conf` | Proxy, TLS, cabeceras, logs y cuota |
| `app/__init__.py`, `app/main.py` | Paquete y entrada FastAPI implementados; `app/config.py` se pospone hasta necesitar configuración |
| `app/auth.py`, `app/policy.py`, `app/clock.py` | Identidad/TOTP, permisos/descarga y reloj didáctico |
| `app/crypto.py`, `app/storage.py`, `app/db.py`, `app/audit.py` | Sobre, persistencia, consultas y eventos |
| `app/templates/`, `app/static/styles.css` | Vistas y diseño accesible |
| `scripts/demo.py` | Hora, copia alterada, restauración; solo terminal |
| `scripts/security_checks.ps1` | Flujo local de controles y bloqueo de promoción |
| `labs/compose.labs.yaml`, `labs/sql/`, `labs/http/` | Entornos de ensayo aislados |
| `labs/nac/model.py`, `labs/network/topologia.pkt`, `labs/network/arp.md` | Simulaciones separadas |
| `tests/test_auth.py`, `tests/test_policy.py`, `tests/test_crypto.py`, `tests/test_audit.py` | Pruebas automáticas de reglas críticas |
| `tests/test_nac.py`, `tests/test_labs.py`, `tests/test_demo.py` | Reglas simuladas, aislamiento y restauración |
| `docs/GUIA_WINDOWS.md`, `docs/evidencias/` | Guía futura y fichas saneadas; artefactos privados ignorados |

La UI propuesta usa el sobre sellado como identidad visual, jerarquía clara, tipografía legible, foco visible y estados textuales «cerrado», «disponible» o «entrega bloqueada». Los textos reflejan respuestas reales del servidor; un indicador verde no certifica cifrado ni integridad. Contrastar escritorio/móvil, teclado y errores en etapas 1–3 y 6.

## Decisiones pendientes acotadas

Etapas 1 y 2A resuelven base local, identidad, TOTP, caducidad y permisos por rol. 2B resuelve asignaciones y horario de metadatos. Etapa 3: formato del sobre, atomicidad y errores no fijados por F3. Etapa 4: TLS y soporte de Packet Tracer. Etapa 5: CVE corregible y herramientas de análisis. No se inicia etapa 3 en esta entrega.
