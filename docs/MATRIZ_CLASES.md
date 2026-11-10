# Matriz de las diez clases

La matriz relaciona los conceptos identificados en el inventario docente ya existente con el alcance real del proyecto, sus archivos y verificaciones. Se actualizó la trazabilidad sin volver a procesar los PDF. «No implementado» significa que no debe presentarse como función del portal.

| Clase y conceptos | Fuente | Aplicación y archivos | Prueba o evidencia real | Estado y límite para sustentar |
|---|---|---|---|---|
| **1. Criptografía:** AES, cifrado simétrico, RSA y clave pública/privada, hash y diferencia entre cifrar y resumir | C1, pp. 7, 9–13; F3, pp. 2–3 | AES-256-GCM cifra el examen; RSA-OAEP-SHA256 protege la llave AES; SHA-256 verifica el original. `app/crypto.py`, `app/documents.py`, `app/storage.py` | `tests/test_crypto.py`, `tests/test_documents.py`; recorrido de navegador descargó bytes idénticos y rechazó alteraciones | **Implementado.** SHA-256 detecta diferencias frente a la referencia protegida; no cifra. Se usa GCM/OAEP/SHA-256, no se afirma usar el ejercicio AES-CBC/MD5 del taller. |
| **2. Comunicaciones:** OSI/TCP-IP, IP, puertos, TCP, HTTP/HTTPS, TLS, inspección de tráfico, firewall y VPN | C2, pp. 3–19; F3, p. 4 | Nginx publica HTTPS local en 8443; FastAPI queda en red privada. `compose.yaml`, `infra/nginx/`, `scripts/verificar_red.py`, `scripts/capturar_portal.py` | 22 comprobaciones de TLS/red; Wireshark capturó el portal real en 8443: GET públicos 200 y 15 registros TLS | **Parcial, implementado y verificado:** TCP/TLS/HTTP(S) y metadatos de captura. No se despliega VPN ni firewall de red empresarial. La captura no incluye credenciales ni contenido privado. |
| **3. Redes inalámbricas:** LAN, VLAN, WEP/WPA/WPA2/WPA3, personal/enterprise y topología Packet Tracer | C3, pp. 5–14; F3, p. 4 | Ninguna implementación inalámbrica. La red privada Docker no es una WLAN ni una VLAN del curso. | No hay prueba ni evidencia de Packet Tracer en el alcance actual. | **No implementado.** No afirmar que el portal configure Wi-Fi, VLAN o WPA. |
| **4. Identidad y acceso:** IAM, AAA, MFA/TOTP, sal y derivación, RBAC, ABAC, mínimo privilegio, Zero Trust, RADIUS/TACACS+ | C4, pp. 2, 4–8, 15; F3, pp. 1–3 | Argon2id, sesiones, TOTP docente, roles y atributos de asignación/horario. `app/auth.py`, `app/security.py`, `app/sessions.py`, `app/policy.py`, `app/clock.py`, `app/audit.py` | `tests/test_auth.py`, `tests/test_availability.py` y recorrido integrado de navegador: TOTP, 401/403, asignación y auditoría | **IAM/AAA/MFA/RBAC/ABAC implementados.** No se despliega RADIUS/TACACS+ ni una arquitectura empresarial Zero Trust. |
| **5. Bastionado web:** configuración segura, banners, OWASP A05, clickjacking y MIME sniffing | C5, pp. 3–4, 6–8, 12–15 | Nginx oculta versión, añade cabeceras, limita orígenes y termina TLS. `infra/nginx/default.conf`, `infra/nginx/nginx.conf` | `scripts/verificar_red.py` (22 comprobaciones) y `scripts/verificar_etapa1.py` (27); banner, `nosniff`, `SAMEORIGIN`, TLS y rutas verificadas | **Implementado y verificado** en la configuración local. Las cabeceras reducen riesgos concretos; no sustituyen parchear software. |
| **6. NAC y cortafuegos:** postura del dispositivo, zonas, herencia/default deny, con/sin estado, DMZ y capas 3/4/7 | C6, pp. 4–18; C2, p. 12; F3, pp. 4, 6 | No hay motor NAC. La separación existente es de servicios Docker y privilegios: `compose.yaml`, `Dockerfile` | `scripts/verificar_etapa1.py` comprueba red interna, puertos publicados, usuario no root y sistemas de archivos de solo lectura | **NAC y firewall stateful no implementados.** La prueba acredita aislamiento Docker básico, no filtrado por postura, zonas ni inspección de paquetes. |
| **7. DevSecOps:** Docker, pruebas, CI/CD, SAST/SCA, CVE, Trivy, infraestructura como código y cloud | C7, pp. 4–7, 11–22; F3, pp. 2, 4 | Docker/Compose fijados; pytest, Bandit y Trivy locales. `Dockerfile`, `compose.yaml`, `requirements*.txt`, `tests/`, `docs/SEGURIDAD_ETAPA5.md` | Suite: **129 aprobadas**. Bandit: 0 High, un B608 Medium intencional. Trivy: **47 High** en imagen Debian actual; no se ocultan. | **Controles locales implementados.** No hay despliegue cloud ni GitHub Actions. La imagen no está libre de vulnerabilidades; consultar los hallazgos y riesgos residuales en seguridad Etapa 5. |
| **8. Pruebas de seguridad:** reconocimiento/pentest, Nmap/NSE, SQL Injection y falsos negativos | C8, pp. 4–21; F3, p. 7 | Demostración SQLi separada, SQLite `:memory:` y datos ficticios. `scripts/demo_sql_injection.py`, `tests/test_stage5.py`; consultas reales parametrizadas en `app/` | `python scripts/demo_sql_injection.py`: la consulta insegura devuelve dos filas; la parametrizada, cero. Pruebas automatizadas y revisión de SQL del portal | **SQLi educativa aislada, implementada y probada.** No se escanea ni ataca el login o la base real; Nmap/NSE y pentest no se implementan. |
| **9. Disponibilidad e intercepción:** DoS/DDoS, botnets, MITM y ARP | C9, pp. 4–16; F3, p. 7 | No hay generador de carga, botnet, envenenamiento ARP ni simulador MITM. TLS real está en `scripts/capturar_portal.py` | Captura de TLS real en 8443; no demuestra defensa frente a DDoS ni experimento ARP. No se ejecutó carga de hasta 100 solicitudes | **No implementado**, salvo controles de tasa de la clase 10 y protección TLS del portal. No afirmar que se probó DDoS, MITM o ARP spoofing. |
| **10. Defensa:** controles preventivos/detectivos/correctivos, limitación de tasa, parche y reducción de superficie | Material complementario B, pp. 3–18; C7, pp. 13, 21; F3, pp. 3–4, 7 | Límite en autenticación, auditoría, contenedores mínimos y parche puntual de zlib. `app/sessions.py`, `app/auth.py`, `app/audit.py`, `Dockerfile` | `test_rate_limit_auditoria_y_recuperacion`: 429 al sexto fallo, evento auditado y recuperación. Imagen: zlib corregida; Trivy mantiene 47 High | **Parcial e implementado:** control de acceso y parche disponible. No se simula carga de red; 47 High quedan pendientes de seguimiento, incluidas tres CVE de SQLite sin parche estable indicado. |

## Inventario docente de referencia

Los códigos C1–C9 y B preservan los nombres y páginas del inventario previo. B es el material complementario de la clase 10; no se cuenta como un undécimo curso.

| Código | Documento previamente inventariado |
|---|---|
| C1 | `Semana 1 comunicación y seguridad informatica (martes 1ro de septiembre) CORRECTA.pdf` |
| C2 | `Semana 2 8 de septiembre Sistemas-de-Comunicacion-y-Seguridad-Informatica.pdf` |
| C3 | `Semana 3 seguridad y comunicación 15-09-2026.pdf` |
| C4 | `Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf` |
| C5 | `Semana-5 Sesión 29 septiembre Sistemas-de-Comunicacion-y-Seguridad-Informatica.pdf` |
| C6 | `Semana 6 06-10-2026 Semana-6-Fundamentos-de-NAC-y-Cortafuegos.pdf` |
| C7 | `Sesión 7 Sistemas-de-Comunicacion-y-Seguridad-Informatica 13 octubre 2026.pdf` |
| C8 | `Sesión 8 20 octu Sistemas-de-Comunicacion-y-Seguridad-Informatica Pentesting y SQL Injectión.pdf` |
| C9 | `Sesión 9 y 10- Sistemas-de-Comunicacion-y-Seguridad-Informatica (27-10-2026).pdf` |
| B | `Bastionado como mitigación de riesgos 03-11-2026 Sistemas-de-Comunicacion-y-Seguridad-Informatica.pdf` |

## Verificaciones asociadas

- `docker run --rm --network none --read-only --tmpfs /tmp el-sobre-de-las-ocho-tests:etapa5-zlib` — suite completa.
- `python scripts/verificar_red.py` — TLS, HTTPS, redirección y cabeceras.
- `python scripts/verificar_etapa1.py` — Docker, exposición, redes y salud.
- `node scripts/verificar_identidad.cjs` — recorrido integrado; para cliente Node usar `set "NODE_EXTRA_CA_CERTS=%CD%\certs\ca\ca.crt"`. La guía de Etapa 6 registra el resultado final respetando los volúmenes de prueba.
- `node scripts/verificar_interfaz.cjs` — escritorio, móvil, teclado, accesibilidad automática y errores/timeout.
- `python scripts/capturar_portal.py` — Wireshark real del portal en 8443, solo rutas públicas.

Resultados finales: [evidencia de Etapa 6](evidencias/etapa-06.md). Las evidencias históricas de [Etapa 1](evidencias/etapa-01.md), [2A](evidencias/etapa-02a.md), [2B](evidencias/etapa-02b.md), [3](evidencias/etapa-03.md), [4](evidencias/etapa-04.md) y [5](evidencias/etapa-05.md) conservan los resultados y límites de cada etapa.
