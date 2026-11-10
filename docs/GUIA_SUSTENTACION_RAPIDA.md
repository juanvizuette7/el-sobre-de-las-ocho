# Guía rápida de sustentación

En CMD, desde la carpeta del proyecto. Usa las cuentas ficticias existentes. No ejecutes `inicializar` si ya existen.

1. **Iniciar:** `docker compose up -d --wait --wait-timeout 120` → abre `https://127.0.0.1:8443/acceso`.
2. **Identidad y permisos:** inicia sesión como estudiante y luego docente en ventanas separadas; muestra TOTP docente y acceso denegado del estudiante a una ruta docente.
3. **Horario:** `docker compose exec app python -m app.demo reloj fijar 2026-11-09T07:59:59` → estudiante, **Comprobar acceso**: bloqueado. `docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:00:00` → consultar de nuevo: autorizado. La asignación también debe cumplirse.
4. **Publicar y descargar:** docente, publica un TXT ficticio desde la tarjeta de evaluación; estudiante autorizado, descarga desde su portal.
5. **Alteración GCM:** `docker compose exec app python -m app.demo sobre alterar-gcm` → intenta descargar (409). Restaura con `docker compose exec app python -m app.demo sobre restaurar`.
6. **Alteración SHA-256:** `docker compose exec app python -m app.demo sobre alterar-hash` → intenta descargar (409). Restaura con `docker compose exec app python -m app.demo sobre restaurar`.
7. **HTTPS/Wireshark:** `python scripts\capturar_portal.py` → el script solicita solo rutas públicas por 8443; en Wireshark usa el filtro `tcp.port == 8443`. No captures formularios ni documentos.
8. **SQL Injection aislada:** `python scripts\demo_sql_injection.py` → compara la consulta vulnerable y la parametrizada en SQLite en memoria.
9. **429 y auditoría del límite:** `docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa5-zlib python -m pytest -q -p no:cacheprovider tests/test_auth.py::test_rate_limit_auditoria_y_recuperacion` → muestra 429, evento y recuperación en datos temporales; no bloquea la cuenta real.
10. **Auditoría:** `docker compose exec app python -m app.demo auditoria --limite 20` → muestra eventos sin credenciales ni OTP.
11. **Resultados:** abre `docs/evidencias/etapa-06.md` y `docs/SEGURIDAD_ETAPA5.md`; Trivy mantiene 47 hallazgos High.

Los comandos de reloj y alteración cambian el estado persistente del ensayo; sigue los pasos de restauración antes de cerrar. No uses `docker compose down -v`. No se requiere regenerar certificados ni inicializar cuentas.
