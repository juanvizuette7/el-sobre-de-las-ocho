# Identidad y control de acceso — etapa 2A

## Alcance

Autenticación real de dos cuentas ficticias, TOTP obligatorio docente, sesiones opacas persistentes, RBAC en servidor y auditoría de identidad. El portal conserva FastAPI/Uvicorn, Nginx, dos servicios Compose y publicación exclusiva en `127.0.0.1:8080`. SQLite se ejecuta dentro de Python, sin servicio adicional. Publicación, asignaciones, descargas, cifrado, reloj didáctico y laboratorios siguen sin implementar. ABAC no está aplicado a recursos todavía.

## Ejecución e inicialización local

CMD de Windows, con Docker Desktop y contenedores Linux activos:

```bat
cd /d C:\Users\juanv\Proyectos\el-sobre-de-las-ocho
docker compose up -d --build --wait --wait-timeout 120
docker compose exec app python -m app.manage inicializar
```

El segundo comando requiere terminal interactiva y solicita dos contraseñas distintas de 12–128 caracteres, cada una con confirmación y sin eco. Las cuentas se denominan **docente** y **estudiante**, con roles fijos DOCENTE y ESTUDIANTE. No se transmiten contraseñas por argumentos, variables de entorno ni archivos de configuración. El alta no sobrescribe cuentas existentes.

El procedimiento genera un secreto TOTP independiente y muestra **solo en esa terminal privada** el secreto de enrolamiento y una URI `otpauth://`. Configurar una entrada en un autenticador local compatible con TOTP/RFC 6238: nombre docente, emisor El sobre de las ocho, seis dígitos, intervalo 30 segundos, HMAC-SHA1. Se puede introducir manualmente el secreto o importar la URI si el autenticador lo permite. No se utiliza un servicio web para generar códigos o QR. No capturar ni compartir la pantalla de enrolamiento.

Introducir el código actual del autenticador en la terminal, también sin eco. Solo si coincide se crean las cuentas y se guarda el secreto. Un código incorrecto aborta el alta; repetir el comando generará otro secreto que deberá sustituirse en el autenticador. Tras el alta, esperar al **siguiente código**: el código de confirmación ya fue consumido. Contraseñas y URI no se incluyen en esta documentación.

El repositorio no incluye un autenticador de escritorio. Su instalación/configuración local corresponde al operador; el servidor nunca muestra códigos de acceso ni su secreto mediante HTTP. La verificación automatizada utiliza un autenticador programático exclusivamente en contenedores efímeros de prueba, no en el portal principal.

```bat
start http://127.0.0.1:8080/acceso
```

Estudiante: usuario `estudiante` y contraseña configurada → panel estudiante. Docente: usuario `docente` y su contraseña → desafío del autenticador → panel docente solo con TOTP válido. Para representar ambas cuentas, usar ventanas normal y privada. Cerrar sesión mediante el formulario del panel. No se admiten destinos de redirección arbitrarios ni roles enviados por el cliente.

## Sesiones y política de acceso

| Control | Implementación |
|---|---|
| Contraseña | Argon2id, 64 MiB, tres iteraciones, paralelismo 1; sal aleatoria por derivación, generada por la biblioteca. Una derivación simultánea por proceso limita consumo de memoria. |
| Cuenta desconocida | Mensaje idéntico al de contraseña errónea y verificación Argon2 con derivado señuelo; no se afirma resistencia absoluta a análisis temporal. |
| Sesión anónima | Token aleatorio para proteger login con CSRF; dura 10 minutos. |
| Desafío docente | Después de contraseña correcta, token nuevo sin permisos privados; vence en 5 minutos. |
| Sesión autenticada | Token nuevo al autenticar estudiante o completar TOTP docente; duración absoluta de 30 minutos, sin prolongación automática. |
| Cookie | `sobre_sesion`, 256 bits aleatorios, HttpOnly, SameSite=Lax, Path=/, sin Domain. SQLite conserva SHA-256 del token; no un token utilizable directamente. |
| Estado del servidor | Cuenta activa, vencimiento, nivel, rol y prueba MFA se consultan en cada acceso. Un cambio administrativo de rol no convierte una sesión estudiante en sesión docente con MFA. |
| CSRF | Token sincronizado por sesión y origen exacto `PORTAL_ORIGIN` en todos los POST de acceso, TOTP y salida. Se rechaza origen ausente, `null` o ajeno. |
| TOTP | Reloj real, 30 s, seis dígitos, tolerancia ±1 paso; consumo atómico del paso aceptado. No se permite repetirlo, incluso en otro desafío. |
| Caducidad/cierre | Sesiones vencidas no autorizan. Logout elimina la sesión en SQLite y la cookie. La revocación local permite cerrar todas las sesiones. |
| Abuso | Cinco intentos de contraseña por nombre de cuenta en cinco minutos; cinco intentos TOTP por cuenta en el mismo intervalo, aunque se cambie cookie. Límite agregado de 30 intentos de contraseña por origen visto por Python. |
| Auditoría | Fecha real, ID de cuenta conocida o anónimo, acción, resultado y motivo interno. Sin cuerpos, contraseñas, OTP, URI, claves, CSRF o cookies. |
| Fallo de almacenamiento/secreto | Denegación; no habilita rutas privadas. Error SQLite devuelve 503 saneado. Si falla la escritura de auditoría, no se completa la operación autenticada. |
| Caché | Respuestas dinámicas `Cache-Control: no-store`; contenido privado no se almacena intencionalmente en caché. |

Los límites cuentan intentos, incluidos los válidos; no se reinician al autenticar. Puede ser necesario esperar cinco minutos tras varios ensayos. Python ve el proxy como origen de red, por lo que el límite agregado agrupa a los clientes locales. No se confía en cabeceras reenviadas por el cliente. No equivale a la cuota por IP de Nginx ni a la prueba de carga de etapas posteriores.

Nginx registra método, ruta sin query, código y tamaño; omite cuerpos y cabeceras. El access log duplicado de Uvicorn se desactiva para no registrar consultas. La auditoría estructurada de identidad está en SQLite; los logs operativos del proxy no sustituyen esos eventos.

`Referrer-Policy: same-origin` conserva el contexto del propio origen para formularios y omite referencias hacia otros sitios. La configuración anterior `no-referrer` podía convertir el origen de un POST en `null`; se corrigió tras probar el navegador real, sin relajar el rechazo de orígenes no confiables.

### Respuestas privadas

| Situación | Resultado |
|---|---|
| `/docente` o `/estudiante` sin sesión completa | 401 |
| Estudiante intenta `/docente` | 403 |
| Docente completo intenta `/estudiante` | 403 |
| Contraseña docente válida, TOTP aún pendiente | No accede a ningún panel |
| Token CSRF/origen inválido | 403 |
| Límite de intentos alcanzado | 429 |
| Login/MFA correcto | 303 hacia la siguiente pantalla; panel autorizado 200 |
| `/admin`, `/laboratorio`, `/descargar` | 404: no implementados |

## Almacenamiento, HTTP y frontera de confianza

Volumen nombrado `identidad` montado **solo en Python** en `/data`. Contiene `portal.sqlite3` (cuentas, sesiones, contadores y eventos) y `secrets/docente.totp`. Directorios privados 0700 y archivos 0600 dentro del contenedor Linux. El resto de la raíz sigue de solo lectura; Nginx no monta estos datos. No se exponen directorios de datos/secretos por rutas estáticas. `stop`, `restart` y `down` sin `-v` conservan cuentas; no usar `down -v` como procedimiento de reinicio.

La privada del futuro cifrado no se crea en 2A. El secreto TOTP está protegido por permisos y aislamiento, **no cifrado en disco**. Un administrador de Windows/Docker o del volumen puede acceder a él y a la base. El modelo de amenaza no impide al propietario del equipo modificar almacenamiento. La bitácora tampoco se presenta como inmutable. Las copias del volumen son privadas.

HTTP local no garantiza confidencialidad en tránsito. Se usan únicamente credenciales ficticias. HttpOnly reduce acceso desde scripts y SameSite/CSRF protegen frente a falsificación; no cifran la conexión ni resuelven un equipo comprometido. `Secure` queda desactivado para HTTP y se activa automáticamente cuando `PORTAL_ORIGIN` use HTTPS. Esto solo prepara la cookie: **TLS no está implementado** y cambiar la variable no crea un certificado. La etapa de red debe activar TLS, actualizar origen y repetir la verificación completa. El origen actual debe abrirse como `http://127.0.0.1:8080`, no alternar con `localhost` al enviar formularios.

Revocación operativa, desde terminal autorizada:

```bat
docker compose exec app python -m app.manage revocar-sesiones
```

Exige confirmación `REVOCAR`. Borra las sesiones de servidor y registra el evento; no borra cuentas, auditoría, contadores o TOTP. El alta inicial no es una función de restablecimiento. Recuperación de contraseña o reenrolamiento de un autenticador perdido no se implementan en 2A; no eliminar el volumen para improvisar una recuperación.

## Archivos y validación

| Archivo | Responsabilidad |
|---|---|
| `app/config.py` | Origen local, duración, directorio y Secure según HTTPS |
| `app/db.py` | Esquema SQLite, conexiones y transacciones |
| `app/security.py` | Argon2id y validación de pasos TOTP |
| `app/sessions.py` | Tokens opacos, rotación, vigencia y límites persistentes |
| `app/auth.py` | Formularios, CSRF, login, MFA, salida y paneles |
| `app/policy.py` | Dependencias de RBAC y denegación por defecto; ABAC futuro será adicional |
| `app/audit.py` | Registro de eventos con motivos internos |
| `app/manage.py` | Alta interactiva y revocación local de sesiones |
| `app/main.py` | Factoría, ciclo de vida, caché, errores y recursos públicos |
| `app/templates/acceso.html`, `panel.html`, `privado_base.html`, `error.html` | Vistas de identidad, privadas y de error |
| `app/static/auth.js` | Estado de envío sin sustituir controles backend |
| `tests/test_auth.py` | Casos de seguridad con cuentas aleatorias y bases temporales |
| `scripts/verificar_identidad.cjs` | Recorrido real Nginx/FastAPI con proyecto Compose efímero en 127.0.0.1:8081; datos en tmpfs |

CMD para pruebas sin usar las cuentas del portal:

```bat
docker build --target test -t el-sobre-de-las-ocho-tests:etapa2a .
docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa2a
python scripts\verificar_etapa1.py
```

Verificación de navegador opcional con las herramientas `.qa` ya descritas en README:

```bat
node scripts\verificar_interfaz.cjs
node scripts\verificar_identidad.cjs
```

El segundo script requiere 8081 libre, inicia su propio proyecto de dos servicios, genera credenciales en memoria y lo retira al terminar. Nunca inicializa cuentas en `identidad`. No exportar logs de sesión, capturas de enrolamiento o archivos de datos como evidencia pública. Resultados reales en [la ficha 2A](evidencias/etapa-02a.md).

## Referencias

Especificación académica: F3 pp. 1–3, 5–6; clase 4, `Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf`, pp. 2, 4–7 y 15. Alcance IAM/AAA/MFA/RBAC en MATRIZ_CLASES; ABAC de asignaciones/horario sigue pendiente para 2B.

Referencias técnicas primarias consultadas: [Argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/howto.html), [PyOTP](https://pyauth.github.io/pyotp/), [sesiones OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [CSRF OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) y [Origin en MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin). No se releyeron los PDF originales ni se añadieron tecnologías ajenas al alcance.
