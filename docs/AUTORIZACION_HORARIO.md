# Autorización por atributos y control horario — etapa 2B

Etapa4: entrada HTTPS8443, con referencia y decisión horaria conservadas. Los comandos CMD siguientes mantienen su comportamiento. Regresión de07:59:59/08:00/sin asignación y entrega íntegra ejecutada por HTTPS. [Seguridad de red](SEGURIDAD_RED.md), [evidencia4](evidencias/etapa-04.md). Las URL HTTP históricas redirigen, sin acceso alternativo sensible.


Integración vigente: etapa 3 reutiliza esta política para documentos reales. Disponibilidad añade metadatos/estado del sobre; con archivo íntegro y autorización devuelve `descarga_habilitada: true`, y ante fallo criptográfico devuelve 409. Sin archivo conserva el comportamiento 2B. La consulta no envía bytes del examen; GET `/evaluaciones/{id}/documento` revalida y entrega después de GCM/SHA. [Detalle](CRIPTOGRAFIA_SOBRE.md). Los comandos siguientes se conservan. El botón actual se llama **Comprobar acceso**; las notas sin archivo describen el cierre histórico de 2B.

## Alcance y estado

Disponibilidad real de metadatos de evaluación según sesión vigente, rol, asignación y apertura completa en `America/Bogota`. Se conservan la autenticación, TOTP, cookies, CSRF y RBAC de [IDENTIDAD_ACCESO.md](IDENTIDAD_ACCESO.md). No hay carga, cifrado, comprobación de integridad ni descarga de archivos. La respuesta 200 de disponibilidad **no acredita una entrega de documento**.

La implementación utiliza la misma SQLite y el mismo volumen privado. No añade servicios Compose, dependencias o una segunda base. La migración es aditiva y no elimina cuentas, secretos, sesiones ni eventos de 2A. Los PDF originales permanecen intactos. Resultados observados: [evidencia 2B](evidencias/etapa-02b.md).

## Modelo y política

| Elemento | Almacenamiento / responsabilidad |
|---|---|
| Evaluación | `evaluaciones`: ID, título y fecha/hora de apertura con offset |
| Asignación | `asignaciones`: par evaluación/cuenta, con claves foráneas |
| Reloj del recurso | `reloj_evaluaciones`: una referencia fija ISO o NULL para modo normal |
| Decisión | `app/policy.py`: identidad → rol → asignación → apertura inclusiva |
| Auditoría | `eventos`: instante real de servidor, cuenta/acción/recurso/decisión/motivo y referencia didáctica independiente |

El caso local tiene ID `evaluacion-001`, título «Evaluación de laboratorio», y apertura a las 08:00 de la fecha indicada por el operador. Se asigna a la cuenta existente `estudiante`. No crea ni sustituye cuentas. La constante y el alta del caso están centralizadas en `app/demo.py`; la web solo consulta SQLite.

Orden de decisión para `GET /evaluaciones/{id}/disponibilidad`:

1. Sesión vigente y completa, comprobada con tiempo real: si falta, **401**.
2. Rol ESTUDIANTE en servidor: otro rol recibe **403**, aunque el docente tenga MFA válido.
3. Asignación persistida a esa cuenta para ese ID: si falta o el recurso es ajeno/inexistente, **403** sin metadatos.
4. Referencia horaria y apertura válidas: configuración ausente o corrupta deniega con **503**.
5. Referencia anterior a apertura: **403**, motivo `fuera_de_horario`.
6. Referencia igual o posterior: **200**, motivo `apertura_cumplida`, `autorizado: true` y `descarga_habilitada: false`.

Se comparan instantes completos conscientes de zona, no solo horas ni cadenas. 08:00:00 está incluido. Un instante UTC equivalente produce la misma decisión. No se establece fecha de cierre: una evaluación ya abierta continúa autorizada para su asignatario mientras la política no cambie. Todos los atributos decisivos proceden del servidor; parámetros de URL como `hora`, `apertura`, `cuenta_id` o `autorizado` no los reemplazan.

La función pura `decidir_disponibilidad` concentra las reglas; `consultar_disponibilidad` vuelve a consultar la sesión, lee datos/reloj en una transacción y audita. La siguiente etapa deberá reutilizar esta política y añadir descifrado/integridad **antes de enviar cualquier byte**. No basta reutilizar un 200 anterior: debe comprobarse otra vez en cada descarga futura.

## Reloj y autoridad administrativa

`app/clock.py` utiliza `zoneinfo.ZoneInfo('America/Bogota')` de Python y la base de zonas ya disponible en el contenedor. No se instalaron bibliotecas. El modo fijo es una **referencia detenida**, no avanza con el tiempo transcurrido. Persiste en SQLite al reiniciar o recrear servicios.

En modo normal se lee el instante real del servidor y se expresa en Bogotá. No se cambia Windows, Docker, el reloj del sistema, las fechas del autenticador ni la caducidad de las sesiones. `app/security.py` y `app/sessions.py` siguen usando tiempo real y no importan el reloj didáctico.

No hay endpoints administrativos de reloj o asignación. Solo un operador con acceso local a Docker puede ejecutar `app.demo` en el contenedor. Ni el rol docente ni el estudiante reciben controles de tiempo web. El propietario/administrador de Docker y SQLite queda fuera de la protección frente a modificación del almacenamiento; no se afirma aislamiento frente a ese administrador.

Si falta el registro de reloj en una instalación con evaluaciones, el arranque no lo recrea silenciosamente en modo normal. La consulta deniega; una acción explícita del operador debe restablecer la referencia. Esto evita que una recuperación implícita convierta el caso cerrado en abierto.

## Comandos reales en CMD

Servicios y cuentas de 2A ya inicializados. Desde la raíz del proyecto:

```bat
cd /d C:\Users\juanv\Proyectos\el-sobre-de-las-ocho
docker compose up -d --build --wait --wait-timeout 120
docker compose exec app python -m app.demo preparar --fecha 2026-11-09
docker compose exec app python -m app.demo reloj estado
start http://127.0.0.1:8080/acceso
```

`preparar` registra/actualiza únicamente `evaluacion-001`, restablece su asignación a `estudiante` y fija la referencia a **2026-11-09 07:59:59 -05:00**. Es el reinicio completo del caso, no borra cuentas, sesiones, contadores ni auditoría. Exige cuenta estudiante activa; si falta, seguir primero el procedimiento de alta de IDENTIDAD_ACCESO. Para otra fecha, cambiar explícitamente `--fecha` y las fechas de todos los comandos del recorrido.

Con la cuenta estudiante autenticada, abrir su panel y pulsar **Actualizar disponibilidad** después de cada cambio:

```bat
docker compose exec app python -m app.demo reloj fijar 2026-11-09T07:59:59
docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:00:00
docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:01:00
```

Esperado: **403 → 200 → 200**. Las fechas sin offset se interpretan en Bogotá; se aceptan también instantes ISO con offset explícito y se normalizan. La salida CLI indica modo, zona, tiempo didáctico y tiempo real. La sesión no se prolonga por adelantar o atrasar este reloj.

Para comprobar asignación, mantener las 08:01 y la misma sesión:

```bat
docker compose exec app python -m app.demo asignacion retirar
docker compose exec app python -m app.demo asignacion asignar
```

Actualizar disponibilidad tras cada comando: **403 por no asignada → 200**. Una recarga del panel sin asignación ya no lista esa evaluación. La URL directa con la misma sesión permite verificar el rechazo: `http://127.0.0.1:8080/evaluaciones/evaluacion-001/disponibilidad`. No abrirla sin sesión ni copiar cookies a argumentos: un cliente sin autenticación recibe 401. `--estudiante NOMBRE` permite seleccionar otra cuenta estudiante existente para el mismo caso; no crea usuarios.

### Restauración: dos operaciones distintas

```bat
docker compose exec app python -m app.demo reloj normal
docker compose exec app python -m app.demo reloj estado
```

Vuelve al tiempo real del servidor, que puede estar **después** de la apertura y autorizar legítimamente. No promete cerrar una evaluación. Para dejar la demostración **cerrada y repetible** con su asignación inicial:

```bat
docker compose exec app python -m app.demo preparar --fecha 2026-11-09
```

Vuelve a 07:59:59 y el mismo estudiante obtiene 403. Es el estado inicial/final documentado del ensayo. Reiniciar servicios no elimina esta referencia fija; no usar `down -v` como reinicio.

### Auditoría

```bat
docker compose exec app python -m app.demo auditoria --limite 20
```

Exporta únicamente decisiones de disponibilidad con campos explícitos: `tiempo_real` ISO en Bogotá, `usuario_id` (NULL para anónimo), `accion`, `evaluacion_id`, `decision`, `motivo` y `tiempo_didactico`. El origen almacenado real sigue siendo un epoch de servidor y la referencia didáctica es una cadena ISO con offset; son columnas distintas. Las decisiones anteriores a 2B conservan NULL en sus campos nuevos. Las operaciones administrativas se registran como `administracion_local`, sin atribuirlas a un usuario web.

No registra contraseñas, secretos/códigos TOTP, cookies, CSRF o cuerpos de solicitudes. Cada consulta por endpoint o panel genera una decisión actual; puede haber varios eventos por recargar y pulsar el control. Un fallo de escritura no habilita acceso. El comando de lectura admite 1–100 eventos y no vuelca tablas de identidad.

## Interfaz y verificación

El docente consulta la programación y el estudiante solo sus metadatos asignados. Los estados se renderizan con la política del servidor y pueden actualizarse mediante un GET real. El JavaScript no compara horas ni autoriza. Sin JavaScript, recargar el panel obtiene la decisión actual. El texto distingue acceso autorizado de descarga pendiente; no hay botón de descarga ni simulación de archivo entregado.

```bat
docker build --target test -t el-sobre-de-las-ocho-tests:etapa2b .
docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa2b
python scripts\verificar_etapa1.py
node scripts\verificar_interfaz.cjs
node scripts\verificar_identidad.cjs
```

El script de identidad ahora incluye horario, asignación, restauración, TOTP con reloj adelantado y auditoría. Usa el proyecto Compose efímero de pruebas en 8081, sin tocar credenciales del portal. Los datos principales se mantienen en el volumen original. Las pruebas crean otro estudiante **solo en una base temporal** para validar separación entre identidades. Resultados y límites de revisión en la ficha 2B; no se acredita entrega del original de P2 ni integridad P3.
