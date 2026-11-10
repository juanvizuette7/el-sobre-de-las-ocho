# Guía del estudiante: entender el sobre

**Material privado de aprendizaje. Etapas 1, 2A y 2B implementadas; examen protegido pendiente.** Cuentas, sesiones, TOTP y permisos por rol ya funcionan; asignaciones y horario también funcionan; cifrado y descarga todavía no. La especificación principal es `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf` (F3). Para relacionar cada concepto con la clase y página original, consulta MATRIZ_CLASES. Esta guía no forma parte de las pantallas del producto ni de una entrega pública; estar ignorada no retira la copia que ya estaba versionada en Git.

## Disponibilidad y reloj de la etapa 2B

El **reloj didáctico** es una referencia que solo consulta la regla de apertura de evaluaciones. No es otro reloj de Windows. En modo fijo se queda detenido en el instante elegido; en modo normal lee la hora real del servidor y la expresa en Bogotá.

No cambiamos la hora de Windows porque TOTP y las sesiones dependen del tiempo real. Adelantar el recurso a 2035 no debe caducar tu sesión ni cambiar el código actual del autenticador. Si una sesión vence realmente, atrasar el reloj de la evaluación tampoco la recupera.

**RBAC** pregunta si tu rol permite la operación. **ABAC** añade atributos: quién solicita, qué evaluación es, si está asignada y si llegó su fecha de apertura. Un estudiante autenticado puede recibir 403 por horario o por no tener esa evaluación; no basta con haber iniciado sesión.

Autorizar una solicitud significa que el servidor acaba de comprobar esas condiciones con datos de su base y devolvió una decisión. No significa que un botón se volvió verde. En esta etapa un 200 significa que se cumplen asignación y apertura, **no que se entregó un documento**. La respuesta dice descarga_habilitada: false y la interfaz lo informa.

### Recorrido sencillo

1. Inicia los servicios y entra como estudiante con tus credenciales.
2. En CMD ejecuta el comando preparar. Crea los metadatos del caso y su asignación, y deja el tiempo en 07:59:59.
3. Recarga el panel o pulsa Actualizar disponibilidad: debe indicar restricción (403).
4. Fija 08:00:00 y repite con la misma sesión: 200 por apertura cumplida. También debe autorizar a las 08:01.
5. Retira la asignación a las 08:01 y consulta: 403 aunque la hora sea correcta.
6. Reasigna y consulta: 200. Vuelve a preparar para dejar el caso cerrado a las 07:59:59.

Comandos CMD reales, desde la carpeta del proyecto:

    docker compose exec app python -m app.demo preparar --fecha 2026-11-09
    docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:00:00
    docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:01:00
    docker compose exec app python -m app.demo asignacion retirar
    docker compose exec app python -m app.demo asignacion asignar
    docker compose exec app python -m app.demo preparar --fecha 2026-11-09

Se usan siempre una fecha completa y America/Bogota. Comparar solo las horas permitiría confundir días distintos. Por eso un día anterior a las 08:01 todavía está antes de la apertura del día previsto.

**Restaurar tiene dos sentidos:** reloj normal vuelve al tiempo real; puede estar después de las 08:00 y permitir acceso. Preparar restablece el caso de ensayo cerrado, incluyendo su asignación y las 07:59:59. No son la misma operación.

    docker compose exec app python -m app.demo reloj normal
    docker compose exec app python -m app.demo reloj estado
    docker compose exec app python -m app.demo auditoria --limite 20

Los datos del reloj se guardan en SQLite: reiniciar Docker no los borra. Si se pierde esa referencia y ya hay evaluaciones, la política no debe asumir que todo está abierto. Exige una configuración local explícita. No borres el volumen para repetir la demo.

### Archivos y decisiones

| Archivo / función | Responsabilidad |
|---|---|
| app/clock.py: leer_reloj | Devuelve la referencia fija o el tiempo real en Bogotá |
| app/demo.py: preparar_ensayo | Configura un único caso ficticio a las 08:00 y lo deja cerrado |
| app/demo.py: cambiar_asignacion | Otorga o retira la relación con una cuenta existente |
| app/policy.py: decidir_disponibilidad | Aplica identidad, rol, asignación y apertura en orden |
| app/policy.py: consultar_disponibilidad | Revalida sesión, consulta datos, llama a la política y audita |
| app/evaluations.py | Obtiene las evaluaciones del panel y responde la consulta JSON |
| app/audit.py | Registra tiempo real separado del tiempo didáctico |
| tests/test_availability.py | Comprueba fronteras, asignación, independencia y reinicio |

No hay controles de reloj en la web, ni siquiera para el docente. La autorización administrativa del comando depende del acceso local a Docker. Al estudiante no se le entrega Docker ni un endpoint que ejecute la CLI.

### Preguntas para sustentar

| Pregunta | Respuesta correcta |
|---|---|
| ¿Qué ocurre exactamente a las 08:00? | La comparación es inclusiva: referencia igual o posterior a la apertura autoriza si identidad, rol y asignación son correctos. |
| ¿Un usuario sin sesión puede consultar? | Recibe 401. Un estudiante ajeno recibe 403 aun con el horario cumplido. |
| ¿Cambiar la URL o la hora del navegador abre la evaluación? | No. Solo se usa el ID solicitado; cuenta, asignación, apertura y reloj se obtienen en servidor. |
| ¿Ya se entrega el examen original? | No. Es una decisión sobre metadatos; faltan cifrado, integridad y descarga de la etapa 3. |
| ¿El docente puede cambiar el reloj desde su panel? | No hay controles administrativos web. La herramienta es local en el contenedor. |
| ¿Cómo se prueba otro estudiante sin crear usuarios reales? | La suite crea otro estudiante en una base temporal. La demo local también muestra el caso no asignado al retirar la asignación de la cuenta de prueba. |
| ¿Qué hora se guarda en la bitácora? | El instante real del evento y la referencia didáctica de la decisión se guardan en campos distintos. |
| ¿Cambiaste TOTP? | No. La prueba acepta un código actual incluso con el reloj de evaluaciones adelantado; las sesiones siguen venciendo con tiempo real. |
| ¿Ya implementaste Zero Trust completo? | Aplico verificación explícita y mínimo privilegio en cada consulta; no es una infraestructura empresarial completa. |

La evidencia profesional está en [etapa-02b.md](evidencias/etapa-02b.md). No captures cookies, contraseñas o códigos. El comando auditoria selecciona solo campos de autorización; no vuelca tablas de sesiones.

## Identidad 2A en palabras sencillas

**Iniciar sesión** es presentar pruebas de quién eres y recibir una sesión que el servidor reconoce. Primero escribes usuario y contraseña. El estudiante entra a su panel; el docente debe demostrar además que tiene el secreto de su autenticador mediante un código TOTP. No seleccionas el rol en un formulario: ya está asignado en SQLite.

**Autenticación** es comprobar identidad. **Autorización** es decidir si esa identidad puede realizar una acción. Por eso un estudiante que inició sesión correctamente obtiene 403 al pedir `/docente`: está identificado, pero no tiene ese permiso. Sin sesión completa se recibe 401. **Auditoría** registra la decisión sin guardar lo que escribiste en contraseña o código. Juntas son las tres partes de AAA de clase 4.

Una **base de datos** organiza información para consultarla y cambiarla de forma controlada. Aquí SQLite es un archivo en el volumen privado del contenedor Python; no es un tercer servicio Docker. Las tablas guardan cuentas/roles, sesiones, límites de intentos y eventos. Las consultas con parámetros mantienen separados los datos y las instrucciones SQL; no estamos realizando un taller de inyección.

La contraseña no se guarda como texto. Argon2id calcula un **derivado** con una sal aleatoria. El servidor verifica la contraseña contra ese derivado. Dos derivaciones de la misma contraseña dan valores distintos gracias a la sal. Argon2id consume tiempo y memoria para dificultar probar contraseñas; una sal no es otro factor ni una clave secreta que debas memorizar.

Una **sesión** es la continuidad de un acceso. El navegador guarda una cookie con un identificador aleatorio; el servidor conserva su huella, vencimiento y relación con la cuenta. La cookie no dice «soy docente». Cambiarla por un texto inventado no crea una sesión válida. HttpOnly impide leerla desde JavaScript de la página; SameSite limita envíos entre sitios. Ninguna de esas dos opciones cifra HTTP.

Hay tres estados: sesión anónima del formulario, desafío MFA y sesión completa. La contraseña docente solo da un desafío. El servidor cambia identificador y token CSRF al pasar de estado, para que el identificador viejo no se convierta en una puerta reutilizable. Las sesiones completas duran 30 minutos; cerrar sesión también elimina el registro del servidor. Borrar solo la cookie no sería una revocación suficiente.

**MFA** exige factores de categorías distintas: contraseña (algo que sabes) y autenticador con secreto (algo que tienes). **TOTP** transforma ese secreto y el tiempo real en un código de seis dígitos. Cambia cada 30 segundos. La aplicación acepta un pequeño desfase de reloj, pero registra el paso aceptado para que no se vuelva a utilizar. El servidor no muestra códigos ni el secreto por web. En una demostración de un solo computador el aislamiento del segundo factor es didáctico; el administrador local puede acceder al volumen. No equivale a un token hardware independiente de un equipo comprometido.

El alta se realiza en una terminal privada con `docker compose exec app python -m app.manage inicializar`. Las contraseñas se leen sin eco. El secreto/URI aparece para configurarlo una vez en un autenticador local compatible; no lo captures ni subas a Git. El comando pide un código para confirmar el enrolamiento y consume ese paso; espera al siguiente antes del primer login. No pegues contraseñas o secretos en este chat. Los pasos técnicos completos están en IDENTIDAD_ACCESO.

**RBAC** aplica permisos según rol. `app/policy.py` comprueba sesión completa, cuenta activa, rol y prueba MFA. El estudiante no puede hacerse docente cambiando parámetros o la URL. **ABAC** ya comprueba en 2B qué evaluación está asignada a la cuenta y si llegó su apertura. Se añade a RBAC; la descarga y la integridad del archivo todavía no existen.

**CSRF** es intentar que tu navegador envíe una acción usando tu sesión desde otra página. Nuestros formularios requieren un token ligado a la sesión y un origen exactamente permitido. También protegemos iniciar sesión y salir. SameSite ayuda, pero no reemplaza esa comprobación. Nginx usa `Referrer-Policy: same-origin`: el ajuste permitió que los POST legítimos conservaran su origen, sin aceptar valores nulos o ajenos.

Los límites evitan probar códigos sin fin: cinco intentos de contraseña por cuenta y cinco de TOTP por cuenta en cinco minutos. Cambiar cookie no elimina el contador. Existe también un límite agregado de 30 intentos de contraseña visto desde el proxy. Cuenta intentos válidos e inválidos; al ensayar muchas veces puedes tener que esperar. No cambies los controles para fabricar un resultado favorable.

### Dónde está cada control

| Control | Archivo |
|---|---|
| Contraseña y código temporal | `app/security.py` |
| Login, MFA, CSRF y logout | `app/auth.py` |
| Tokens, rotación y límites | `app/sessions.py` |
| Permisos por rol | `app/policy.py` |
| Datos y transacciones | `app/db.py` |
| Qué decisión ocurrió | `app/audit.py` |
| Alta y revocación de todas las sesiones | `app/manage.py` |
| Duraciones, origen y Secure futuro | `app/config.py` |
| Casos automatizados | `tests/test_auth.py` |

### Cómo demostrarlo y responder preguntas

Usa dos sesiones de navegador. Muestra el panel estudiante y luego escribe la URL docente: debe responder 403. En la otra sesión entra como docente, detente antes del código e intenta el panel: 401. Completa TOTP y muestra el panel autorizado. Cierra sesión y solicita otra vez el panel: 401. Conserva respuestas y fichas sin capturar contraseñas, OTP o cookies. No necesitas esperar a las 08:00 reales: el recorrido horario se controla con la CLI descrita en la sección 2B.

La suite de pytest usa claves aleatorias y bases temporales; no opera sobre tus cuentas. El script de navegador de identidad levanta otro proyecto temporal en 8081 con datos en memoria y lo retira al terminar. Eso permite repetir sin restablecer tus contraseñas o el secreto. No se usa ese autenticador programático de prueba para entrar al portal real.

| Pregunta posible | Respuesta correcta |
|---|---|
| ¿Por qué no basta ocultar el enlace docente? | Porque se puede escribir la URL. El backend comprueba el permiso en cada solicitud. |
| ¿Qué tiene la cookie? | Un identificador aleatorio; la cuenta, el rol y el vencimiento se verifican en servidor. |
| ¿La contraseña docente ya autoriza? | No: solo crea un desafío de cinco minutos, sin permisos del panel. |
| ¿El código TOTP se puede repetir? | El paso aceptado se consume en una transacción; otro desafío no puede reutilizarlo. |
| ¿Ya hay ABAC? | Sí, para disponibilidad de metadatos: asignación y fecha/hora se verifican después de identidad y rol. No hay todavía autorización de descarga con integridad. |
| ¿La sesión es segura porque dice HttpOnly? | Ese atributo reduce acceso desde scripts. Aún falta HTTPS para proteger el tránsito. |
| ¿Por qué no has cifrado el secreto TOTP en disco? | Por ahora tiene permisos y volumen privados. El administrador del equipo queda fuera de esa protección; no afirmo cifrado de reposo. |
| ¿Zero Trust está completo? | Aplico verificación explícita y mínimo privilegio en estas rutas; no desplegué una arquitectura empresarial completa. |
| ¿Se puede reiniciar sin perder usuarios? | Sí, el volumen persiste. No se debe usar `down -v` como reinicio. |
| ¿Qué ocurre si pierdes el autenticador? | No hay reenrolamiento o recuperación en 2A; no lo resuelvo borrando el volumen ni mostrando códigos en la web. |

Las palabras del producto describen funciones y estados. Estas explicaciones de aprendizaje se mantienen en esta guía privada.

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

Ahora existen `auth.py`, `config.py`, SQLite y los módulos de identidad indicados arriba. `crypto.py` para el examen sigue pendiente. No se usa `.env` para contraseñas; la inicialización interactiva guarda derivados y un secreto TOTP privado en el volumen.

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

En el diseño final, el rol docente podrá publicar y el estudiante no; esa operación sigue pendiente. Eso es **RBAC**, permisos por rol. Además, el estudiante debe tener ese parcial asignado y cumplir la fecha/hora; es una decisión basada también en atributos, relacionada con **ABAC**. El servidor repite esas reglas aunque escribas directamente la URL. Aplicamos el principio de verificar cada solicitud; no significa haber desplegado una infraestructura empresarial completa de Zero Trust.

La contraseña no se guarda legible. Una función de derivación la transforma con una **sal** aleatoria por cuenta. La sal no es otra contraseña: permite que dos cuentas con la misma contraseña no tengan el mismo valor almacenado. Para contraseñas no basta aplicar una sola vez un hash rápido como SHA-256.

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

La [GUIA_WINDOWS.md](GUIA_WINDOWS.md) contiene los comandos operativos; [IDENTIDAD_ACCESO.md](IDENTIDAD_ACCESO.md) detalla alta y sesiones. Identificar usuarios ya funciona en 2A. La [ficha 2A](evidencias/etapa-02a.md) registra sus pruebas; restaurar un examen y cumplir íntegramente P1–P10 siguen pendientes. No se avanza a etapa 3 sin autorización.
