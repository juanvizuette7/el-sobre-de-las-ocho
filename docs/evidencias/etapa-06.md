# Evidencia de Etapa 6 — validación final

**Alcance:** regresión y preparación de sustentación. No se añadieron funcionalidades ni se modificó la arquitectura. Se conservaron los datos, cuentas, certificados y volumen principal. Los materiales fuera de alcance (Cisco Packet Tracer y laboratorios NAC/ARP independientes) no se presentan como implementados.

## Resultados

| Verificación | Resultado |
|---|---|
| Suite pytest existente | **129 aprobadas** (imagen de pruebas etiquetada `etapa5-zlib`, 96,79 s). |
| Infraestructura Docker | **27 comprobaciones aprobadas**: dos servicios, salud, red privada, puertos, usuario no root y sistemas de archivos de solo lectura. |
| TLS y red | **22 comprobaciones aprobadas**: HTTPS, TLS 1.2/1.3, CA/SAN, rechazo de protocolos antiguos, redirección y cabeceras. |
| Navegador e interfaz | **1440, 768, 390 y 320 px**; verificaciones de accesibilidad A/AA, teclado, salud real, errores/timeout y consola sin fallos. |
| Recorrido integrado | Login y cierre, TOTP docente, 401/403, ABAC horario/asignación, publicación, descarga byte a byte, alteraciones GCM y SHA-256 rechazadas (409), restauración y auditoría. Límites exactos **07:59:59 → 403** y **08:00:00 → 200** con las demás reglas satisfechas. |
| Docker Compose actual | `app` y `nginx` en estado **healthy**; FastAPI sin puerto publicado y HTTPS local en `127.0.0.1:8443`. Se conservó el volumen principal. |
| Wireshark | Captura real `.qa/red/portal-8443.pcapng`: GET públicos `/health` y `/acceso` con 200; **15 registros TLS** en 8443, sin credenciales, OTP, cookies ni documentos. |
| SQL Injection | Demostración aislada: consulta concatenada devuelve dos filas ficticias; parametrizada, cero; SQLite en memoria. |
| Bandit | 0 High; un B608 Medium esperado en la demostración SQLi intencional, además de 14 hallazgos Low. El código de salida distinto de cero corresponde a ese hallazgo. |
| Trivy | No se repitió el escaneo sin cambios que lo justifiquen. Informe vigente: **47 High, 0 Critical** en paquetes Debian; incluye tres registros de `libsqlite3-0`. Ver clasificación, disponibilidad de corrección y riesgo residual en [Seguridad Etapa 5](../SEGURIDAD_ETAPA5.md). |
| Archivos sensibles | No se encontraron claves privadas, base SQLite ni secretos TOTP en el índice Git. Certificados privados, datos y `.qa` están excluidos por `.gitignore`; la aplicación conserva SQLite y claves en el volumen Docker local. |

La integración de navegador usa la CA pública local mediante `NODE_EXTRA_CA_CERTS`; se adaptó la copia de QA para que `docker compose down` no eliminara volúmenes. Las fallas de configuración del cliente durante la preparación no fueron fallos de la aplicación. La verificación de errores/timeout se ejecutó con el verificador de interfaz. Las ejecuciones de identidad dejaron volúmenes de QA nombrados; no se borraron.

## Documentación de cierre

- [Guía rápida de sustentación](../GUIA_SUSTENTACION_RAPIDA.md).
- [Matriz de las diez clases](../MATRIZ_CLASES.md): implementación, archivos, prueba y límites, sin acreditar Packet Tracer/NAC/ARP.
- Las evidencias de etapas [1](etapa-01.md), [2A](etapa-02a.md), [2B](etapa-02b.md), [3](etapa-03.md), [4](etapa-04.md) y [5](etapa-05.md) se conservan como registros históricos.

**Cierre:** la regresión funcional y de infraestructura queda verificada. La aplicación no está libre de vulnerabilidades: los 47 hallazgos High continúan como riesgo residual. No se avanzó a otra etapa, ni se hicieron commits o push.
