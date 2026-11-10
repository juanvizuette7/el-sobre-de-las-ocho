# El sobre de las ocho

Portal académico de Sistemas de Comunicaciones y Seguridad Informática, Universidad Cooperativa de Colombia. **Etapas 1, 2A, 2B y 3:** identidad/TOTP/RBAC, asignación/apertura y documentos protegidos, en FastAPI detrás de Nginx. Publicación de TXT UTF-8 con AES-256-GCM, RSA-OAEP y SHA-256. SQLite y sobres en el volumen privado existente. TLS y laboratorios de red pendientes.

## Ejecutar en CMD de Windows

Abre Docker Desktop y espera a que el motor esté listo. Usa contenedores Linux. La primera construcción necesita Internet para descargar las imágenes y dependencias fijadas. No necesitas instalar Python, Nginx ni las bibliotecas en Windows para abrir el portal.

```bat
cd /d C:\Users\juanv\Proyectos\el-sobre-de-las-ocho
docker version
docker compose version
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
start http://127.0.0.1:8080
```

La portada permite iniciar sesión para acceder a los paneles privados. El docente publica el TXT en la tarjeta de evaluación y consulta actividad. El estudiante comprueba acceso y descarga únicamente si el backend autoriza y verifica integridad. El laboratorio no tiene controles web: sus herramientas son CLI locales. **Comprobar conexión** consulta `/health`. Los formularios de acceso/publicación funcionan con envío HTML nativo.

## Sobre cifrado (etapa 3)

Con las cuentas existentes, preparar la evaluación mediante el comando 2B y publicar un `.txt` UTF-8 de hasta 512 KiB desde el panel docente. No reinicializar identidades. El estudiante usa **Comprobar acceso**; conserva reloj grande y confirmación sin hora real visible. Cada descarga revalida RBAC/ABAC, AES-GCM y SHA-256 antes de emitir bytes.

Guía completa con comandos comprobados, dos alteraciones y restauración: [CRIPTOGRAFIA_SOBRE.md](docs/CRIPTOGRAFIA_SOBRE.md). [Resultados](docs/evidencias/etapa-03.md): 120 pruebas y recorrido real de navegador. Módulos nuevos: `app/crypto.py`, `app/storage.py`, `app/documents.py`; tabla aditiva `documentos`. El volumen `identidad` conserva `/data/sobres` y `/data/secrets/sobre-rsa.pem`. Nunca eliminarlo para reiniciar o repetir. Las notas de disponibilidad sin archivo siguientes documentan la etapa histórica 2B; la integración vigente está en la guía criptográfica.

## Inicializar las cuentas ficticias

Desde una terminal CMD privada, con los servicios activos:

```bat
docker compose exec app python -m app.manage inicializar
start http://127.0.0.1:8080/acceso
```

El procedimiento solicita sin eco contraseñas diferentes de 12–128 caracteres para `docente` y `estudiante`, confirma ambas y presenta el enrolamiento TOTP docente únicamente en la terminal. Configurar un autenticador TOTP local compatible (seis dígitos, 30 segundos, HMAC-SHA1) con el secreto o URI mostrados; confirmar su código. Esperar al siguiente código para el primer acceso. No copiar secretos a archivos del repositorio, argumentos o capturas. El comando rechaza sobrescribir cuentas existentes.

Estudiante: contraseña → panel estudiante. Docente: contraseña → código del autenticador → panel docente. Los permisos se comprueban en el servidor. Cerrar sesión desde el panel revoca el token; para revocación operativa global: `docker compose exec app python -m app.manage revocar-sesiones` y confirmar `REVOCAR`. Alta, TOTP, límites, recuperación y frontera de confianza: [IDENTIDAD_ACCESO.md](docs/IDENTIDAD_ACCESO.md).

El almacenamiento real se mantiene sin cuentas predefinidas hasta que el operador ejecute el alta. Las pruebas generan cuentas efímeras aisladas. HTTP local no cifra credenciales: usar solo cuentas ficticias. Cookies HttpOnly/SameSite y CSRF están activos; Secure se habilitará al configurar HTTPS con TLS real en la etapa de red.

HTTP se usa exclusivamente para desarrollo local en esta etapa. HTTPS/TLS corresponde a la etapa 4. El único puerto publicado es `127.0.0.1:8080` de Nginx; el puerto 8000 de FastAPI no se publica en el anfitrión.

## Disponibilidad y reloj de ensayo (2B)

Tras inicializar las cuentas, preparar el caso cerrado:

    docker compose exec app python -m app.demo preparar --fecha 2026-11-09
    docker compose exec app python -m app.demo reloj estado

En el panel estudiante, pulsar **Actualizar disponibilidad**: 07:59:59 devuelve 403. Cambiar solo el reloj del recurso y repetir después de cada comando:

    docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:00:00
    docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:01:00
    docker compose exec app python -m app.demo asignacion retirar
    docker compose exec app python -m app.demo asignacion asignar
    docker compose exec app python -m app.demo auditoria --limite 20

Con asignación: 200 a las 08:00 y 08:01. Al retirarla: 403; al reasignar: 200. La disponibilidad JSON no entrega bytes del examen: si existe un sobre válido, habilita el enlace cuya ruta revalida y descarga.

Para tiempo real: ejecutar el comando siguiente (puede autorizar si ya pasó la apertura):

    docker compose exec app python -m app.demo reloj normal

Para cerrar y repetir el ensayo, volver a **preparar --fecha 2026-11-09**: restablece asignación y 07:59:59 sin borrar identidad ni bitácora. TOTP y sesiones mantienen tiempo real. No hay controles administrativos web. Comandos y política en [AUTORIZACION_HORARIO.md](docs/AUTORIZACION_HORARIO.md); resultados en [evidencia 2B](docs/evidencias/etapa-02b.md).

## Comprobar y reiniciar

```bat
docker compose ps
curl.exe --fail --show-error http://127.0.0.1:8080/health
curl.exe --fail --show-error -I http://127.0.0.1:8080/static/styles.css
docker compose exec nginx nginx -t
docker compose restart
docker compose up -d --wait --wait-timeout 120
curl.exe --fail --show-error http://127.0.0.1:8080/health
```

Esperado: ambos servicios `healthy` y salud `{"status":"ok","servicio":"el-sobre-de-las-ocho","etapa":1}`. Para verificar automáticamente exposición de puertos, redes, usuarios, recursos HTTP y cabeceras, si tienes Python en Windows:

```bat
python scripts\verificar_etapa1.py
```

Para revisar logs o detener sin borrar el proyecto:

```bat
docker compose logs --tail 50
docker compose stop
```

Para arrancar otra vez: `docker compose up -d --wait --wait-timeout 120`. `docker compose down` retira contenedores/redes pero conserva el volumen `identidad`. **No usar `down -v`**: eliminaría cuentas, secreto TOTP, sesiones y auditoría. No se necesita borrar datos para reiniciar.

## Pruebas con pytest

La imagen de pruebas es temporal y **no añade un tercer servicio a Compose**. No publica puertos y se ejecuta sin red. No instala pytest en la imagen del portal.

```bat
docker build --target test -t el-sobre-de-las-ocho-tests:etapa2b .
docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa2b
```

Se conservan los casos de portada/infraestructura, identidad, MFA, CSRF, RBAC, vigencia, revocación y ausencia de secretos. La suite usa bases temporales sin acceder al volumen real. Las fichas [2A](docs/evidencias/etapa-02a.md), [2B](docs/evidencias/etapa-02b.md) y [3](docs/evidencias/etapa-03.md) distinguen la cobertura de cada entrega: P1–P3 se verifican en etapa 3; P4–P10 siguen pendientes. Para ejecutar toda la suite vigente, construir el destino test y usar la etiqueta `etapa3` de la guía criptográfica; las etiquetas históricas siguientes no identifican ramas de código.

Revisión de navegador opcional, solo para desarrollo: requiere Node/npm y Google Chrome instalado; no se necesita para usar el portal. Las herramientas quedan en `.qa/`, ignorada por Git y excluida del contexto Docker:

```bat
npm install --prefix .qa --no-save --package-lock=false playwright@1.65.0 @axe-core/playwright@4.14.0
node scripts\verificar_interfaz.cjs
node scripts\verificar_identidad.cjs
```

La versión de axe usada en la verificación se registra en la ficha. El script comprueba cuatro anchos de pantalla, anclas, teclado, salud/errores/timeout, movimiento reducido, alternativa sin JavaScript y reglas automáticas WCAG A/AA. Guarda capturas/resultados locales en `.qa/`; un análisis automático no acredita accesibilidad completa.

## Cómo encajan las piezas

```text
Navegador en Windows → 127.0.0.1:8080 → Nginx → app:8000 → FastAPI
                                             red interna portal
```

Docker Compose crea dos contenedores. Nginx pertenece a la red de entrada y a la red interna; FastAPI solo a la interna. FastAPI construye el HTML con Jinja2 y sirve CSS/JS; Nginx devuelve esas respuestas al navegador. Los recursos son locales, sin fuentes o scripts de CDN. Ambos procesos ejecutan sin root y con sistema de archivos de solo lectura, excepto `/tmp`. El proxy espera a que la aplicación pase su healthcheck.

| Archivo | Para qué sirve |
|---|---|
| [app/main.py](app/main.py) | Rutas `/` y `/health`, plantillas y directorio estático |
| [app/templates/index.html](app/templates/index.html) | Portada y estados pendientes; `base.html` y `components.html` reutilizan estructura/iconos |
| [app/static/styles.css](app/static/styles.css) | Colores, tipografía, sobre ilustrado con CSS, adaptación móvil y foco |
| [app/static/main.js](app/static/main.js) | Consulta real de salud con timeout y manejo de errores |
| [compose.yaml](compose.yaml) | Dos servicios, redes, puerto local, límites y salud |
| [Dockerfile](Dockerfile) | Imágenes separadas de ejecución y pruebas |
| [infra/nginx/default.conf](infra/nginx/default.conf) | Proxy a `app:8000`, cabeceras y resolución del nombre del servicio |
| [infra/nginx/nginx.conf](infra/nginx/nginx.conf) | Proceso Nginx sin root y archivos temporales en `/tmp` |
| [tests/test_portal.py](tests/test_portal.py) | Contratos de la etapa 1 con pytest y TestClient |
| [requirements.txt](requirements.txt), [requirements-dev.txt](requirements-dev.txt) | Versiones exactas, incluidas dependencias transitivas; los `.in` declaran las directas |
| [.dockerignore](.dockerignore), [.gitignore](.gitignore) | Evitan incluir PDF/secretos en construcción y nuevos artefactos privados en Git |

No se necesita `.env` con contraseñas. `app/config.py` define parámetros no secretos y `PORTAL_ORIGIN`; las credenciales se inicializan interactivamente y el secreto TOTP reside en el volumen privado, fuera del repositorio. El mapa adicional de módulos está en IDENTIDAD_ACCESO. La guía de aprendizaje es material privado: una regla `.gitignore` no retira su versión ya rastreada del índice/historial; no se publica el repositorio en esta entrega. Esto también aplica a los PDF privados previamente versionados.

## Documentación

La [guía Windows](docs/GUIA_WINDOWS.md) contiene los procedimientos operativos. La [matriz de clases](docs/MATRIZ_CLASES.md) distingue cobertura parcial de prácticas pendientes. La arquitectura y las seis etapas permanecen en [ARQUITECTURA.md](docs/ARQUITECTURA.md) y [PLAN_IMPLEMENTACION.md](docs/PLAN_IMPLEMENTACION.md); el seguimiento de construcción no se muestra en el producto. Las explicaciones didácticas están separadas en [GUIA_ESTUDIANTE.md](docs/GUIA_ESTUDIANTE.md).

Referencias técnicas consultadas: [plantillas en FastAPI](https://fastapi.tiangolo.com/advanced/templates/), [TestClient y pytest](https://fastapi.tiangolo.com/tutorial/testing/) y [salud y orden de arranque en Compose](https://docs.docker.com/compose/how-tos/startup-order/). Las fuentes académicas y páginas siguen siendo los PDF locales indicados en la matriz.

2A implementa identidad/RBAC y 2B añade ABAC de disponibilidad, asignaciones y reloj independiente. La etapa 3 añade cifrado, integridad y entrega real. La siguiente etapa es 4 y no se inicia automáticamente.
