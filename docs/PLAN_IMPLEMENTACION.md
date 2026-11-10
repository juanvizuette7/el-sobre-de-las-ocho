# Plan de implementación

## Estado vigente de etapa 4

1. HTTPS/TLS 1.2/1.3, CA local, SAN, Nginx y redirección HTTP están implementados.
2. Cookies seguras, cabeceras y comprobaciones de infraestructura están verificadas.
3. La captura Wireshark se realiza sobre el portal real en `127.0.0.1:8443` mediante `scripts/capturar_portal.py`.
4. La aplicación conserva autenticación, MFA, RBAC/ABAC, reloj, cifrado, integridad y descarga.

Cisco Packet Tracer y los ejecutables independientes NAC/ARP fueron retirados por quedar fuera del alcance acordado. No se afirma implementación de VLAN, WLAN, RADIUS, NAC o ARP. Los PDF originales se conservan.

## Estado vigente de etapa 5

La demostración SQL Injection opera en SQLite `:memory:` con datos ficticios; las pruebas confirman que la cadena altera la consulta concatenada y queda como dato en la consulta parametrizada. Las consultas del portal usan parámetros.

El acceso y TOTP reutilizan el contador persistente existente en SQLite. Se validan 5 fallos por cuenta, respuesta 429 al exceder, evento de auditoría sin secretos y recuperación después de una ventana de 300 segundos. No se limitan las rutas del examen ni se agrega middleware duplicado.

La validación final suma 129 pruebas automatizadas; TLS/red: 22 comprobaciones; infraestructura: 27. El navegador confirmó login/TOTP, RBAC/ABAC, límites del reloj, publicación, descarga e integridad. Bandit informa B608 en el ejercicio vulnerable intencional. Trivy mantiene 47 hallazgos High en la imagen Debian actual y 0 Critical; no se ocultan ni se afirma que la imagen esté libre de vulnerabilidades. La Etapa 6 cerró la regresión y la documentación, sin añadir funciones; ver [evidencia](evidencias/etapa-06.md).
