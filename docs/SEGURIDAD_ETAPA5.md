# Seguridad de aplicación — etapa 5

## SQL Injection

`scripts/demo_sql_injection.py` usa SQLite en memoria y dos nombres ficticios. La consulta concatenada existe únicamente para representar el riesgo; no se importa en FastAPI ni recibe tráfico HTTP. Su contraparte usa `?` y parámetros. `tests/test_stage5.py` comprueba ambos resultados. La revisión de las consultas de `app/` no encontró SQL construido con entradas de usuario; los valores se pasan como parámetros a SQLite.

## Límite de intentos

`app/auth.py` ya aplica `excede_limite` desde `app/sessions.py`: cinco intentos por cuenta durante 300 segundos y hasta 30 intentos por origen en la misma ventana. La regla se usa en contraseña y TOTP; no se amplía a consultas del examen. El siguiente intento bloqueado obtiene HTTP 429 y se registra con motivo interno `limite_intentos`. Tras vencer la ventana, la petición vuelve a recibir el resultado normal de autenticación. Auditoría no guarda contraseña, OTP, cookie o cuerpo.

`test_rate_limit_auditoria_y_recuperacion` valida cinco fallos, el 429, el evento y la recuperación mediante un reloj inyectado. Usa credenciales aleatorias de fixture y base temporal; no espera cinco minutos ni accede al volumen real.

## Análisis estático y de imagen

Bandit 1.9.4 encontró B608 en la línea de concatenación de la demostración SQL. Es un hallazgo real en el código demostrativo e intencional; el alcance se reduce por la base en memoria y los datos ficticios. B310 en los verificadores que usan `urllib` se suprimió localmente porque el host es loopback HTTPS fijo y las rutas son constantes/cerradas. No hubo hallazgos High/Critical de Bandit.

Trivy 0.76.2 reportó, en la imagen anterior Python 3.12 sobre Debian 12, dos registros críticos del sistema operativo: `CVE-2025-7458` en SQLite y `CVE-2023-45853` en zlib (marcado `will_not_fix` por la base). Se actualizó el digest de `python:3.12-slim-trixie`; la imagen reconstruida usa Debian 13.7 y ya no reporta esos críticos. De los 49 registros High iniciales, dos correspondían a `zlib1g` y tenían parche disponible. Se fijó e instaló `1:1.3.dfsg+really1.3.1-1+deb13u1`, sin actualizar otros paquetes. Un escaneo dirigido de la imagen reconstruida confirma que ambos registros desaparecieron. Quedan 47 registros High en paquetes Debian del sistema base, todos sin versión corregida indicada en el informe. El inventario de `requirements.txt` no reporta vulnerabilidades.

### Clasificación del informe High

El informe inicial corresponde al contenido de la imagen runtime usada por FastAPI: los ocho DiffID de sus capas coincidían con los del contenedor activo. El escaneo posterior identifica directamente la imagen reconstruida por digest. Los 49 eran hallazgos de paquetes de sistema (`os-pkgs`), no de bibliotecas Python (`lang-pkgs`). La tabla agrupa los 49 registros por CVE y paquetes afectados:

| Paquetes afectados | CVE High | Corrección en el informe inicial |
|---|---|---|
| `bsdutils`, `libblkid1`, `liblastlog2-2`, `libmount1`, `libsmartcols1`, `libuuid1`, `login`, `mount`, `util-linux` | `CVE-2026-76642`, `CVE-2026-78408`, `CVE-2026-78409`, `CVE-2026-78410` | Sin versión corregida; 36 registros de paquete/CVE. |
| `libacl1` | `CVE-2026-54369` | Sin versión corregida. |
| `libncursesw6`, `libtinfo6`, `ncurses-base`, `ncurses-bin` | `CVE-2025-69720` | Sin versión corregida. |
| `libsqlite3-0` | `CVE-2026-119373`, `CVE-2026-119374`, `CVE-2026-119379` | Sin versión corregida; es el grupo de mayor relevancia porque la aplicación usa SQLite. |
| `libsystemd0`, `libudev1` | `CVE-2026-16742` | Sin versión corregida. |
| `perl-base` | `CVE-2026-9538` | Sin versión corregida. |
| `zlib1g` | `CVE-2026-76844`, `CVE-2026-85091` | Corregidos con `1:1.3.dfsg+really1.3.1-1+deb13u1`; 2 registros eliminados del escaneo nuevo. |

Los registros de `util-linux` describen funciones de montaje, `nsenter` y resolución de rutas/montajes; la aplicación no invoca esos programas y el contenedor corre como UID no privilegiado, con capacidades descartadas y sistema de archivos de solo lectura. Las alertas de ncurses, ACL, systemd/udev y Perl son de paquetes presentes en la imagen base; no se encontró llamada desde el código de la aplicación a esas herramientas. SQLite sí forma parte de la persistencia del portal: las consultas usan parámetros y la base está en un volumen privado, pero esos controles no sustituyen un parche de `libsqlite3-0`. Se conserva ese riesgo residual hasta que Debian publique una versión corregida. Trivy no indica corrección para los otros 44 registros restantes; se revisarán con una futura actualización de su base y de la imagen fijada, sin ocultarlos ni actualizar paquetes a ciegas.

### Revisión de imágenes candidatas

El 10 de noviembre de 2026 se compararon alternativas sin modificar el servicio actual:

| Candidata | Verificación observada | Decisión |
|---|---|---|
| `python:3.12-slim-trixie` | `docker pull` resolvió al mismo digest ya fijado (`5e2bdb1…`); no es una base más nueva. | Se conserva la imagen actual. |
| `python:3.12-alpine3.23` | Escaneo Trivy de la imagen base: 0 High/Critical; SQLite 3.53.4. | Descartada: versión anterior a 3.54.0 y cambia glibc por musl. El resultado Trivy no acredita que SQLite esté corregida. |
| `python:3.12-alpine3.24` | Escaneo Trivy de la imagen base: 0 High/Critical; `apk policy` y Python confirman SQLite 3.53.4. | Descartada por la misma vulnerabilidad subyacente y por no haber probado las dependencias de la aplicación en musl. |
| Debian Sid / SQLite 3.54.1 | El tracker oficial marca como corregida allí; Trixie (estable) y Forky aún aparecen vulnerables. No existe el tag consultado `python:3.12-slim-sid`. | No se adopta Sid: sería una base de desarrollo continuo, no una alternativa estable equivalente. |

Trivy informó cero alertas para las bases Alpine candidatas, pero ese conteo no es prueba suficiente de seguridad: su SQLite 3.53.4 cae en el rango afectado señalado por el tracker Debian y las descripciones upstream. Por tanto no se construyó ni probó una imagen completa de la aplicación basada en esas candidatas ni se sustituyó el servicio. El [tracker oficial de SQLite en Debian](https://security-tracker.debian.org/tracker/source-package/sqlite3) muestra Trixie en `3.46.1-7+deb13u2` como vulnerable, Forky en `3.53.4-2` como vulnerable y Sid en `3.54.1-2` como corregida. Los detalles oficiales de [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373), [CVE-2026-119374](https://security-tracker.debian.org/tracker/CVE-2026-119374) y [CVE-2026-119379](https://security-tracker.debian.org/tracker/CVE-2026-119379) describen requisitos FTS5/session específicos. Esas extensiones están compiladas en la SQLite actual, pero `app/` no crea tablas FTS ni usa cambiosets de sesión; la base privada no acepta archivos SQLite cargados por usuarios. Esto reduce exposición directa, pero no elimina el riesgo de una futura ruta que permita datos o esquemas SQLite manipulados. El riesgo residual se mantiene hasta una versión corregida estable.

Trivy también marcó DS-0026 (Low) al inspeccionar Dockerfile aislado, porque no declara `HEALTHCHECK` en la imagen. La salud está declarada por servicio en `compose.yaml` y se comprobó con Compose; se clasifica como limitación del contexto escaneado, no como ausencia de healthcheck en ejecución.

## Secretos y datos

La revisión encontró CA/clave TLS y SQLite solo en carpetas locales excluidas (`certs/`, `data/`); los artefactos Trivy/PCAP están en `.qa/`, también ignorada. `git ls-files` no mostró claves, bases, secretos o capturas. Los PDF originales del profesor siguen intactos y no se escanean como parte del análisis del código.

## Comprobación reproducible en CMD

```bat
python scripts\demo_sql_injection.py
docker build --target test -t el-sobre-de-las-ocho-tests:etapa5 .
docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa5 python -m pytest -q -p no:cacheprovider tests/test_stage5.py tests/test_auth.py::test_rate_limit_auditoria_y_recuperacion
uvx --from bandit==1.9.4 bandit -r app scripts -ll
if not exist .qa\trivy mkdir .qa\trivy
docker save -o .qa\trivy\portal-image.tar el-sobre-de-las-ocho-app:etapa1
docker run --rm -v "%CD%:/project" aquasec/trivy:0.76.2 image --input /project/.qa/trivy/portal-image.tar --scanners vuln --severity HIGH,CRITICAL
docker run --rm -v "%CD%:/project:ro" aquasec/trivy:0.76.2 fs --scanners vuln,misconfig,secret --skip-dirs /project/.git --skip-dirs /project/.qa --skip-dirs /project/certs --skip-dirs /project/data --skip-dirs /project/docs/material-profesor /project
```

Bandit termina con B608 medio por diseño en la muestra intencional. Trivy descarga su base de avisos la primera vez y puede reportar cambios posteriores; comparar identificador, paquete, severidad, estado de corrección y uso efectivo antes de actuar. Los ejercicios no modifican cuentas, documentos, reloj ni el volumen principal. No requieren un comando de restauración; los resultados de QA y la base de SQL temporal se eliminan al cerrar el proceso.
