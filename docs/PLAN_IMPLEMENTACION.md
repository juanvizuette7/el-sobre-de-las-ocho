# Plan de implementación

## Estado vigente de etapa 4

1. HTTPS/TLS 1.2/1.3, CA local, SAN, Nginx y redirección HTTP están implementados.
2. Cookies seguras, cabeceras y comprobaciones de infraestructura están verificadas.
3. La captura Wireshark se realiza sobre el portal real en `127.0.0.1:8443` mediante `scripts/capturar_portal.py`.
4. La aplicación conserva autenticación, MFA, RBAC/ABAC, reloj, cifrado, integridad y descarga.

Cisco Packet Tracer y los ejecutables independientes NAC/ARP fueron retirados por quedar fuera del alcance acordado. No se afirma implementación de VLAN, WLAN, RADIUS, NAC o ARP. La Etapa 5 no se inicia.

## Verificación

```powershell
python scripts\verificar_red.py
python scripts\verificar_etapa1.py
python scripts\capturar_portal.py
docker compose ps
```

La matriz y la evidencia detallan los resultados sin modificar los PDF originales ni hacer commits/push.
