# Matriz de clases, aplicación y evidencia

## Etapa 3: cobertura real de criptografía y entrega

Estado vigente: etapas 1, 2A, 2B y 3 implementadas. P1–P3 verificados en la aplicación local; P4–P10 pendientes. Las tablas de planificación se conservan más abajo como antecedente. Se releyeron las siete páginas de F3 y las páginas citadas de C1, sin modificar originales.

| Concepto / fuente concreta | Implementación y prueba observada | Modalidad / límite |
|---|---|---|
| Simetría/confidencialidad, C1 p. 7 y pp. 9–11; F3 p. 3 | `crypto.cifrar`, AES-256-GCM; ciphertext sin original, recuperación idéntica, claves distintas y tag/ciphertext alterados rechazados | Real. C1 usa AES-CBC/OpenSSL; GCM es decisión del proyecto |
| Pública/privada, C1 p. 7; F3 p. 3 | RSA-3072-OAEP-SHA256 envuelve AES; otra privada falla; reinicio real conserva documento | Real. No es firma digital ni KMS |
| Hash/integridad, C1 pp. 7, 12–13; F3 pp. 3, 6 | SHA-256 original persistido; copia con GCM válido y otro texto recibe 409 por hash; restauración recupera original | Real. C1 muestra MD5; SHA-256 es decisión F3/proyecto |
| AAA/MFA, C4 pp. 4–5; F3 pp. 1, 3, 6 | Publicación tras TOTP, CSRF/origen, auditoría con cuenta/recurso y dos tiempos; subida anónima 401, estudiante 403, docente sin MFA 401 | Real. HTTP local sin TLS todavía |
| RBAC/ABAC/mínimo privilegio, C4 pp. 6–7, 15; F3 p. 3 | `documents.resolver_documento` reutiliza política: 07:59:59 → 403; 08:00 → 200 byte a byte; sin asignación → 403; anónimo → 401 | Real; no se afirma Zero Trust empresarial |
| Referencia/repetición, F3 pp. 2–3, 6–7 | Copias privadas, AAD, CLI local; GCM y SHA distinguibles, referencia conservada y restauración 200; auditoría fallida impide entrega | Real. Administrador de Docker/volumen fuera del modelo de protección |

Resultados: [etapa-03.md](evidencias/etapa-03.md), **120 pruebas** y recorrido real de carga/reinicio/entrega, capturas y axe A/AA en 1440/390. Comandos y límites en [CRIPTOGRAFIA_SOBRE.md](CRIPTOGRAFIA_SOBRE.md). No acredita Wireshark, Packet Tracer, NAC, SQLi, DoS ni DevSecOps.

## Registro histórico y planificación inicial

**Estado global: etapas 1, 2A y 2B implementadas; P1 tiene cobertura parcial de identidad, P2 acredita el límite horario sin archivo; P3–P10 siguen pendientes.** La modalidad «Real prevista» conserva su carácter futuro donde se indica. Autenticación, MFA, sesiones, RBAC y auditoría de identidad ya existen; asignaciones y horario de metadatos también existen; cifrado y laboratorios no están implementados. Resultados en [evidencia 2A](evidencias/etapa-02a.md); arquitectura vigente en [ARQUITECTURA.md](ARQUITECTURA.md).

## Clase 4: cobertura de etapa 2B

Fuente C4: Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf, pp. 4–7 y 15. F3 pp. 1–3 y 6. Modalidad real sobre metadatos; no archivo entregado. [Evidencia 2B](evidencias/etapa-02b.md).

| Concepto / fuente | Control y archivo | Prueba reproducible | Evidencia / resultado | Explicación para sustentar | Estado |
|---|---|---|---|---|---|
| IAM, C4 p. 4 | Cuenta autenticada y sesión vigente; app/sessions.py y app/policy.py | test_sin_sesion_y_docente_no_autorizan_como_estudiante; test_sesion_estudiante_expira_con_reloj_fijo | 401 sin identidad completa o vencida | Tener un ID de evaluación no identifica al solicitante. | Verificado |
| AAA, C4 p. 4 | Decisión actual y auditoría estructurada; app/policy.py, app/audit.py | test_auditoria_separa_relojes_y_recurso; recorrido real y comando auditoria | Usuario, acción, evaluación, motivo y dos tiempos, sin secretos | Autenticar, autorizar y registrar decisiones son responsabilidades separadas. | Verificado en disponibilidad |
| RBAC, C4 p. 6 | Acceso estudiante a disponibilidad y docente a su panel; app/policy.py | tests de permisos anteriores y test_sin_sesion_y_docente_no_autorizan_como_estudiante | Docente con MFA ve programación, pero no consulta disponibilidad como estudiante | El rol define el tipo de operación; no asigna automáticamente recursos. | Verificado |
| ABAC, C4 p. 6 | decidir_disponibilidad consulta asignación y apertura; app/policy.py | test_limite_inclusive, test_otro_estudiante_no_asignado, test_parametros_del_navegador_no_sustituyen_atributos | 403 a 07:59:59, 200 desde 08:00; ajeno 403 aun a 08:01 | Se combinan usuario, relación con recurso y fecha/hora persistidas. | Verificado para metadatos |
| Verificación explícita / mínimo privilegio, C4 pp. 6–7, 15 | Política en cada petición, sin controles web de reloj; app/evaluations.py y app/demo.py | test_estudiante_no_modifica_reloj; test_retirar_y_reasignar_sin_cambiar_sesion | URL directa aplica las mismas reglas; retirar asignación revoca disponibilidad inmediatamente | La sesión no equivale a un permiso permanente sobre toda evaluación. No se afirma Zero Trust empresarial completo. | Verificado en estas rutas |
| MFA independiente, C4 p. 5 y F3 p. 3 | app/security.py sigue con tiempo real; app/clock.py solo para apertura | test_reloj_no_afecta_totp_ni_caducidad y navegador con reloj 2035 | TOTP actual aceptado; sesión conserva vigencia real | Cambiar el tiempo del recurso no cambia la identidad. | Verificado |
| Denegación y repetición, C4 pp. 6–7 y F3 pp. 3, 6 | Estado persistido y recuperación explícita; app/db.py, app/demo.py | test_reinicio_no_abre_y_preparar_restauracion_repetible; test_reinicio_no_recrea_reloj_perdido_en_modo_normal | Reinicio conserva 07:59:59; reloj perdido no abre; preparar restaura caso cerrado | Un reinicio no elimina una restricción configurada. | Verificado |

P2 se acredita parcialmente en su decisión horaria, no en entrega de bytes originales. P3 (integridad), criptografía, descarga y laboratorios siguen pendientes. Las cuarenta pruebas de 2A forman parte de la suite de regresión.

## Clase 4: cobertura de etapa 2A

Fuente exacta C4: `Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf`; numeración física desde 1. Modalidad: implementación real, con cuentas ficticias en pruebas. Condiciones de seguridad detalladas en IDENTIDAD_ACCESO; evidencia saneada en `docs/evidencias/etapa-02a.md`.

| Concepto y fuente | Aplicación / archivo real | Prueba reproducible | Evidencia | Explicación de sustentación | Estado |
|---|---|---|---|---|---|
| IAM, C4 p. 4 | Alta local de dos identidades y consulta SQLite; `app/manage.py`, `app/db.py` | Alta confirmada, no sobrescritura y login correcto/incorrecto en `tests/test_auth.py` | Resultado pytest y procedimiento local sin credenciales | Identidad gestionada por el servidor; no registro público ni rol elegido por formulario. | Verificado 2A |
| AAA, C4 p. 4 | Autenticación, decisión RBAC y eventos separados; `app/auth.py`, `app/policy.py`, `app/audit.py` | 401 sin sesión, 403 rol incorrecto, auditoría sin datos sensibles | Suite y recorrido Nginx/FastAPI | La autenticación identifica; la autorización permite o deniega; auditoría registra la decisión. | Verificado para identidad |
| Sal/derivación, C4 p. 2; F3 p. 3 | Argon2id por cuenta; `app/security.py` | Dos derivaciones de la misma clave difieren; contraseñas ausentes del dump de DB | Pruebas sin publicar derivados ni secretos | Se conserva un derivado con sal, no la contraseña ni un hash rápido aislado. | Verificado 2A |
| MFA, C4 p. 5 | Contraseña y TOTP docente; `app/auth.py`, `app/security.py`, `app/sessions.py` | OTP incorrecto/válido/reutilizado, contraseña insuficiente, desafío vencido | pytest y flujo real con autenticador programático de prueba | El segundo factor usa un secreto independiente y tiempo real; no es una pantalla de confirmación simulada. | Verificado 2A; TLS pendiente |
| RBAC, C4 p. 6 | Cuenta/rol persistente y comprobado en cada panel; `app/policy.py` | Estudiante → URL docente 403; parámetros rol/MFA no elevan permisos | Suite y respuesta real del proxy | Cambiar URL, query o formulario no cambia el rol ni prueba MFA. | Verificado 2A |
| Mínimo privilegio y verificación explícita, C4 pp. 6–7, 15 | Sesión completa/cuenta activa/rol/MFA comprobados por solicitud; `app/policy.py`, `app/sessions.py` | Sesión vencida, revocada, cuenta inactiva o desafío pendiente → denegación | Suite y recorrido de cierre | La red local o una cookie sin estado válido no otorgan acceso. No equivale a una arquitectura Zero Trust empresarial completa. | Verificado en estas rutas |
| ABAC, C4 p. 6 | Política real de usuario/recurso/asignación/apertura; app/policy.py y app/clock.py | test_limite_inclusive, test_otro_estudiante_no_asignado y CLI | Ficha 2B y recorrido real Nginx | El rol no basta: se comprueban relación con la evaluación y fecha completa. No se entrega archivo. | Verificado 2B para disponibilidad |

La autenticación local del portal no implementa RADIUS/TACACS+; P5 continúa pendiente. El caso P1 completo de F3 incluye publicar y descargar: esos endpoints no existen, por lo que solo se acredita su componente de identidad/MFA y rechazo de roles mediante paneles.

## Aplicación parcial verificada en etapa 1

| Clase y fuente | Implementación real de esta etapa | Archivos existentes | Comprobación / límite |
|---|---|---|---|
| 2, C2 pp. 4, 9–10, 16–18 | Peticiones/respuestas HTTP, IP local y puertos, proxy hacia servicio interno | `app/main.py`, `compose.yaml`, `infra/nginx/default.conf` | Portada y salud por Nginx; falta captura Wireshark y comparación HTTPS para P4 |
| 5, C5 pp. 4, 8–14 | Nginx/Compose, versión oculta, SAMEORIGIN, nosniff; configuración de solo lectura | `infra/nginx/`, `compose.yaml` | Cabeceras y `nginx -t` comprobados; no se ha hecho el iframe de P6 ni el taller completo |
| 6, C6 pp. 5–8 | Separación de entrada y aplicación, puerto único local; relación conceptual con mínimo privilegio | `compose.yaml`, `Dockerfile` | Python sin publicación, red interna, ejecución sin root; esto no implementa NAC, VLAN ni firewall con estado |
| 7, C7 pp. 4, 6–7, 13–14 | Dependencias/imágenes fijadas, construcción reproducible y pytest local | `requirements*.txt`, `Dockerfile`, `tests/test_portal.py` | Pruebas básicas ejecutadas; no hay todavía Bandit/Trivy, análisis CVE ni barrera P8 |

La evidencia de infraestructura de etapa 1 no completa las filas del semestre. La clase 4 añade la cobertura 2A anterior. Clases 1, 3, 8, 9 y 10 mantienen pendientes sus prácticas. El arte del sobre y el texto 08:00 siguen siendo ilustrativos, no cifrado ni reloj funcional.

## Inventario y convención de citas

Archivos inspeccionados en `docs/material-profesor/`; las páginas son físicas desde 1. Los códigos C1–C9 y B permiten citar nombres exactos sin repetirlos en cada fila. F3 corresponde a `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf`, 7 páginas, leído completo.

| Fuente | Nombre real del PDF | Páginas | Cobertura identificada |
|---|---|---:|---|
| C1 | `Semana 1 comunicación y seguridad informatica (martes 1ro de septiembre) CORRECTA.pdf` | 15 | Criptografía; AES, claves, hash y práctica OpenSSL/MD5 |
| C2 | `Semana 2 8 de septiembre Sistemas-de-Comunicacion-y-Seguridad-Informatica.pdf` | 22 | OSI, captura, TCP, HTTP/HTTPS, firewall y VPN |
| C3 | `Semana 3 seguridad y comunicación 15-09-2026.pdf` | 15 | WPA2/WPA3, LAN y VLAN, Packet Tracer |
| C4 | `Semana 4- 22-09-2026 Comunicación y seguridad Informatica.pdf` | 16 | IAM, AAA, MFA, RBAC/ABAC, RADIUS y Zero Trust |
| C5 | `Semana-5 Sesión 29 septiembre Sistemas-de-Comunicacion-y-Seguridad-Informatica.pdf` | 16 | Bastionado Nginx, banners y cabeceras |
| C6 | `Semana 6 06-10-2026 Semana-6-Fundamentos-de-NAC-y-Cortafuegos.pdf` | 19 | NAC, zonas y motor Python con reglas heredadas |
| C7 | `Sesión 7 Sistemas-de-Comunicacion-y-Seguridad-Informatica 13 octubre 2026.pdf` | 23 | DevSecOps, cloud, GitHub Actions, Docker y Trivy |
| C8 | `Sesión 8 20 octu Sistemas-de-Comunicacion-y-Seguridad-Informatica Pentesting y SQL Injectión.pdf` | 21 | Pentesting, Nmap/NSE, falso negativo y SQLi manual |
| C9 | `Sesión 9 y 10- Sistemas-de-Comunicacion-y-Seguridad-Informatica (27-10-2026).pdf` | 16 | El contenido se presenta como semana 9: DoS/DDoS, MITM y ARP |
| B | `Bastionado como mitigación de riesgos 03-11-2026 Sistemas-de-Comunicacion-y-Seguridad-Informatica.pdf` | 18 | El contenido se presenta como semana 10: defensa, parches y limitación de tasa |

Son diez PDF docentes, **no diez sesiones con archivo separado más un undécimo complemento**. La cobertura de clase 10 se acredita con B, el material complementario; no se inventa una sección de defensa en C9. En total se inspeccionaron 181 páginas docentes y 7 de F3 mediante extracción de texto local, sin instalar dependencias ni enviar los PDF a servicios externos.

### Límites de lectura

Se recuperó texto de los once documentos. No se obtuvo texto en C1 p. 15, C4 p. 3 y C5 p. 5; pueden contener imágenes o carecer de capa textual. C7 p. 8 solo devuelve el número de página. No se hizo OCR ni inspección visual de las láminas: no se atribuye contenido faltante a esas páginas. Varias presentaciones producen texto separado por glifos; se reconstruyeron secuencias para identificar temas. Diagramas y capturas incrustadas no quedan acreditados por esa extracción. Si una futura tarea depende de ellos, revisar esas páginas visualmente antes de especificar detalles.

Los conceptos citados abajo se apoyan en texto recuperado de las páginas indicadas; no dependen de interpretar láminas sin texto. Las referencias amplias de F3 p. 4 se concretan aquí con las fuentes reales.

## Cobertura de las diez clases

Pruebas P1–P10: definiciones completas en [RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md). Pruebas «adicionales» complementan F3 sin renumerarla. Abreviaturas de evidencia: una carpeta futura por ejecución y caso en `docs/evidencias/`, con ficha saneada; no son artefactos existentes.

| Clase / concepto explicado | Fuente y página | Modalidad y aplicación prevista | Archivo futuro | Prueba reproducible prevista | Evidencia a guardar | Explicación para sustentar | Estado |
|---|---|---|---|---|---|---|---|
| 1. Cifrado simétrico: una clave cifra y descifra | C1 pp. 7, 9–11; F3 p. 3 | Real prevista: AES-GCM protege el parcial en reposo; comparar con AES-CBC del taller | `app/crypto.py` | P3: publicar, recuperar y comparar bytes; adicional: tag corrupto bloquea | Metadatos no secretos, huellas y resultado de prueba | «El archivo se guarda cerrado; GCM también verifica que el cifrado no se manipuló». | Pendiente |
| 1. Asimetría: pública protege, privada recupera | C1 p. 7; F3 p. 3 | Real prevista: RSA-OAEP envuelve solo la clave AES | `app/crypto.py` | Adicional: clave correcta recupera; otra privada falla sin entrega | Salida saneada, IDs de claves; nunca privada | «RSA protege la llave del sobre; AES protege el contenido». | Pendiente |
| 1. Hash y diferencia frente a cifrado/ofuscación | C1 pp. 7, 12–13; F3 pp. 3–4 | Real prevista: SHA-256 con referencia protegida; comparación teórica con MD5 del taller y ofuscación | `app/crypto.py`, `scripts/demo.py` | P3: cambiar letra, cifrar válidamente, hash distinto y 409; restaurar y 200 | Dos huellas, motivo específico y restauración | «El hash no abre el archivo: permite comparar lo recuperado con el original aprobado». | Pendiente |
| 2. OSI/TCP-IP, IP, puertos e inicio TCP | C2 pp. 3–4, 8–9 | Real prevista: observar tráfico propio y distinguir capas | `labs/http/`, `docs/evidencias/` | P4: filtrar puerto local e identificar SYN/SYN-ACK/ACK | Flujos `.pcapng` privados y ficha anotada | «IP identifica extremos, el puerto el servicio; el saludo TCP prepara la conexión, no la cifra». | Pendiente |
| 2. DPI y HTTP frente a HTTPS | C2 pp. 5–11, 16–19 | Real prevista: marca ficticia visible por HTTP y protegida por TLS | `labs/http/`, `infra/nginx/default.conf` | P4: misma marca, capturar ambos flujos sin claves TLS | Capturas saneadas y selección del flujo | «La carga HTTP se lee; en HTTPS sin claves de sesión se observa cifrado, aunque IP y puertos sigan visibles». | Pendiente |
| 2. Firewall y VPN | C2 pp. 12–14; F3 p. 4 | Simulación del filtrado en NAC; teoría VPN con extremos y túnel, sin desplegar VPN | `labs/nac/model.py`, `docs/evidencias/clase-02.md` | P5 y explicación del dibujo VPN; no afirmar prueba de túnel real | Reglas/salida del modelo y esquema etiquetado | «HTTPS protege esta conexión web; una VPN protege tráfico entre los extremos de su túnel». | Pendiente |
| 3. WEP/WPA/WPA2/WPA3 y WPA2 Personal/Enterprise | C3 pp. 5–6, 9, 11 | Simulación Packet Tracer WPA2 Personal; comparación teórica de alternativas | `labs/network/topologia.pkt` | P5: asociación con clave válida y rechazo con inválida; documentar soporte | `.pkt`, parámetros sin clave y capturas | «El taller configura WPA2; explicar WPA3 no significa haberlo desplegado». | Pendiente |
| 3. VLAN, puertos de acceso y troncal | C3 pp. 7–8, 12–14; F3 p. 4 | Simulación: VLAN 10 docente, 20 servidores, 30 alumnado; troncal como extensión del diseño F3 | `labs/network/topologia.pkt` | P5: ping en red plana; aislar; permitir solo rutas autorizadas; bloquear administración de alumnos | Topología y configuraciones saneadas, pings antes/después | «Separar grupos limita su comunicación; comunicar VLAN necesita capa 3 y una política explícita». | Pendiente |
| 4. AAA e identidad frente a autorización | C4 pp. 4–5; F3 pp. 1–3 | Real: dos cuentas, sesiones, decisiones y auditoría de identidad | `app/auth.py`, `app/audit.py` | Identidad/MFA y paneles verificados; publicación/descarga de P1 pendientes | Ficha 2A y suite | Identificación, permiso y registro son responsabilidades separadas. | Parcial verificado 2A |
| 4. MFA, sal y derivación | C4 pp. 2, 5; F3 p. 3 | Real: Argon2id y TOTP docente independiente | `app/security.py`, `app/auth.py`, `app/config.py` | OTP erróneo/válido/reutilizado, sal individual, caducidad; independencia del reloj verificada en 2B | Suite y ficha 2A | La identidad usa tiempo real; el reloj de apertura permanece independiente. | Verificado 2A y 2B |
| 4. RBAC, ABAC, mínimo privilegio y Zero Trust | C4 pp. 6–7, 15 | Real: RBAC, sesión/MFA y ABAC de disponibilidad por solicitud; sin arquitectura empresarial completa | app/policy.py, app/clock.py, app/evaluations.py | 401 sin sesión; 403 rol/asignación/antes; 200 desde apertura sin archivo; fallo de reloj 503 | Ficha 2B, suite y auditoría | La identidad se autentica con tiempo real; cada recurso se autoriza con sus atributos actuales. | Verificado 2A/2B; entrega pendiente |
| 4. RADIUS y referencia TACACS+ | C4 pp. 5, 8–15 | Simulación RADIUS para acceso al switch; TACACS+ teórico; no autentica el portal Python | `labs/network/topologia.pkt` | P5: administración válida/inválida; verificar soporte real de comandos del simulador | `.pkt`, decisiones AAA y versión de Packet Tracer | «Centralizo la identidad del switch en la maqueta; las cuentas web siguen en SQLite». | Pendiente |
| 5. Banners y mala configuración OWASP A05:2021 | C5 pp. 3–4, 6, 8, 12–15 | Real prevista: ocultar versión Nginx y auditar configuración | `infra/nginx/default.conf` | P6: inspeccionar respuesta normal y errores; no aparece número de versión | Cabeceras antes/después y configuración | «Reducir información expuesta ayuda; ocultar la versión no reemplaza un parche». | Pendiente |
| 5. Clickjacking y MIME-sniffing | C5 pp. 7–8, 12, 14–15 | Real prevista: SAMEORIGIN y nosniff, tipo MIME explícito | `infra/nginx/default.conf`, `labs/http/` | P6: iframe desde otro origen local bloqueado; comprobar cabeceras también en errores | Cabeceras y consola del navegador | «Una cabecera impide incrustar la página desde otro origen; otra evita adivinar tipos». | Pendiente |
| 6. NAC: identidad y estado del dispositivo | C6 pp. 4, 8–10; F3 pp. 4, 6 | Simulación Python ampliada con estado verificado/no verificado | `labs/nac/model.py` | P5: mismo docente/equipo, cambiar estado; acceso pasa a denegado | Entradas, política y salidas etiquetadas simulación | «El modelo pregunta también si el equipo cumple la política; no intercepta paquetes». | Pendiente |
| 6. Zonas, herencia, default deny | C6 pp. 6, 9–18 | Simulación: reglas globales y locales, búsqueda desde zona hija y aislamiento al salir | `labs/nac/model.py`, `tests/test_nac.py` | P5: regla global heredada, puerto interno permitido en hija y denegado fuera; puerto sin regla denegado | Árbol de zonas y salidas permitida/denegada | «Una regla interna no debe hacerse visible a toda la red». | Pendiente |
| 6. Con/sin estado, DMZ y capas 3/4/7 | C6 pp. 5–7; C2 p. 12 | Teoría comparativa; modelo no implementa seguimiento real de conexiones | `docs/evidencias/clase-06.md` | Explicar ejemplo puerto/protocolo frente a inspección HTTP; relacionar P5 y P9 | Esquema y ficha con límites | «Filtrar un puerto no equivale a entender una consulta web; este NAC no es un firewall instalado». | Pendiente |
| 7. DevSecOps, shift-left y CI/CD con barrera | C7 pp. 4, 6–7, 12–20; F3 pp. 2, 4 | Real prevista: flujo **local** en Git con pruebas, Bandit y Trivy; sin dependencia de GitHub Actions | `scripts/security_checks.ps1` | P8: hallazgo bloquea promoción; corrección y todos los controles habilitan siguiente paso | Commit, configuración y códigos de salida | «Automatizo la revisión y detengo el avance cuando hay un fallo». | Pendiente |
| 7. SAST/SCA, CVE e imagen versionada | C7 pp. 7, 11, 13, 18, 20–22 | Real prevista: Bandit revisa Python; Trivy componentes/imágenes; registrar versiones y base | `scripts/security_checks.ps1`, `Dockerfile`, `requirements.txt` | P8: comparar mismo CVE con misma base antes/después; repetir escaneo | Informes originales privados y resumen saneado | «El código propio y las dependencias necesitan revisiones diferentes; un escáner no prueba ausencia de fallos». | Pendiente |
| 7. Cloud, responsabilidad compartida e IaC | C7 pp. 5, 13 | Teoría cloud; configuración Compose versionada y revisión local reales previstas | `compose.yaml`, `Dockerfile`, `docs/evidencias/clase-07.md` | Explicar responsabilidades con esquema; P8 revisa configuración e imagen | Esquema local/cloud y revisión de archivos | «Aquí no desplegué nube; sí apliqué configuración reproducible y controles previos». | Pendiente |
| 8. Reconocer, escanear, analizar, explotar y reportar | C8 pp. 4–12, 16–18 | Real prevista: Nmap/NSE contra copia local autorizada; informe con alcance | `labs/compose.labs.yaml`, `labs/sql/` | P7: objetivo/puerto explícitos, escaneo y validación manual | Comando, versión, objetivo, reporte y hora | «El escaneo orienta la prueba; un puerto abierto no confirma una vulnerabilidad». | Pendiente |
| 8. Falso negativo y SQLi | C8 pp. 18–21; F3 p. 7 | Real prevista en laboratorio: consulta concatenada frente a parametrizada; portal siempre parametrizado | `labs/sql/`, `app/db.py`, `tests/test_labs.py` | P7: acceso indebido antes; mismo intento denegado tras corrección; acceso válido sigue funcionando | Resultados antes/después, diferencia de código y log | «Los datos deben seguir siendo datos, no convertirse en instrucciones SQL». | Pendiente |
| 9. CID, DoS/DDoS, botnets y capas | C9 pp. 4–6, 9, 12–16 | Carga local real prevista y limitada; DDoS/botnet solo teoría, sin colapso obligatorio | `labs/compose.labs.yaml`, `docs/evidencias/clase-09.md` | P9: hasta 100 solicitudes, concurrencia 5; medir latencia y CPU sin/con cuota | Informes y métricas observadas, incluso si no hay degradación | «Disponibilidad se mide; este ensayo de un cliente no representa una botnet distribuida». | Pendiente |
| 9. MITM y ARP spoofing | C9 pp. 7–8; F3 p. 7 | Simulación de dos tablas ARP, sin envenenar la red real | `labs/network/arp.md` | P10: asociar IP de router con MAC distinta y señalar destino de las tramas | Tablas normal/alterada, flechas y explicación | «Cambiar la asociación dirige tráfico a otro equipo; no implica descifrar TLS válido». | Pendiente |
| 10. Controles preventivos, detectivos y correctivos | B pp. 3–6, 18; F3 p. 4 | Real prevista: cuota, auditoría, parche/restauración; WAF/IDS/IPS como ejemplos teóricos | `infra/nginx/default.conf`, `app/audit.py`, `scripts/security_checks.ps1` | P8/P9/P10: bloquear exceso, conservar evento y corregir/restaurar | Logs, informes y ficha de incidente | «Prevengo solicitudes excesivas, observo decisiones y corrijo componentes». | Pendiente |
| 10. Limitación de tasa y preservación de servicio | B pp. 7–8, 10–17; F3 p. 7 | Real prevista: Nginx 5 r/s/IP, burst 5, 429; dos clientes de IP distinta | `infra/nginx/default.conf`, `labs/compose.labs.yaml` | P9: misma carga antes/después; exceso produce 429 y alumno legítimo 200; verificar IP reales | Logs Nginx, latencia, CPU y porcentaje calculado | «Limito a cada origen; debo comprobar que el usuario normal conserve acceso». | Pendiente |
| 10. Ciclo de parches y reducción de superficie | B pp. 4, 6; C7 pp. 13, 21 | Real prevista: mínimo de servicios/puertos y CVE corregible de ensayo | `Dockerfile`, `compose.yaml`, `scripts/security_checks.ps1` | P8: versión vulnerable y corregida con misma base; comprobar exposición prevista | Digest/versiones, CVE y resultados del flujo | «Actualizar debe cambiar el hallazgo y pasar las otras pruebas; ocultar un banner no basta». | Pendiente |
| Complementario B. Método del taller y adaptación | B pp. 12–18; F3 pp. 3, 7 | Real prevista con parámetros F3; comparar el ejemplo docente sin copiar sus cifras como resultados | `docs/evidencias/clase-10.md` | P9: 100/c5, burst 5 y 429; no 1000/c50, burst 10 y 503 del ejemplo | Tabla de parámetros y mediciones propias | «Adapté la práctica al alcance del portátil; el 98,8 % del PDF no es mi evidencia». | Pendiente |

## Temas anunciados y límites de cobertura

| Tema | Fuente | Tratamiento previsto, archivo y validación | Estado |
|---|---|---|---|
| Metasploit | C4 p. 16; F3 p. 4 | Solo ubicarlo teóricamente en explotación, en `docs/evidencias/clase-08.md`; explicación oral. El archivo real de semana 5 trata bastionado, no un taller Metasploit. | Pendiente, teórico |
| HSTS | F3 p. 4 | Explicar junto a TLS en `docs/evidencias/clase-02.md`; no marcar activo sin verificar certificado y política. | Pendiente, teórico inicialmente |
| NAC avanzado | C6 p. 19; F3 p. 4 | Mencionar alcance en `docs/evidencias/clase-06.md`; no atribuir 802.1X real al modelo Python. | Pendiente, teórico |
| SOC y cumplimiento, semana 11 | F3 p. 4 | Ficha de incidente/revisión de controles propuesta en `docs/evidencias/incidente.md`; sin norma o rúbrica inventada. No hay PDF específico local. | Pendiente, aproximación documental |
| Validación final, semana 12 | F3 p. 4 | Dos recorridos P2/P3/P10 y fichas por clase, según etapa 6. No hay PDF específico local. | Pendiente |

## Atención especial y correcciones de interpretación

1. **Criptografía:** C1 usa AES-CBC y MD5; F3 define GCM/OAEP y SHA-256. Comparar pedagógicamente sin sustituir los algoritmos del proyecto. El hash no protege una referencia que un administrador pueda reescribir.
2. **Red e identidad:** Packet Tracer simula, el motor NAC decide sobre datos de ejemplo y el portal aplica controles reales. RADIUS de la maqueta no autentica las cuentas web. El ejemplo C4 utiliza Telnet (pp. 11–12): no presentarlo como canal cifrado ni trasladarlo a la aplicación; verificar soporte de SSH si se amplía la maqueta. No asumir autorización por comando completa con RADIUS o soporte idéntico en todas las versiones del simulador.
3. **Material y calendario:** las recapitulaciones internas de C5/C7/C8 no coinciden siempre con los talleres efectivamente disponibles. Se usa el tema de cada documento real y F3 como especificación, no los anuncios de clases futuras como evidencia de un taller realizado.
4. **DevSecOps:** GitHub Actions es el ejemplo del profesor; el flujo local es la adaptación explícita de F3. Trivy se usará para dependencias/imágenes; Bandit para Python. Elegir un CVE corregible y registrar una base idéntica para comparar; no copiar CVE ni conteos históricos de una diapositiva como resultados propios.
5. **Pentesting:** un NSE sin hallazgos no demuestra seguridad. El falso negativo de C8 es un caso docente, no un resultado ya obtenido aquí. Su objetivo Juice Shop se adapta a la copia SQL propia exigida por F3, con datos y volúmenes separados.
6. **Disponibilidad:** C9 p. 14 muestra una carga mucho mayor y valores de concurrencia inconsistentes entre texto y explicación. B pp. 14–18 usa burst 10 y 503 en su ejemplo. Prevalecen los límites, burst 5 y 429 de F3. No se exige tumbar el portátil, ni un rechazo porcentual o latencia predeterminados.
7. **Tráfico:** TCP no aporta por sí solo confidencialidad; modo promiscuo no asegura ver todo un segmento conmutado; TLS requiere validar identidad del servidor. Las demostraciones medirán lo observado sin repetir generalizaciones de las láminas como garantías.

## Ficha mínima de evidencia y reglas de estado

Ruta futura: `docs/evidencias/<ejecucion>/<caso>/ficha.md`. Incluir clase y fuente/página, modalidad (real/simulación/teoría), commit/versiones, fecha/hora real y didáctica, entorno/objetivo autorizado, condiciones iniciales, pasos/comando saneado, resultado esperado, **resultado observado**, código HTTP/salida, artefactos, incidencia y repetición tras restaurar. Capturas y logs sin contraseñas, OTP, claves, cookies ni contenido privado.

Estados: **pendiente → implementado sin verificar → verificado con evidencia**; si falla, registrar **fallido** y conservar evidencia del fallo. La explicación teórica solo se marca revisada, nunca implementada. Ninguna fila cambia a verificada solo por existir documentación o por mostrar una captura del profesor. Los artefactos crudos se mantienen privados; los Markdown se conservan en Git tras revisión de contenido.
