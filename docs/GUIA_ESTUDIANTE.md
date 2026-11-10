# Guía del estudiante: entender el sobre

**Todavía estamos en diseño.** Esta guía explica lo que se construirá; no describe funciones ya disponibles. La especificación principal es `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf` (F3). Para relacionar cada explicación con la clase y página original, consulta [MATRIZ_CLASES.md](MATRIZ_CLASES.md).

## La idea con un ejemplo

Imagina un examen dentro de un sobre cerrado. Un estudiante llega a recogerlo, pero el encargado comprueba cuatro cosas: quién es, si ese examen le corresponde, si llegó la hora y si el contenido es el aprobado. Conocer la dirección de descarga no evita esas comprobaciones.

Tú representarás a docente y estudiante en el mismo computador. Una ventana normal y una privada permiten mantener dos sesiones distintas. El docente publica un archivo de texto inventado; el estudiante intenta descargarlo. No se usan exámenes reales ni datos de compañeros (F3 p. 1).

La secuencia principal será:

1. A las **07:59:59** del reloj de ensayo, el estudiante recibe rechazo por horario.
2. A las **08:00:00**, recibe exactamente los bytes originales.
3. A la misma hora, eliges una copia con una letra diferente: se bloquea la entrega.
4. Restauras el original: vuelve a funcionar y puedes repetir.

Estos son resultados esperados de P2 y P3, no pruebas ejecutadas. Cada intento deberá dejar registro (F3 pp. 3, 6).

## Qué hace cada tecnología

| Tecnología | Explicación sencilla | Papel en el proyecto |
|---|---|---|
| Navegador | La ventana desde la que usas una web | Muestra formularios, estados y descarga; no decide permisos |
| Nginx | La puerta de entrada que recibe solicitudes | Protege la conexión con HTTPS, añade cabeceras y limita peticiones |
| Python | El lenguaje con el que escribiremos las reglas | Comprueba identidad, asignación, hora e integridad |
| SQLite | Una base de datos guardada en un archivo | Conserva cuentas, metadatos y eventos; no necesita otro servidor |
| Docker | Ejecuta programas en contenedores con su entorno preparado | Separa y hace repetible el portal en tu Windows |
| Docker Compose | Describe cómo arrancar juntos los servicios | Declara Nginx y Python, redes y almacenamiento |
| Volumen | Almacenamiento que puede durar más que un contenedor | Conserva datos aunque reinicies servicios; no es automáticamente un respaldo |
| Git | Historial de cambios del proyecto | Permite saber qué versión de código produjo una prueba |

Fuente de componentes: F3 p. 2. El diseño propone HTML generado por Python y CSS, con JavaScript mínimo, para evitar una aplicación frontend adicional. El framework concreto se decidirá al preparar el entorno.

`127.0.0.1` es una dirección que apunta al propio equipo. El portal se publicará solo allí. La red privada de Docker permite que Nginx hable con Python sin publicar el puerto Python al exterior. «Local» limita exposición; la aplicación aún necesita autenticación y autorización.

## Cifrar, proteger una clave y comparar una huella

**AES-GCM** cifra el archivo con una clave secreta. Sin esa clave no se espera recuperar el texto. También usa una etiqueta de autenticación para detectar alteraciones del cifrado. La clave y el nonce, un valor usado en la operación, se generan con una biblioteca y no deben repetirse como pareja.

**RSA-OAEP** utiliza una clave pública y una privada. Aquí se usa la pública para proteger la pequeña clave AES, y la privada para recuperarla. RSA no se utiliza para cifrar directamente todo el examen. Esa combinación se llama cifrado híbrido.

**SHA-256** calcula una huella de los bytes del archivo. Al publicar se guarda una referencia; al abrir se calcula otra sobre el texto recuperado y se comparan. Un hash no permite descifrar un documento y tampoco certifica por sí mismo quién lo creó. La referencia tiene que estar protegida frente a cambios de las cuentas web.

El taller de clase 1 muestra AES-CBC y MD5; el proyecto aplica GCM y SHA-256 según F3 p. 3. No se copian contraseñas de ejemplo de las diapositivas como secretos del proyecto. Ofuscar —por ejemplo, disfrazar el texto de forma reversible— no sustituye cifrar con una clave.

La copia modificada es un detalle importante: la herramienta cambiará una letra y la **cifrará correctamente**, conservando la huella del original. GCM podrá validar el cifrado de esa copia y SHA-256 descubrirá que su contenido no es el aprobado. Una prueba distinta romperá la etiqueta GCM para demostrar el otro control. Ninguna prueba debe enviar parte del examen antes de terminar las verificaciones (F3 p. 3).

## Identificarse y tener permiso son cosas diferentes

Autenticación responde «¿quién eres?». Autorización responde «¿qué puedes hacer?». Auditoría responde «¿qué intentaste y cuál fue la decisión?». Son las tres partes de AAA estudiadas en clase 4.

El rol docente puede publicar; el estudiante no. Eso es **RBAC**, permisos por rol. Además, el estudiante debe tener ese parcial asignado y cumplir la fecha/hora; es una decisión basada también en atributos, relacionada con **ABAC**. El servidor repite esas reglas aunque escribas directamente la URL. Aplicamos el principio de verificar cada solicitud; no significa haber desplegado una infraestructura empresarial completa de Zero Trust.

La contraseña no se guardará legible. Una función de derivación la transforma con una **sal** aleatoria por cuenta. La sal no es otra contraseña: permite que dos cuentas con la misma contraseña no tengan el mismo valor almacenado. Para contraseñas no basta aplicar una sola vez un hash rápido como SHA-256.

El docente necesitará además un código **TOTP**, que cambia con el tiempo y proviene de un secreto independiente. El autenticador local se prepara antes de la presentación y se mantiene separado del formulario de acceso. Es un segundo factor didáctico: en este proyecto una misma persona maneja las dos cuentas y las herramientas. Ni el secreto TOTP ni los códigos se muestran en evidencias (F3 p. 3).

## Dos relojes que no deben confundirse

El reloj real mantiene TOTP y la duración de la sesión. El reloj didáctico solo sirve para decidir si el parcial está abierto. Así podrás probar las 07:59:59 y las 08:00 sin esperar ni cambiar Windows. Ambas fechas se etiquetarán en los registros cuando corresponda.

La apertura usa una **fecha completa** y la zona `America/Bogota`; no se compara solamente el número 8. La utilidad de ensayo se maneja desde terminal, no desde un botón libre para estudiantes (F3 pp. 1–3).

## Qué significan las respuestas

| Código | Qué significa en esta descarga |
|---|---|
| 401 | No hay una sesión válida; debes identificarte |
| 403 | No tienes el permiso/asignación o todavía no llegó la apertura; la bitácora distingue la causa |
| 409 | El sobre no supera la comprobación de integridad |
| 429 | Nginx recibió demasiadas solicitudes de esa IP |
| 200 | Las condiciones se cumplieron y se entrega el original |

Fuente: F3 p. 3. Un error puede contener un mensaje, pero nunca bytes del examen protegido. Un 200 por sí solo no basta como evidencia: también comprobaremos que el contenido coincide exactamente con el original.

## HTTPS y cabeceras

HTTPS protege el trayecto navegador–Nginx usando TLS. Necesita un certificado que corresponda a la dirección usada y cuya confianza esté preparada en Windows/navegador. Tener un candado o aceptar cualquier advertencia sin revisar no demuestra por sí solo la identidad del servidor. Dentro de la red privada del portátil Nginx se comunica con Python por HTTP; hay que explicar dónde termina el cifrado.

En la práctica de Wireshark enviaremos una marca ficticia por HTTP de ensayo y HTTPS. En HTTP se puede reconstruir el contenido; en la captura HTTPS sin claves de sesión se espera ver carga cifrada. IP, puertos y tiempos siguen siendo observables. El saludo TCP prepara la comunicación, pero no la cifra (F3 P4; clase 2).

Las cabeceras son instrucciones de la respuesta para el navegador. `X-Frame-Options: SAMEORIGIN` limita que otro origen incruste el portal; `X-Content-Type-Options: nosniff` indica que se respete el tipo declarado. Ocultar el número de versión de Nginx reduce información expuesta, pero no corrige errores del programa. Descargar sin caché reduce la reutilización automática del navegador; no puede borrar una copia que el usuario ya guardó (F3 pp. 3–4, P6).

## Qué será real, simulado o teórico

| Modalidad futura | Ejemplos | Qué podrás afirmar |
|---|---|---|
| Implementación real prevista | Cifrado, login/TOTP, descarga, auditoría, TLS, cuotas, corrección SQL en copia aislada y escaneos | Solo después de implementar, probar y guardar evidencia de tu ejecución |
| Simulación | WiFi/VLAN/RADIUS en Packet Tracer, NAC en Python y tablas ARP | «Probé esta política en una maqueta o modelo», indicando sus límites |
| Explicación teórica | VPN, TACACS+, cloud, WAF/IDS/IPS, botnets y ubicación de Metasploit | «Puedo explicar su función», sin decir que están desplegados |

Una VLAN separa grupos de red; en la maqueta habrá docentes, servidores y alumnado. RADIUS centraliza la autenticación del switch simulado; no reemplaza las cuentas SQLite del portal. El modelo NAC comprueba reglas y estado de equipos representados como datos: no filtra el tráfico real de Windows.

SQL injection ocurre cuando una entrada se convierte indebidamente en instrucciones de consulta. Solo la copia de laboratorio tendrá ese fallo intencional. Se repetirá el caso después de parametrizar la consulta: deben fallar el intento indebido y funcionar el acceso válido. Esa copia no comparte secretos ni almacenamiento del portal (F3 pp. 2, 7).

Bandit busca patrones problemáticos en Python; Trivy revisa componentes e imágenes. Un CVE identifica una vulnerabilidad conocida. Compararemos una versión vulnerable y otra corregida usando la misma base de análisis. No pasar un control debe detener la promoción de la versión. El flujo será local para que la presentación no dependa de GitHub Actions (F3 pp. 4, 7).

La prueba de disponibilidad genera hasta 100 solicitudes con concurrencia 5 dentro del laboratorio propio. Compararemos códigos, CPU y latencia antes/después de la cuota, mientras otro cliente autorizado intenta descargar. No es necesario hacer caer el equipo ni obtener un porcentaje de rechazo copiado del profesor. Dos tablas ARP mostrarán un posible desvío de tráfico, sin atacar la red real (F3 pp. 6–7).

## Cómo preparar una buena evidencia

Una captura aislada no demuestra por sí sola la prueba. Cada ficha deberá decir clase, documento/página, entorno, modalidad, versión, condiciones iniciales, pasos, resultado esperado y resultado observado. Adjunta la respuesta o registro relevante y explica por qué sostiene tu conclusión. Conserva también resultados fallidos para documentar la corrección.

Ejemplo **sin ejecutar**: clase 4, estudiante asignado, original intacto, reloj didáctico 07:59:59. Esperado: 403 y motivo fuera de horario. El campo observado se deja pendiente hasta hacer la prueba; no se rellena con el resultado esperado. Nunca captures contraseñas, OTP, cookies de sesión o claves. El examen siempre será ficticio.

## Cómo usar esta documentación

Lee el [resumen](RESUMEN_PROYECTO.md) para conocer requisitos y P1–P10; la [arquitectura](ARQUITECTURA.md) para ver responsabilidades y archivos propuestos; la [matriz](MATRIZ_CLASES.md) para preparar la explicación de cada clase; y el [plan](PLAN_IMPLEMENTACION.md) para construir en seis etapas.

La futura `docs/GUIA_WINDOWS.md` contendrá comandos realmente comprobados para arrancar, verificar, restaurar y parar. Aún no existe y esta guía no promete que Docker o las herramientas estén listos. La primera etapa empezará comprobando entorno y recursos cuando autorices programar. Después se hará un portal mínimo local; todavía no se avanza a esa etapa.
