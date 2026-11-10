# Seguridad de red y demostración TLS

La Etapa 4 se concentra en el portal real: Nginx termina HTTPS en `127.0.0.1:8443`, aplica TLS 1.2/1.3 y reenvía a FastAPI por la red privada de Docker. El puerto HTTP `8080` solo redirige a HTTPS. La CA local y el certificado SAN para `127.0.0.1`/`localhost` se generan con `scripts/preparar_https.cmd`.

No forman parte del alcance final los ejecutables o maquetas independientes de Cisco Packet Tracer, NAC, ARP, VLAN, WLAN o RADIUS. Se retiraron sus archivos; no se afirma que esos controles protejan el portal.

## Comprobar HTTPS en Windows

```powershell
cmd /c scripts\preparar_https.cmd
curl.exe --cacert certs\ca\ca.crt https://127.0.0.1:8443/health
python scripts\verificar_red.py
```

Abra `https://127.0.0.1:8443/acceso`; `8080` solo debe redirigir.

## Captura auténtica con Wireshark

La captura usa el loopback y el puerto real del portal. No envía contraseñas, TOTP, cookies ni documentos. Para generar tráfico público seguro:

```powershell
python scripts\capturar_portal.py
```

Para demostrar una consulta real de disponibilidad, use una sesión ya autenticada:

```powershell
python scripts\capturar_portal.py --esperar-disponibilidad
```

Mientras espera, abra `https://127.0.0.1:8443`, inicie sesión normalmente y pulse **Comprobar acceso**. Después presione Enter en PowerShell. En Wireshark seleccione `Npcap Loopback Adapter` y filtre:

```text
tcp.port == 8443
tls
tls.record.content_type == 23 || tls.record.opaque_type == 23
```

Se observan handshake, registros cifrados, IP/puerto, tamaños y tiempos; no el texto de credenciales, cookies o documentos. El archivo queda en `.qa/red/portal-8443.pcapng` y el resumen en `.qa/red/portal-8443-resultados.json`.

## Límites

La CA es local y de desarrollo. TLS protege el tránsito navegador–Nginx; AES-GCM, RSA-OAEP y SHA-256 protegen el examen. No se implementa la Etapa 5 ni controles empresariales de VPN, firewall, NAC o RADIUS.
