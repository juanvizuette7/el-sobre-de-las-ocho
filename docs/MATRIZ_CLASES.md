# Matriz de clases, aplicación y evidencia

## Etapa 4 — alcance vigente

| Concepto | Evidencia en el proyecto | Estado |
|---|---|---|
| HTTPS/TLS y certificados | `compose.yaml`, `infra/nginx/default.conf`, `app/certificates.py`, `scripts/verificar_red.py` | Implementado y verificado en `127.0.0.1:8443` |
| Redirección y cabeceras | Nginx y regresión HTTP/HTTPS | Implementado |
| Captura de comunicaciones | `scripts/capturar_portal.py`, Wireshark/Npcap | Tráfico TLS real del portal; sin secretos |
| Identidad, MFA, RBAC/ABAC y sesión | Aplicación y verificadores existentes | Conservado y regresado |
| Cifrado, integridad y descarga | AES-GCM, RSA-OAEP, SHA-256 y rutas protegidas | Conservado y regresado |
| Cisco Packet Tracer, NAC, ARP, VLAN, WLAN y RADIUS | Fuera del repositorio y del alcance final | No implementado ni acreditado |

La demostración de red se limita al sistema real y a Wireshark. Los PDF originales del profesor no se modifican.

## Etapa 5 — verificaciones y defensas

| Concepto | Evidencia en el proyecto | Estado |
|---|---|---|
| SQL Injection frente a consulta parametrizada | `scripts/demo_sql_injection.py`, SQLite en memoria y `tests/test_stage5.py` | Demostración aislada; consultas de aplicación revisadas y parametrizadas |
| Limitación de acceso y MFA | `app/sessions.py`, `app/auth.py`, `tests/test_auth.py` | Control existente reutilizado: 5 intentos por cuenta/ventana, 30 por origen; 429 y auditoría probados |
| Recuperación después de la ventana | `test_rate_limit_auditoria_y_recuperacion` | Probada con reloj inyectado, sin espera real ni cambios a la base del portal |
| Análisis estático Python | Bandit 1.9.4 sobre `app` y `scripts` | B608 esperado en el ejemplo vulnerable; B310 local justificado en verificadores |
| Imagen y configuración | Trivy 0.76.2 sobre dependencias e imagen | Sin registros críticos tras actualizar el digest de Debian 12 a Debian 13; severidad alta pendiente de seguimiento |
| Secretos y archivos privados | `.gitignore`, `git ls-files` y Trivy | Claves privadas, SQLite y capturas excluidas del índice |

No hubo actualizaciones masivas de dependencias. Ver [evidencia 5](evidencias/etapa-05.md) y [seguridad de aplicación](SEGURIDAD_ETAPA5.md). La etapa 6 permanece pendiente.
