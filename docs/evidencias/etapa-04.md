# Evidencia de etapa 4 — HTTPS y tráfico del portal

Fecha: 10 de noviembre de 2026, America/Bogota. Se conservaron la base principal, cuentas, TOTP, sobres, asignaciones y referencia horaria. No se hicieron commits, push ni cambios de etapa 5.

## Alcance final

| Área | Resultado |
|---|---|
| Nginx, HTTPS, TLS 1.2/1.3, CA local, SAN y redirección HTTP | Implementación real verificada |
| Cookies Secure/HttpOnly, cabeceras y recursos del mismo origen | Verificado |
| Autenticación, MFA, RBAC/ABAC, reloj, cifrado, integridad y descarga | Conservados y regresionados por HTTPS en QA aislado |
| Wireshark/dumpcap en `127.0.0.1:8443` | Procedimiento preparado para tráfico real del portal; no captura secretos |
| Cisco Packet Tracer, NAC, ARP, VLAN, WLAN y RADIUS | Fuera del alcance final; archivos independientes retirados |

La captura verificada generó únicamente `GET /health` y `GET /acceso` sin cookies: ambas respuestas fueron 200 y tshark identificó 15 registros TLS en el puerto 8443. Con `--esperar-disponibilidad`, el operador puede iniciar sesión en el navegador y pulsar **Comprobar acceso** mientras dumpcap captura el puerto 8443; esa interacción manual no se repitió en esta comprobación. El script no lee ni imprime credenciales, TOTP, cookies o documentos.

## Comandos ejecutados

```text
python scripts/verificar_red.py        -> 22 comprobaciones correctas
python scripts/verificar_etapa1.py    -> 27 comprobaciones correctas
python scripts/capturar_portal.py     -> captura loopback 8443 y resumen JSON
```

La suite pytest se ejecuta después de reconstruir la imagen de pruebas. La revisión visual de escritorio y móvil y el recorrido de identidad/etapa 3 se mantienen en sus verificadores existentes.

## Límites

La CA es de desarrollo y el tráfico interno Nginx–FastAPI no se presenta como cifrado extremo a extremo. La captura permite observar metadatos y registros TLS, no el contenido de aplicación. No se afirma implementación de controles empresariales de red ni avance a etapa 5.
