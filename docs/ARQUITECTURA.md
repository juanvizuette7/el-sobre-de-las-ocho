# Arquitectura vigente

La solución es una aplicación FastAPI en Docker detrás de un único Nginx publicado en `127.0.0.1`. Nginx termina TLS en el puerto 8443 y reenvía por una red privada al proceso Python; el puerto 8080 solo redirige a HTTPS. SQLite, sesiones, TOTP, auditoría y el almacén de sobres permanecen privados en el volumen de la aplicación.

La autorización se decide en el servidor: identidad, rol, asignación, apertura en `America/Bogota` y estado criptográfico se comprueban en cada ruta protegida. JavaScript solo presenta respuestas recibidas; no calcula permisos ni relojes. AES-256-GCM, RSA-OAEP-SHA256 y SHA-256 protegen la entrega del documento.

La Etapa 4 añade certificados locales con SAN, TLS 1.2/1.3, cookies Secure/HttpOnly/SameSite, cabeceras de seguridad y una captura Wireshark del tráfico real del portal mediante `scripts/capturar_portal.py`. La Etapa 5 agrega controles aislados de seguridad de aplicación; su alcance y evidencia constan en [SEGURIDAD_ETAPA5.md](SEGURIDAD_ETAPA5.md). No se conservan proyectos independientes de Cisco Packet Tracer, NAC, ARP, VLAN, WLAN o RADIUS.

En la Etapa 5, inicio de sesión y TOTP reutilizan el contador persistente de intentos; el bloqueo genera auditoría sin registrar secretos. Las consultas del portal usan parámetros. La demostración vulnerable es una CLI separada que crea SQLite en memoria con datos ficticios. Bandit y Trivy se ejecutan fuera del proceso productivo; la imagen Python usa versión y digest fijados sobre Debian 13.

La Etapa 6 realizó la validación final y el cierre documental; no modificó la arquitectura ni añadió funciones. La matriz de diez clases y la evidencia de cierre registran el alcance y los límites verificados. Los PDF originales del profesor no se modifican.
