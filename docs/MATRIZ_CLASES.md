# Matriz de clases, aplicación y evidencia

## Etapa 4 — alcance vigente

| Concepto | Evidencia en el proyecto | Estado |
|---|---|---|
| HTTPS/TLS y certificados | `compose.yaml`, `infra/nginx/default.conf`, `app/certificates.py`, `scripts/verificar_red.py` | Implementado y verificado en `127.0.0.1:8443` |
| Redirección y cabeceras | Nginx y regresión HTTP/HTTPS | Implementado |
| Captura de comunicaciones | `scripts/capturar_portal.py`, Wireshark/Npcap | Preparada para tráfico real del portal; sin secretos |
| Identidad, MFA, RBAC/ABAC y sesión | Aplicación y verificadores existentes | Conservado y regresado |
| Cifrado, integridad y descarga | AES-GCM, RSA-OAEP, SHA-256 y rutas protegidas | Conservado y regresado |
| Cisco Packet Tracer, NAC, ARP, VLAN, WLAN y RADIUS | Fuera del repositorio y del alcance final | No implementado ni acreditado |

La demostración de red se limita al sistema real y a Wireshark. Los PDF originales del profesor no se modifican. La Etapa 5 no se inicia.
