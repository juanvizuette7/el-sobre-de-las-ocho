# El sobre de las ocho

Portal académico de Sistemas de Comunicaciones y Seguridad Informática, Universidad Cooperativa de Colombia. **Etapa 1:** portada funcional, estado de salud y entorno local con FastAPI, Nginx y Docker Compose. Docente, estudiante y laboratorio se presentan como áreas pendientes; todavía no hay usuarios, descargas de exámenes, cifrado, MFA ni reloj didáctico.

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

La portada presenta el portal docente, el portal estudiante y el laboratorio de seguridad previsto para administración. Todas las funciones de evaluación están pendientes de habilitación. El laboratorio no tiene rutas públicas ni controles operativos. **Comprobar conexión** consulta realmente `/health`. La navegación admite teclado y enlace de salto al contenido; sin JavaScript se conserva el acceso al JSON de salud.

HTTP se usa exclusivamente para desarrollo local en esta etapa. HTTPS/TLS corresponde a la etapa 4. El único puerto publicado es `127.0.0.1:8080` de Nginx; el puerto 8000 de FastAPI no se publica en el anfitrión.

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

Para arrancar otra vez: `docker compose up -d --wait --wait-timeout 120`. Para retirar contenedores/redes de este proyecto: `docker compose down` (no borra el código ni las imágenes). No se usa `down -v`; todavía no se crean bases o volúmenes de datos.

## Pruebas con pytest

La imagen de pruebas es temporal y **no añade un tercer servicio a Compose**. No publica puertos y se ejecuta sin red. No instala pytest en la imagen del portal.

```bat
docker build --target test -t el-sobre-de-las-ocho-tests:etapa1 .
docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa1
```

Los nueve casos verifican salud, HTML/recursos/anclas y ausencia de rutas privadas o futuras. Los resultados ejecutados, incidencias corregidas y límites de verificación se registran en [la ficha de etapa 1](docs/evidencias/etapa-01.md). No se han ejecutado P1–P10 del examen.

Revisión de navegador opcional, solo para desarrollo: requiere Node/npm y Google Chrome instalado; no se necesita para usar el portal. Las herramientas quedan en `.qa/`, ignorada por Git y excluida del contexto Docker:

```bat
npm install --prefix .qa --no-save --package-lock=false playwright@1.65.0 @axe-core/playwright@4.14.0
node scripts\verificar_interfaz.cjs
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

No se necesita `.env` ni ningún secreto para esta portada. No se crean archivos vacíos de configuración de autenticación antes de necesitarla. Los PDF previamente rastreados por Git siguen rastreados: las exclusiones no cambian el índice ni el historial.

## Documentación

La [guía Windows](docs/GUIA_WINDOWS.md) contiene los procedimientos operativos. La [matriz de clases](docs/MATRIZ_CLASES.md) distingue cobertura parcial de prácticas pendientes. La arquitectura y las seis etapas permanecen en [ARQUITECTURA.md](docs/ARQUITECTURA.md) y [PLAN_IMPLEMENTACION.md](docs/PLAN_IMPLEMENTACION.md); el seguimiento de construcción no se muestra en el producto. Las explicaciones didácticas están separadas en [GUIA_ESTUDIANTE.md](docs/GUIA_ESTUDIANTE.md).

Referencias técnicas consultadas: [plantillas en FastAPI](https://fastapi.tiangolo.com/advanced/templates/), [TestClient y pytest](https://fastapi.tiangolo.com/tutorial/testing/) y [salud y orden de arranque en Compose](https://docs.docker.com/compose/how-tos/startup-order/). Las fuentes académicas y páginas siguen siendo los PDF locales indicados en la matriz.

La etapa 2 requiere autorización; esta entrega no implementa identidades, permisos ni el examen protegido.
