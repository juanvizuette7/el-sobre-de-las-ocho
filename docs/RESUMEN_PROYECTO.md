# El sobre de las ocho: resumen del proyecto

Análisis inicial: 9 de noviembre de 2026. **Estado: diseño documentado; aplicación y laboratorios sin implementar ni verificar.** Este paso solo produce cinco documentos Markdown y `.gitignore`.

## Especificación y fuentes

La fuente principal es `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf` (7 páginas), leída completa. Las citas «F3, p. N» remiten al número físico de página, contando desde 1. El inventario de los diez PDF docentes, sus conceptos y las limitaciones de extracción están en [MATRIZ_CLASES.md](MATRIZ_CLASES.md). No se consultaron fuentes externas ni se instalaron dependencias.

La Fase 3 menciona antecedentes de fases 1 y 2 (p. 7), pero esos documentos no están en el inventario local. No se infiere su contenido. Las propuestas adicionales de esta documentación se identifican como tales y no sustituyen requisitos de F3.

## Objetivo y demostración

Construir un portal local para un parcial ficticio. Una sola persona usa una sesión docente y otra estudiante, por ejemplo ventana normal y privada del navegador. El profesor observa; no se necesita un segundo participante (F3, p. 1).

La demostración verificable consiste en rechazar la descarga a las 07:59:59, entregar exactamente el original desde las 08:00:00 inclusive y rechazar a esa misma hora una copia modificada. Se restaura el original y se repite. Cada decisión deja un motivo auditable. Apertura en una fecha del laboratorio y zona `America/Bogota` (F3, pp. 1, 3, 6–7).

## Alcance

Incluye un portátil Windows con Docker Desktop, dos cuentas ficticias, un parcial activo, una aplicación Python detrás de Nginx, SQLite, almacenamiento privado, controles locales de ensayo, una maqueta Packet Tracer, un modelo NAC en Python y una copia SQL vulnerable aislada. Herramientas gratuitas o educativas preparadas antes de presentar (F3, pp. 1–2).

Quedan fuera calificación de exámenes, personas o datos estudiantiles reales, despliegue público, pruebas en la red universitaria, SOC profesional y dependencia de terceros durante la presentación. No se añadirá un servidor de base de datos, infraestructura cloud ni una aplicación frontend independiente sin necesidad justificada (F3, pp. 1–2; esta última simplificación es propuesta).

## Requisitos y aceptación

| ID | Requisito | Criterio verificable | Fuente / pruebas |
|---|---|---|---|
| R01 | Publicación docente | Contraseña y TOTP local válido antes de publicar texto ficticio, asignarlo al estudiante y fijar fecha a las 08:00 de Bogotá. | F3 p. 1, p. 3 / P1 |
| R02 | Control en servidor | Cada petición, también por URL directa, valida sesión, rol, asignación y apertura; la interfaz no es la barrera de seguridad. | F3 pp. 1, 3 / P1, P2 y casos adicionales |
| R03 | Cifrado híbrido | AES-GCM cifra los bytes y RSA-OAEP protege la clave AES; privada RSA y secreto TOTP fuera de Git. Una biblioteca criptográfica realiza las operaciones. | F3 p. 3 / P3 y pruebas criptográficas |
| R04 | Integridad antes de entregar | SHA-256 del original queda como referencia protegida. Se descifra y compara antes de emitir cualquier byte del documento. Error de descifrado, archivo o referencia ausente bloquean. | F3 pp. 2–3 / P3 |
| R05 | Copia de ensayo | Una letra distinta, cifrado válido y huella original inalterada. Permite distinguir rechazo por hash de rechazo por autenticación GCM. Restauración reproducible. | F3 p. 3 / P3, P10 |
| R06 | Relojes separados | Solo el reloj de apertura avanza. Windows, TOTP y vigencia de las sesiones siguen su tiempo real. | F3 p. 3 / P2 y prueba adicional |
| R07 | Auditoría | Hora, cuenta ficticia o anónimo, acción y motivo en cada decisión. Nunca contraseña, OTP, claves ni contenido del parcial. Nginx registra el 429 que Python no recibe. | F3 pp. 1, 3 / P1–P10 |
| R08 | Acceso local y HTTPS | Solo Nginx publica el puerto de la aplicación en `127.0.0.1`; Python y sus volúmenes son privados. TLS, cabeceras y cuota por IP. | F3 pp. 2–3 / P4, P6, P9 |
| R09 | Contraseñas y descarga | Función de derivación con sal por cuenta; descarga sin caché. Las cuentas web no pueden reescribir la huella ni navegar al almacén. | F3 pp. 2–3 / P1, P3, comprobaciones adicionales |
| R10 | Laboratorios trazables | VLAN/WPA2/RADIUS, NAC, HTTP/HTTPS, SQL, análisis/parche, carga y ARP con fuentes, archivos futuros, pruebas y evidencias. Simulaciones identificadas. | F3 pp. 4, 6–7 / P4–P10 |
| R11 | Repetición autónoma | Restablecer copia y reloj; repetir la demo desde 07:59 dos veces; una ficha por clase y guion de 6–8 minutos. | F3 pp. 5, 7 / P10 |
| R12 | Calidad solicitada | Interfaz profesional, adaptable y accesible; errores claros, código mantenible, pruebas automáticas, documentación y guía Windows. Aceptación propuesta: teclado, foco visible, etiquetas, contraste legible, estados comprensibles sin depender del color, vista móvil y escritorio. | Petición actual; tareas en PLAN_IMPLEMENTACION |

### Orden contractual de decisión

Fuente: F3, p. 3. Comprobar en este orden; ningún rechazo entrega bytes del parcial.

| Condición | HTTP | Registro |
|---|---|---|
| Exceso de cuota por IP | 429 | Nginx, antes de Python |
| Sesión ausente o inválida | 401 | Aplicación, identidad no establecida |
| Rol o asignación incorrectos | 403 | Aplicación, permiso denegado |
| Fecha/hora anterior a apertura | 403 | Aplicación, fuera de horario |
| Apertura cumplida y copia alterada | 409 | Aplicación, fallo de integridad |
| Apertura cumplida y original íntegro | 200 | Aplicación, acceso permitido |

F3 no fija código para archivo/referencia ausente u otros errores internos: se exige denegación sin documento y evento. La propuesta es 409 para incoherencia del sobre y 503 para indisponibilidad del almacenamiento; se precisará antes de implementar esos casos, sin cambiar los códigos anteriores.

## Catálogo fiel de pruebas P1–P10

Todos los resultados siguientes son **esperados, no observados**. Fuente: F3 pp. 6–7. El plan contiene las tareas para ejecutarlos.

| Caso | Procedimiento reproducible previsto | Aceptación y evidencia por guardar |
|---|---|---|
| P1 Identidad | Sin sesión descargar; estudiante intenta publicar; docente prueba OTP incorrecto y válido. | 401; 403; acceso docente solo con segundo factor válido. Respuestas y eventos saneados. |
| P2 Hora límite | Misma cuenta, fecha, asignación y original; reloj de ensayo 07:59:59 y 08:00:00; Windows intacto. | 403 sin documento y 200 con bytes iguales al original. Bitácora y huellas. |
| P3 Integridad | A las 08:00 seleccionar copia alterada válidamente cifrada, descargar y restaurar original. | Huellas distintas, 409 sin documento, luego 200. Hashes y eventos; probar aparte tag GCM corrupto. |
| P4 Tráfico | Misma marca ficticia por HTTP de ensayo y HTTPS del portal; captura sin claves de sesión. | Marca reconstruible en HTTP; payload cifrado en HTTPS; IP, puerto y SYN/SYN-ACK/ACK identificados. Dos flujos. |
| P5 Red e identidad | Packet Tracer antes/después de VLAN; RADIUS válido/inválido; modelo Python con dispositivo docente no verificado. | Tráfico autorizado permitido; administración de alumnos bloqueada; identidad/estado indebidos rechazados. `.pkt`, configuración saneada y salida NAC por separado. |
| P6 Configuración web | Consultar cabeceras y cargar iframe desde otro origen local de ensayo. | `SAMEORIGIN`, `nosniff`, sin número de versión y bloqueo del iframe. Cabeceras, consola/captura del navegador. |
| P7 Inyección SQL | Solo copia aislada: Nmap/NSE, reproducción manual y repetición tras parametrizar consulta. | Acceso indebido antes; intento rechazado y credencial válida aceptada después. Informes y respuestas. Puerto abierto no acredita SQLi. |
| P8 Análisis y parche | CVE corregible de imagen/dependencia de ensayo; Bandit y Trivy antes/después; misma base de vulnerabilidades. | Hallazgo HIGH/CRITICAL bloquea promoción. Seguir CVE y versión corregida; promover solo con todos los controles aprobados. Informes, versiones, base utilizada y códigos de salida. |
| P9 Ráfaga local | Cliente Docker autenticado, máximo 100 peticiones y concurrencia 5; cliente válido de IP distinta en paralelo. Repetir con 5 solicitudes/s/IP y ráfaga 5. | Medir latencia, CPU, códigos y porcentaje real de rechazo. Con cuota se esperan 429 para exceso y 200 para alumno autorizado. Logs acreditan IP distintas. |
| P10 Intercepción y reinicio | Dibujar ARP normal/alterado; restaurar copia y reloj; repetir P2 y P3. | Explicar desvío simulado y obtener iguales decisiones con iguales condiciones. Tablas, registro de restauración y dos ejecuciones. |

## Estado, incertidumbres y lectura posterior

No se ejecutaron P1–P10: no existe aún aplicación. Tampoco se han verificado Docker, herramientas, puertos, certificados ni recursos del equipo. No se eligió un CVE ni se inventaron métricas. El flujo local DevSecOps y el límite de carga de F3 prevalecen sobre los ejemplos docentes más amplios.

La Fase 3 estima 30–40 h, aunque sus seis intervalos suman 30–40 h para construcción y ensayo; el informe extenso y diapositivas corresponden a la **fase académica 5**, diferente de la etapa de construcción 5 (F3 p. 5).

Los PDF locales ya están rastreados por Git. `.gitignore` no los retira del índice ni del historial; esta tarea no cambia el índice, borra originales ni publica archivos. Antes de compartir el repositorio será necesario resolver la autorización de distribución y la permanencia de esos materiales.

Continuar con [ARQUITECTURA.md](ARQUITECTURA.md), [PLAN_IMPLEMENTACION.md](PLAN_IMPLEMENTACION.md) y [GUIA_ESTUDIANTE.md](GUIA_ESTUDIANTE.md). No se inicia programación en este paso; el siguiente requiere autorización y se ejecutará paso a paso con comprobación del usuario (F3 p. 5).
