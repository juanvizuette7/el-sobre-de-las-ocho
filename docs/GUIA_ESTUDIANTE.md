# Guía del estudiante: entender el sobre

**La etapa 1 ya tiene un portal real; el examen protegido sigue en diseño.** La primera parte explica lo implementado. Las secciones sobre cifrado, cuentas, reloj y laboratorios describen etapas futuras, todavía pendientes. La especificación principal es `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf` (F3). Para relacionar cada explicación con la clase y página original, consulta [MATRIZ_CLASES.md](MATRIZ_CLASES.md).

## Lo que ya puedes abrir

Con Docker Desktop activo, ejecuta los comandos CMD de [README](../README.md) y abre `http://127.0.0.1:8080`. Verás una portada con las áreas previstas de docente, estudiante y laboratorio administrativo. Los enlaces navegan a inicio, áreas y estado del servicio. Las seis etapas quedan en PLAN_IMPLEMENTACION, fuera del producto. Las tarjetas «Pendiente» no publican, descargan ni simulan ataques; el laboratorio no tiene ruta de acceso ni controles. El sobre dibujado con CSS es una ilustración; el número 08:00 no es un reloj activo.

El botón **Comprobar conexión** sí funciona: pide `/health` al servidor. Solo indica que la aplicación respondió; no verifica integridad, autorización ni cifrado. Si la respuesta tarda más de cinco segundos o es incorrecta, muestra un error y permite volver a intentarlo. Esto evita presentar un estado verde inventado.

La interfaz usa lenguaje dirigido a sus usuarios; las explicaciones sobre cómo desarrollar o estudiar el sistema quedan en esta guía. «El portal está disponible» solo significa que la consulta real de salud fue correcta. Mostrar «Acceso administrativo pendiente de habilitación» no implementa autorización: actualmente no existe ninguna entrada administrativa. Cuando se construya ese acceso será necesario protegerlo en el servidor.

## De abrir la página a verla en pantalla

Una petición HTTP es un mensaje que tu navegador envía para pedir algo. Al abrir la dirección local, pide `GET /`; GET significa consultar. El servidor responde con un código, unas cabeceras y un cuerpo. El cuerpo de la portada es HTML; el navegador lo interpreta y después pide CSS, JavaScript y el icono.

En nuestro proyecto sucede lo siguiente:

1. El navegador conecta con `127.0.0.1:8080`, el propio computador.
2. Docker entrega ese tráfico al puerto 8080 del contenedor Nginx.
3. Nginx actúa como **proxy inverso**: recibe la petición en nombre de la aplicación y se la envía a `app:8000`, dentro de Docker. El nombre `app` se resuelve al contenedor Python.
4. Uvicorn recibe HTTP y llama a **FastAPI**, el framework Python donde declaramos qué función atiende cada ruta.
5. La función `inicio` de `app/main.py` usa **Jinja2** para convertir las plantillas en HTML. `base.html` contiene la estructura común y `components.html` reutiliza iconos y tarjetas.
6. La respuesta regresa por Nginx al navegador. CSS decide el aspecto; JavaScript solo consulta salud al pulsar el botón. No se descargan fuentes ni recursos externos.

En `app/main.py`, `@app.get("/")` asocia una URL con una función. `@app.get("/health")` atiende otra ruta y devuelve datos JSON. El modelo `EstadoSalud` define sus campos. `StaticFiles` expone únicamente `app/static`, no los PDF, el código Python ni la carpeta completa del proyecto.

**FastAPI** facilita escribir y validar respuestas web en Python; no es el navegador ni Docker. **Uvicorn** es el servidor que lo ejecuta mediante ASGI, una interfaz entre servidor y aplicación. **Nginx** es la puerta común: hoy hace proxy y añade cabeceras; después terminará TLS y aplicará cuotas. **Docker Compose** describe cómo se crean y conectan los dos servicios. No necesitan que instales Nginx o bibliotecas Python globalmente en Windows.

Hay dos redes: `entrada`, a la que pertenece Nginx para publicar la dirección local, y `portal`, interna, compartida con Python. FastAPI solo pertenece a la interna. Escribir `EXPOSE 8000` en Dockerfile documenta un puerto: no equivale a publicarlo con `ports`. Por eso no abrimos el backend directamente desde Windows.

## Archivos que conviene leer primero

| Archivo | Qué aprender al leerlo |
|---|---|
| `app/main.py` | Ruta, función, respuesta HTML frente a JSON y recursos públicos |
| `app/templates/base.html`, `index.html`, `components.html` | HTML accesible y reutilización sin copiar tarjetas/iconos |
| `app/static/styles.css` | Variables de color, composición, media queries y movimiento reducido |
| `app/static/main.js` | Petición fetch, espera, respuesta, error y recuperación del botón |
| `infra/nginx/default.conf` | `location`, `proxy_pass` y cabeceras; Nginx habla con el servicio `app` |
| `infra/nginx/nginx.conf` | Configuración general del proceso y escritura limitada a `/tmp` |
| `Dockerfile` | Receta que copia código e instala versiones fijadas; destinos runtime y test |
| `compose.yaml` | Qué servicio ejecuta cada imagen, redes, salud y único puerto publicado |
| `requirements.in` / `.txt` y sus variantes dev | Dependencias directas frente a conjunto completo de versiones |
| `tests/test_portal.py` | Qué esperamos del servidor y cómo se detecta una regresión |
| `scripts/verificar_etapa1.py` | Comprobar contenedores y HTTP reales desde Windows |
| `scripts/verificar_interfaz.cjs` | Revisión opcional de navegador; herramientas fuera de la aplicación |

No hay todavía `auth.py`, `crypto.py`, una base SQLite ni `.env`: se añadirán cuando la etapa correspondiente lo necesite. La base actual no procesa credenciales y no necesita secretos.

## Cómo demostrar esta primera etapa

Abre la portada, recorre sus secciones y señala los estados pendientes. Pulsa el botón y explica que se observa una respuesta real. Ejecuta `docker compose ps`: muestra dos servicios. Ejecuta `python scripts\verificar_etapa1.py` si tienes Python en Windows: comprueba el proxy, redes y ausencia de puertos de FastAPI. Las instrucciones para pytest y reinicio están en [GUIA_WINDOWS.md](GUIA_WINDOWS.md).

Las pruebas de `TestClient` consultan la aplicación sin levantar una conexión real: sirven para detectar errores de rutas y plantillas. El verificador de infraestructura y el navegador sí usan el Nginx que está corriendo. Necesitamos ambas perspectivas; un test de Python aprobado por sí solo no prueba que el puerto Docker esté bien publicado.

Para sustentar, practica explicar este recorrido sin memorizar comandos: «Mi navegador entra por Nginx; Nginx consulta a FastAPI en una red interna; Python devuelve el HTML y el navegador carga los recursos». Relación con clases: HTTP/puertos de clase 2, configuración Nginx de clase 5, mínimo privilegio relacionado con clase 6 y construcción/pruebas relacionadas con clase 7. Eso no completa las prácticas de Wireshark, NAC, análisis de vulnerabilidades o cifrado.

## Glosario que iremos ampliando

| Término | Significado en nuestro proyecto |
|---|---|
| Backend | Python que recibe consultas y produce respuestas |
| Frontend | HTML/CSS/JS que interpreta el navegador |
| Framework | Biblioteca que organiza tareas comunes; aquí FastAPI |
| Endpoint o ruta | Dirección y método que atiende una función, por ejemplo GET `/health` |
| HTTP / GET | Protocolo de petición/respuesta y método para consultar un recurso |
| JSON | Formato de datos de la respuesta de salud |
| Proxy inverso | Servicio que recibe por la aplicación y le reenvía las peticiones |
| ASGI / Uvicorn | Interfaz de servidor Python y programa que la ejecuta |
| Plantilla / Jinja2 | Documento HTML con partes reutilizables que Python renderiza |
| Imagen / contenedor | Receta empaquetada y proceso aislado que se ejecuta desde ella |
| Compose | Archivo/herramienta que coordina los servicios del proyecto |
| Puerto / loopback | Punto de entrada de un servicio / dirección del propio computador |
| DNS de Docker | Resolución del nombre `app` a su dirección interna |
| Healthcheck | Consulta periódica para saber si un servicio responde |
| Dependencia / digest | Biblioteca necesaria / identificador de contenido de una imagen |
| pytest / aserción | Herramienta de pruebas / comprobación de un resultado esperado |
| CSP | Cabecera que limita de dónde puede cargar recursos el navegador |
| Media query | Regla CSS que adapta el diseño a pantalla o preferencias |
| CDN | Servidor externo de recursos; esta portada no depende de uno |

## El objetivo de las próximas etapas

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

La [GUIA_WINDOWS.md](GUIA_WINDOWS.md) ya contiene el entorno observado y los comandos de esta etapa. La [ficha de resultados](evidencias/etapa-01.md) registra ejecuciones reales e incidencias corregidas. Restaurar un examen, identificar usuarios y cumplir P1–P10 siguen pendientes; no se avanza a etapa 2 sin autorización.
