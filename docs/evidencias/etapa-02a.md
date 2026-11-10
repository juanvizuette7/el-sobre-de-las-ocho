# Evidencia de etapa 2A — identidad y autorización

Fecha de referencia: 9 de noviembre de 2026, zona de Bogotá. Modalidad: implementación real en entorno local con cuentas ficticias. Alcance: identidad y RBAC; no asignaciones, reloj, cifrado, publicación o descargas. El árbol de trabajo no se ha confirmado en Git; no se atribuye un SHA de commit a esta ejecución.

## Fuentes y entorno

F3: `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf`, pp. 1–3, 5–6. Clase 4: `Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf`, pp. 2, 4–7, 15. Documentación de diseño existente utilizada sin reprocesar PDF. Trazabilidad detallada en [MATRIZ_CLASES.md](../MATRIZ_CLASES.md); políticas y comandos en [IDENTIDAD_ACCESO.md](../IDENTIDAD_ACCESO.md).

Windows/Docker conservados de la etapa 1, Nginx 1.30.6, Python 3.12.16 y FastAPI 0.162.2. Dependencias nuevas fijadas: Argon2-cffi 25.1.0, PyOTP 2.10.0 y python-multipart 0.0.33. Pytest 9.2.0, Chrome instalado, Playwright 1.65.0 y axe 4.14.0 para verificación local. No se almacenaron contraseñas reales ni se configuró un autenticador de usuario en el portal principal.

## Resultados observados

| Comprobación | Resultado real |
|---|---|
| Construcción, inicio, healthchecks y reinicio Compose | Dos servicios saludables; la aplicación recupera portada/salud tras reiniciar |
| `python scripts/verificar_etapa1.py` | 27 comprobaciones aprobadas; incluye Nginx→FastAPI, localhost exclusivo, ausencia de puerto Python, red interna, raíz de solo lectura y rutas protegidas |
| `nginx -t` y recarga de configuración | Configuración válida, salida 0; proxy funcionando con política de referencia compatible con formularios |
| Suite de contenedor sin red, raíz de solo lectura y `/tmp` temporal | **40 passed in 23.52s**: nueve casos heredados adaptados a las rutas de identidad y 31 casos de seguridad |
| Contraseña válida, incorrecta y cuenta inexistente | Acceso correcto; errores genéricos 401 sin revelar existencia; el rol no procede de formularios |
| TOTP incorrecto, correcto y repetido | Incorrecto denegado, válido aceptado, paso consumido rechazado al reutilizarlo; contraseña sola no abre panel docente |
| Sin sesión, sesión vencida, sesión revocada, cuenta desactivada | 401; token anterior eliminado al pasar de estado; logout revoca el registro del servidor |
| RBAC y manipulación del cliente | Estudiante→docente 403; query/formulario con rol o MFA inventados no autorizan; cambio administrativo de rol no fabrica prueba MFA |
| CSRF | Token ausente/falso/no ASCII u origen ausente/ajeno → 403; también en MFA/logout |
| Abuso | Después de cinco intentos se recibe 429; cambiar cookie no elimina contador de cuenta |
| Cookies y respuesta privada | HttpOnly y SameSite=Lax; cookie Secure emitida bajo configuración HTTPS de prueba; no-store en respuestas dinámicas |
| Persistencia y revocación operativa | Una aplicación reiniciada con la misma DB conserva una sesión vigente; el comando local revoca todas las sesiones |
| Derivados, secretos y rutas | Argon2id con sales diferentes; claves, secreto TOTP y token utilizable ausentes del dump; `/data` y `/secrets` no publicados |
| Aprovisionamiento CLI | Alta con confirmación TOTP válida crea dos cuentas; confirmación incorrecta no crea cuentas; alta existente no sobrescribe; sin terminal se rechaza. Entrada de terminal simulada en pruebas, sin exponer valores |
| Permisos del volumen principal | SQLite en 0600; directorio privado; cero cuentas predefinidas tras verificaciones |
| Portada en Chrome a 1440/768/390/320 px | 200, sin desbordamiento, teclado/anclas, salud real, manejo de errores/timeout y alternativa sin JS aprobados |
| Acceso y paneles de identidad en navegador | Login estudiante real, panel, rechazo 403 por URL docente, logout y posterior 401; docente con contraseña pasa a MFA, 401 sin completarlo, código válido abre panel, logout correcto |
| Acceso y panel estudiante a 1440/390 px, panel docente móvil | Revisión de capturas; sin desbordamiento ni infracciones automáticas axe A/AA detectadas en las vistas analizadas; sin excepciones JavaScript |
| Logs del recorrido real | Contraseñas y código usados no aparecen; configuración limita logs operativos a método/ruta sin query/código/tamaño y auditoría a campos internos |

La prueba de navegador usa un proyecto **sobre-identidad-qa**, puerto exclusivo `127.0.0.1:8081`, datos en tmpfs y credenciales aleatorias en memoria. Aprovisiona únicamente ese entorno con la misma función de alta, utiliza formularios reales a través de Nginx y valida TOTP mediante un autenticador programático temporal. No opera sobre `identidad` ni imprime credenciales. Contenedores/redes temporales retirados al terminar. Artefactos locales ignorados: `.qa/identidad-resultados.txt`, `.qa/interfaz-resultados.txt` y `.qa/capturas/` (formularios capturados antes de rellenar credenciales).

## Incidencia detectada y corregida

Los tests HTTP aislados aprobaban la validación de origen, pero el primer recorrido de navegador devolvió 403 en un POST legítimo. La política `Referrer-Policy: no-referrer` podía producir origen nulo para formularios. Se cambió a `same-origin` y se repitió el flujo completo con éxito. Se mantuvo la comprobación de token y origen exacto: no se aceptan `null` o peticiones de sitios ajenos como excepción. Referencia técnica: [Origin y políticas de referencia](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin).

## Límites del resultado

El enrolamiento final del autenticador que usará el operador no se ha realizado: requiere sus contraseñas elegidas y su autenticador local. El CLI se ejercitó con entradas de terminal simuladas y base real temporal; no se afirma haber configurado una aplicación externa de autenticación. El flujo web con TOTP sí se ejecutó a través del proxy con datos de prueba aislados.

HTTP no cifra credenciales; HTTPS/TLS no está implementado. La prueba Secure comprueba la configuración de cookie, no un certificado ni TLS real. TOTP se almacena en archivo privado sin cifrado en reposo; el administrador del equipo/Docker queda fuera de esa protección. No hay recuperación de contraseña/TOTP, auditoría inmutable, autorización administrativa, ni ABAC de recursos. Los límites locales pueden bloquear temporalmente accesos legítimos repetidos. El análisis automático de accesibilidad no sustituye una evaluación completa.

P1 solo se acredita parcialmente para identidad/MFA y roles en paneles; no existen todavía publicar/descargar. P2–P10 permanecen pendientes. La clase 4 demuestra IAM, AAA, MFA, RBAC, verificación explícita y mínimo privilegio dentro de este alcance; no se presenta Zero Trust como despliegue empresarial completo. La etapa 2B no se inicia. PDF, historial y secretos fuera del repositorio conservados; sin commits o push.
