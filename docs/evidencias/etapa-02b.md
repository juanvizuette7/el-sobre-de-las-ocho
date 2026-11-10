# Evidencia de etapa 2B — disponibilidad por asignación y horario

Fecha local de referencia: 9 de noviembre de 2026, America/Bogota. Modalidad: implementación real sobre metadatos, no entrega de documentos. Fuentes: F3 pp. 1–3, 5–6; clase 4, `Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf`, pp. 4–7 y 15. Se utilizó la documentación existente sin reprocesar PDF. No se hicieron commits ni push; la ejecución corresponde al árbol de trabajo entregado.

## Condiciones y procedimiento

Se conservaron los dos servicios Compose, puerto exclusivo 127.0.0.1:8080, FastAPI no publicado, red interna y volumen SQLite privado. No se añadieron dependencias; America/Bogota estaba disponible mediante ZoneInfo en el contenedor Python 3.12.16. El sistema principal ya tenía una cuenta por rol; no se leyeron contraseñas ni secreto TOTP y no se modificaron identidades para verificar 2B.

El caso principal se preparó mediante `docker compose exec -T app python -m app.demo preparar --fecha 2026-11-09`: metadatos de evaluacion-001, apertura 08:00:00-05:00, asignación al estudiante existente y referencia fija 07:59:59-05:00. Se comprobó el estado antes y después de `docker compose restart` y de una recreación de aplicación: la referencia permaneció cerrada. La salida distinguió tiempo didáctico 07:59:59 de hora real del servidor (23:28 en el registro de ese ensayo); no se cambió el sistema operativo.

Para pruebas de autenticación y disponibilidad se utilizó el proyecto efímero **sobre-identidad-qa**, solo 127.0.0.1:8081, con cuentas aleatorias y datos en tmpfs. Se ejecutaron los formularios reales a través de Nginx, no respuestas de autorización interceptadas. Los comandos de reloj/asignación operaron dentro de ese proyecto, sin usar contraseñas del portal principal. Se retiraron contenedores/redes temporales al terminar.

Comandos reproducibles de operación y pruebas: [AUTORIZACION_HORARIO.md](../AUTORIZACION_HORARIO.md). Scripts: `scripts/verificar_identidad.cjs`, `scripts/verificar_interfaz.cjs`, `scripts/verificar_etapa1.py`. La suite usa `tests/test_availability.py` y conserva los 40 casos anteriores de 2A.

## Resultados reales

| Comprobación | Resultado esperado | Resultado observado |
|---|---|---|
| Toda la suite, contenedor sin red, raíz de solo lectura y /tmp temporal | Regresión de 2A y reglas 2B aprobadas | **66 passed in 40.05s**: 40 casos anteriores y 26 casos de 2B |
| Regresión de portada con los recursos finales montados en solo lectura | Mantener contratos públicos después del ajuste textual de la ilustración | **9 passed in 2.11s**; repetición dirigida, no nueve funcionalidades adicionales |
| Estudiante asignado 07:59:59 | 403, fuera de horario | 403 en pytest y navegador por Nginx |
| Mismo estudiante a 08:00:00 y 08:01:00 | 200 inclusivo, sin archivo | 200 en ambos instantes; autorizado verdadero, descarga_habilitada falso, sin Content-Disposition |
| Fecha anterior / instante UTC equivalente | Comparar fecha completa y zona, no solo hora | Día anterior denegado; 12:59:59 UTC denegado y 13:00:00 UTC autorizado para apertura 08:00 Bogotá |
| Otro estudiante temporal no asignado | 403 aun después de apertura | 403; sin título ni metadatos del recurso ajeno en su panel |
| Retirar/reasignar con la misma sesión | Rechazo inmediato / aceptación | 403 al retirar a las 08:01, 200 al reasignar; token no cambia |
| Usuario sin sesión o sesión vencida | 401 | 401; adelantar/atrasar reloj del recurso no recupera una sesión vencida |
| Docente con contraseña, sin MFA | Sin panel ni disponibilidad de estudiante | 401; TOTP actual aceptado después de fijar reloj de evaluaciones en 2035 |
| Roles existentes | Estudiante no entra a docente y docente conserva su panel | 403 por URL docente para estudiante; panel docente 200 tras MFA; consulta como estudiante 403 para docente |
| Estudiante intentando cambiar el reloj por HTTP | Ninguna modificación | POST a rutas de reloj inexistentes → 404; POST al endpoint de consulta → 405; referencia intacta |
| Hora/asignación/rol inventados en query | Ignorar atributos del navegador | 403 por política real, sin apertura por parámetros |
| Sesiones y TOTP frente al reloj didáctico | Tiempo de identidad independiente | Desafío conserva sus campos creada/vence; MFA acepta código real; sesiones completas duran 1800 segundos reales; vencidas siguen denegadas incluso con referencia en 2000 |
| Reiniciar/recrear servicios | No perder restricción configurada | Referencia fija 07:59:59 antes y después del reinicio real; nueva factoría con misma DB continúa en 403 |
| Configuración corrupta o reloj perdido | Denegación, sin apertura implícita | 503 para asignatario; anónimo sigue 401; arranque con evaluaciones y reloj ausente no lo recrea en modo normal |
| Restaurar modo normal | Leer tiempo real | Se comprobó modo normal y retorno al proveedor real; no se afirma que quede cerrado si ya pasó la apertura |
| Restablecer ensayo mediante preparar | Asignación original y referencia 07:59:59 | Tras 200, preparar vuelve a producir 403; conserva sesiones y bitácora |
| Migración 2A→2B | Aditiva e idempotente | Evento anterior conserva datos; campos nuevos NULL; repetir inicialización no elimina datos |
| Auditoría real | Cuenta, acción, recurso, resultado y dos tiempos | Comprobados motivos fuera_de_horario, apertura_cumplida y evaluacion_no_asignada; cuenta e ID de evaluación presentes; tiempo real separado de referencia didáctica |
| Exportación CLI de auditoría | Solo campos de disponibilidad, sin datos sensibles | Límite probado, selección explícita; claves, TOTP y cookies ausentes en pruebas y logs del recorrido |
| Infraestructura tras cambios | Mantener etapa 1 operativa | 27 comprobaciones aprobadas; Nginx válido con nginx -t; ambos servicios saludables y Python sin puerto publicado |
| Portada, cuatro anchos | Sin regresión de interfaz | 1440/768/390/320 px: HTTP 200, sin desbordamiento, teclado/anclas, salud, errores/timeout, movimiento reducido y modo sin JS aprobados |
| Paneles/asignación escritorio y móvil | Estado real legible y operación disponible | Capturas 1440/390 revisadas; actualización obtiene respuestas reales del endpoint; sin excepciones JavaScript ni infracciones automáticas axe A/AA en vistas analizadas |

El primer recorrido de portada coincidió con el reinicio controlado y recibió una conexión interrumpida; el verificador de salud también observó el estado transitorio. Se repitieron ambas comprobaciones después de esperar servicios saludables y aprobaron. Esto se registra como interferencia del procedimiento de prueba; no se ocultó un resultado fallido ni se modificó el producto para ignorarlo.

Artefactos locales no publicados: `.qa/identidad-resultados.txt`, `.qa/interfaz-resultados.txt` y capturas de paneles/acceso en `.qa/capturas/`. Las capturas no incluyen campos de contraseña/OTP rellenados, secretos de enrolamiento o cookies. Los IDs y nombres de cuentas del ensayo son ficticios.

## Estado de entrega y límites

Se deja el caso principal **asignado a estudiante y cerrado**: fecha 2026-11-09, apertura 08:00 y reloj fijo 07:59:59 de Bogotá. La autenticación y la caducidad siguen dependiendo del tiempo real. La modificación de metadatos o reloj requiere acceso administrativo local a Docker; no se protege frente al dueño/administrador del volumen. La bitácora no es inmutable.

Un 200 de disponibilidad no entrega el examen, no verifica bytes y no acredita AES/RSA/SHA-256 del archivo. P2 solo tiene cobertura de decisión horaria; su entrega del original permanece para etapa 3. P3 y los laboratorios siguen pendientes. HTTP local/TLS pendiente conserva las limitaciones de 2A. La revisión automática de accesibilidad no certifica compatibilidad completa con todos los navegadores o tecnologías de asistencia.

Clase 4: se demuestra la separación autenticación/autorización, IAM, AAA, RBAC, ABAC de disponibilidad, verificación explícita y mínimo privilegio en estas rutas. No se afirma una arquitectura Zero Trust empresarial completa. La matriz documenta fuente/página, función y prueba; la guía privada contiene las explicaciones de estudio. No se avanza a etapa 3.
