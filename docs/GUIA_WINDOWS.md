# Guía de ejecución en Windows — etapas 1, 2A y 2B

Los comandos de uso y pruebas están completos en [README.md](../README.md). Están escritos para **CMD**, sin variables o sintaxis exclusivas de PowerShell. Abre Docker Desktop con motor Linux antes de ejecutarlos. Internet es necesario para la primera construcción; con imágenes construidas puedes volver a iniciar sin reinstalar.

## Actualización 2B

La política y todos los comandos están en [AUTORIZACION_HORARIO.md](AUTORIZACION_HORARIO.md). El reloj persistente se administra con app.demo dentro de Docker y no modifica Windows. Estado de ensayo final: evaluacion-001 asignada a estudiante, apertura 2026-11-09T08:00:00-05:00 y referencia fija 07:59:59. Preparar restablece ese caso; reloj normal vuelve a la hora real y puede autorizar después de la apertura.

    docker compose exec app python -m app.demo preparar --fecha 2026-11-09
    docker compose exec app python -m app.demo reloj estado
    docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:00:00
    docker compose exec app python -m app.demo auditoria --limite 20

No hay bibliotecas adicionales: ZoneInfo y America/Bogota se comprobaron en el contenedor. TOTP y sesiones conservan tiempo real. Sin descarga aún. Resultados en la ficha de etapa 2B.

## Actualización 2A

Acceso y aprovisionamiento: [IDENTIDAD_ACCESO.md](IDENTIDAD_ACCESO.md). Nuevas dependencias fijadas: Argon2-cffi 25.1.0, PyOTP 2.10.0 y python-multipart 0.0.33, incluidas sus transitivas en requirements. Persistencia en volumen `identidad`, privado de Python; no publicar ni copiar su contenido a Git.

```bat
docker compose up -d --build --wait --wait-timeout 120
docker compose exec app python -m app.manage inicializar
start http://127.0.0.1:8080/acceso
```

Alta interactiva con dos contraseñas propias y confirmación de TOTP local. No hay contraseña por defecto ni registro web. No usar `down -v`: elimina la identidad persistente. El inventario de versiones de la sección siguiente corresponde a la base de etapa 1 conservada. La prueba de salud mantiene `etapa: 1` por compatibilidad del contrato; no indica que la autenticación esté ausente.

## Entorno observado

Fecha local de referencia: 9 de noviembre de 2026, zona de Bogotá. No se usa la fecha UTC del log Docker como reloj del laboratorio.

| Componente | Resultado observado |
|---|---|
| Sistema | Windows 11 Pro, versión 10.0.26200 |
| Docker Desktop | 4.49.0, motor Linux activo |
| Docker Engine / CLI | 28.5.1 |
| Compose | v2.40.2-desktop.1 |
| Git | 2.50.1.windows.1 |
| Python de Windows | 3.11.9; opcional para abrir portal, usado en verificador de infraestructura |
| Python del contenedor | 3.12.16 |
| Nginx del contenedor | 1.30.6 |
| FastAPI / Uvicorn / Jinja2 | 0.162.2 / 0.54.0 / 3.1.6 |
| pytest / cliente de prueba | 9.2.0 / httpx2 2.16.0, solo imagen test |
| Memoria del anfitrión | Aproximadamente 15,8 GiB visibles y 5,0 GiB libres al inventariar |
| Disco C | Aproximadamente 170 GiB libres antes de construir |
| Estado inicial Docker | Sin imágenes, contenedores ni volúmenes; se descargaron los necesarios |
| Puerto | 8080 sin escucha al comienzo; ahora reservado al Nginx del proyecto |
| OpenSSL en PATH | No encontrado; no es necesario para HTTP de etapa 1. Preparación de TLS pendiente |

No se verificaron todavía Bandit, Trivy, Nmap, Wireshark o Packet Tracer: corresponden a las etapas siguientes. Las imágenes se fijan por digest en Dockerfile/Compose; las bibliotecas exactas están en los dos archivos `requirements*.txt`. Las actualizaciones se harán con pruebas, no cambiando estos valores a ciegas.

## Sesión cotidiana en CMD

```bat
cd /d C:\Users\juanv\Proyectos\el-sobre-de-las-ocho
docker compose up -d --build --wait --wait-timeout 120
start http://127.0.0.1:8080
```

Después de editar Python, plantillas, CSS o JavaScript, vuelve a ejecutar el `up` con `--build`: el código está copiado a la imagen, no montado con recarga automática. Refresca el navegador. El montaje Nginx es de solo lectura; después de cambiar su configuración ejecuta `docker compose exec nginx nginx -t` y, si pasa, `docker compose restart nginx`.

## Qué comprobar

```bat
docker compose ps
curl.exe --fail --show-error http://127.0.0.1:8080/health
docker compose exec nginx nginx -t
python scripts\verificar_etapa1.py
```

El último comando requiere Python de Windows; los anteriores solo Docker/cURL. `healthy` significa que los controles HTTP del servicio responden. No certifica MFA, cifrado, integridad de exámenes ni P1–P10. El JSON de salud no contiene secretos ni datos de usuarios.

Para pytest sin instalar Python en Windows:

```bat
docker build --target test -t el-sobre-de-las-ocho-tests:etapa2b .
docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa2b
```

## Reinicio y parada

```bat
docker compose restart
docker compose up -d --wait --wait-timeout 120
curl.exe --fail --show-error http://127.0.0.1:8080/health
docker compose stop
```

Es normal una breve indisponibilidad mientras reinician los servicios. El healthcheck confirma recuperación; no cambies el puerto a `0.0.0.0` para resolver un fallo. Después de la verificación se deja el portal disponible para revisar la entrega; `stop` te permite detenerlo al terminar.

## Si algo falla

| Síntoma | Comprobación concreta |
|---|---|
| No conecta con Docker | Abrir Docker Desktop; ejecutar `docker version` y revisar que aparezca servidor Linux, no solo cliente |
| 8080 ocupado | `netstat -ano | findstr :8080`; identificar el proceso, sin finalizarlo a ciegas; no cambiar el alcance del puerto |
| Página no abre | `docker compose ps`, `docker compose logs --tail 50`; abrir exactamente `http://127.0.0.1:8080`, no HTTPS todavía |
| 502 al recrear Python | Esperar su healthcheck y resolución DNS de Docker (hasta unos 10 segundos), luego repetir; revisar logs si persiste |
| Construcción no descarga | Verificar conexión a registros/PyPI; no desactivar certificados para evitar el error |
| Cambios de CSS no aparecen | Reconstruir con `--build` y actualizar el navegador |
| pytest pide otra biblioteca | Usar la imagen test y requirements-dev.txt fijados; no instalar paquetes sueltos en la imagen runtime |

La incidencia inicial de red y el ajuste del cliente de pruebas se describen en [la evidencia de la etapa](evidencias/etapa-01.md). No se modificaron PDF ni historial Git; no se hicieron commits o push.
