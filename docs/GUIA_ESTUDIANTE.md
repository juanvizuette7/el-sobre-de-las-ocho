# Guía del estudiante: entender el sobre

## Etapa 4: redes y HTTPS desde cero

Esta es la explicación personal para estudiar. Las pantallas del programa conservan lenguaje de producto. El procedimiento técnico y las limitaciones verificadas están en [SEGURIDAD_RED.md](SEGURIDAD_RED.md); el manual gráfico/CLI del simulador está en [labs/network/README.md](../labs/network/README.md).

### Una historia para ubicar las piezas

La profesora tiene un examen en su computador. Inicia sesión y lo sube al portal. El portal lo guarda cifrado en el disco. Más tarde, un estudiante pide descargarlo. Hay dos preguntas distintas: «¿Quién puede abrir el archivo guardado?» y «¿Quién puede leer lo que viaja mientras se sube o descarga?». AES/RSA/SHA del sobre respondían la primera. HTTPS/TLS añade protección para el viaje. Las cuentas, la asignación y las ocho siguen decidiendo si se permite la entrega.

Una **red informática** permite que dispositivos intercambien datos siguiendo protocolos, es decir, reglas compartidas. Un **servidor** es el programa que atiende solicitudes; también se llama servidor al equipo que lo ejecuta. Nginx y FastAPI son programas distintos del mismo sistema, no dos universidades ni dos computadores obligatorios.

Una **IP** identifica una interfaz dentro de una red. `127.0.0.1` es loopback: «este mismo computador». Abrir el portal ahí no lo publica en toda la universidad. Un **puerto** identifica un servicio dentro del equipo: 8443 es la entrada HTTPS de este proyecto. Escribir 8443 no cifra nada por sí solo; Nginx tiene que hablar TLS en ese puerto.

**Docker** ejecuta programas aislados como contenedores. **Compose** describe cómo se levantan juntos. Seguimos teniendo dos contenedores principales. **Nginx** es la puerta o proxy inverso: recibe la conexión del navegador y pregunta a **FastAPI**, el programa que aplica las reglas. FastAPI no publica un puerto hacia Windows. Entre ambos hay una red privada Docker; no es la VLAN de Packet Tracer.

### HTTP, HTTPS y TLS

**HTTP** define peticiones y respuestas: «GET esta página», «POST este formulario», código 200/403/409, cabeceras y cuerpo. HTTP sin TLS permite que un observador del trayecto lea datos transmitidos.

**TLS** es el protocolo que crea un canal cifrado y autentica el servidor con certificados. **HTTPS** es HTTP transportado por ese canal TLS. TLS no cambia el significado de 403 ni decide si el estudiante tiene la evaluación asignada. Protege el contenido mientras viaja. Un **paquete** es una unidad de datos de la red; varios paquetes transportan una petición. **TCP** organiza una conexión fiable y ordenada; su saludo SYN, SYN-ACK y ACK establece la conexión, pero **no la cifra**. El saludo TLS sucede después y negocia la protección.

Nuestro trayecto queda así:

1. Navegador → `https://127.0.0.1:8443` → Nginx: canal TLS real.
2. Nginx → `app:8000`: HTTP dentro de la red privada de Docker.
3. FastAPI → SQLite/sobre privado: comprueba y recupera antes de entregar.
4. Nginx envía la respuesta al navegador dentro del canal TLS.

Por eso no decimos «cifrado extremo a extremo hasta Python»: TLS termina en Nginx. Y no decimos que AES del archivo cifre la conexión: es otra protección. El texto se utiliza en memoria después de verificar el sobre; TLS protege ese texto durante la entrega autorizada al navegador.

### Certificado y autoridad certificadora

Un **certificado digital** relaciona una identidad/nombre de servidor con una clave pública mediante una firma. El servidor conserva la privada correspondiente. El navegador comprueba firma/cadena, vigencia y nombre. No basta ver un archivo llamado certificado.

Una **autoridad certificadora**, CA, firma certificados. Windows/navegador debe decidir en qué raíces confía. En desarrollo creamos una CA local, distinta de una autoridad pública de Internet. Su certificado público se puede importar; su clave privada debe permanecer protegida. Quien robe esa privada podría emitir certificados que el usuario que confía en la CA acepte. Por eso la confianza requiere una decisión consciente.

**SAN**, Subject Alternative Name, es la lista de nombres/IP válidos del certificado. Aquí incluye IP `127.0.0.1` y DNS `localhost`. El puerto no forma parte del SAN. No incluir `::1` significa que no se debe anunciar una URL IPv6 como verificada. La URL canónica del proyecto es `https://127.0.0.1:8443/acceso`.

Una **huella** del certificado permite comparar exactamente qué certificado se va a confiar. La huella del certificado DER no es necesariamente el hash del texto del archivo PEM, que contiene encabezados y Base64. Nuestros comandos muestran la huella del certificado, no una contraseña. Los certificados del servidor vencen tras 180 días; esto usa tiempo real, no las 7:59:59 del laboratorio.

### Demostración 1: preparar HTTPS y entender cada paso

Problema: proteger el trayecto de la profesora y del estudiante. Herramientas: Docker, Nginx y CA local.

1. Abrir Docker Desktop, esperar a que esté listo y usar contenedores Linux.
2. Abrir **CMD**, no escribir estos comandos dentro del navegador o del CLI de Cisco.

```bat
cd /d C:\Users\juanv\Proyectos\el-sobre-de-las-ocho
scripts\preparar_https.cmd
```

`cd /d` cambia carpeta y unidad. El script construye la imagen, ejecuta el generador sin red, conserva certificados existentes válidos, aplica permisos y arranca Compose. No reinicializa cuentas ni genera otra RSA del examen. **No instala confianza en Windows**. Si falla por archivos incompletos no los borra; hay que recuperar una copia privada consistente y entender la causa.

El generador crea tres parejas: CA, servidor Nginx y servidor del laboratorio ficticio. No reutiliza las claves RSA del examen ni el secreto TOTP. El contenedor temporal de preparación usa root solo para asignar propietario Linux a los certificados de cada servicio. Nginx normal sigue ejecutándose como usuario 101, con raíz de solo lectura y solo su pareja TLS montada.

3. Comprobar huella y SAN:

```bat
docker run --rm --user 0 --read-only --network none --mount "type=bind,source=%CD%\certs,target=/certificados,readonly" el-sobre-de-las-ocho-app:etapa1 python -m app.certificates comprobar
```

`--mount` entrega esa carpeta al contenedor solo para leerla; `--network none` impide conexiones de red de esa utilidad. El resultado muestra nombre/huella/SAN sin privadas. Revisarlos antes de confiar.

4. Si decides confiar en esa CA local:

```bat
certutil -user -addstore Root certs\ca\ca.crt
```

`-user` limita el cambio al usuario actual. `Root` es el almacén de raíces de confianza. `ca.crt` es el certificado público. Si Windows pregunta «Está a punto de instalar…», revisar identidad/huella y pulsar **Sí** solo si coinciden. En nuestra ejecución se pidió y recibió autorización expresa antes de hacer este cambio. No se importó la clave privada.

5. Cerrar/reabrir el navegador si estaba abierto y entrar directamente a la URL HTTPS. Usar el icono de información de conexión/certificado para revisar nombre, emisor, vigencia y SAN; el dibujo exacto del candado cambia según Brave/Chrome. No basarse únicamente en el color o en que haya una palabra HTTPS.

```bat
start https://127.0.0.1:8443/acceso
python scripts\verificar_red.py
```

El verificador comprueba conexiones reales, no solo archivos: TLS1.2/1.3, rechazo de versiones viejas, nombre incorrecto y cliente que no confía en la CA, redirección HTTP y rutas privadas. Esperado en esta entrega: 22 comprobaciones aprobadas. Un error de CA/nombre/vigencia es un fallo que debe corregirse, no un motivo para activar `-k` permanentemente.

6. Si abres `http://127.0.0.1:8080/acceso`, Nginx responde 308 hacia HTTPS antes de consultar la aplicación. 308 es una redirección; no es una autenticación aprobada. Una contraseña que ya se hubiera enviado por HTTP no puede cifrarse retroactivamente. Por eso se usa el acceso HTTPS desde el principio.

7. La cookie se envía con **Secure** para HTTPS, **HttpOnly** para reducir acceso desde JavaScript y **SameSite=Lax** para limitar ciertos envíos entre sitios. No contiene el rol; el servidor sigue comprobando la sesión SQLite. CSRF sigue comparando token y origen exacto. No cambiar la URL entre localhost e IP durante un formulario, porque el origen configurado es la IP con puerto8443.

8. Para repetir, ejecutar `docker compose restart` y después esperar salud con `docker compose up -d --wait --wait-timeout 120`. No borrar volúmenes. Para dejar de confiar en la CA al terminar el proyecto, seguir la reversión de SEGURIDAD_RED: identificar exactamente su SHA-1 y `certutil -user -delstore Root IDENTIFICADOR`. Eso quita confianza, no destruye el examen; no eliminar otras raíces.

Qué decir: «El navegador verifica la CA que decidí confiar y el SAN de la IP. Nginx solo acepta TLS1.2/1.3. HTTP no atiende acceso o documentos. Las reglas de aplicación se ejecutan después, como antes».

### Demostración 2: seguir publicando y descargando

Entrar docente en ventana normal con contraseña y el código actual TOTP; entrar estudiante en una privada. La aplicación no muestra laboratorios en el panel estudiante. Publicar el TXT desde la tarjeta docente y comprobar su nombre/estado. No hace falta volver a inicializar usuarios.

Ejecutar los comandos de reloj/asignación/alteración de etapa3 de la sección siguiente, **uno cada vez**, mirando el navegador entre cambios. Antes de las ocho: 403, sin descarga. A las ocho con asignación: 200 y original idéntico. Sin asignación: 403 aunque la conexión sea HTTPS. GCM o SHA alterado: 409 sin documento. Restaurar: original descargable. HTTPS no convierte una evaluación no asignada en autorizada.

Una sesión realmente vencida pide entrar de nuevo. No atrasar Windows para recuperar acceso: TOTP y sesiones siguen usando tiempo real. Si el navegador muestra «Verificación completada» hay que leer también el estado y el motivo: una consulta completada puede haber confirmado un rechazo.

Qué decir: «Conservo las mismas identidades y el mismo sobre. Cambié el canal de comunicación; no cambié la regla horaria». El documento previamente publicado se verificó tras la transición sin reemplazarlo.

### Demostración 3: Wireshark paso a paso

**Wireshark** es un analizador que muestra paquetes capturados. **Npcap** es el componente que permite capturarlos en Windows, incluido loopback. **dumpcap** captura y **tshark** analiza desde terminal; ambos pertenecen a Wireshark. No son firewalls y no garantizan que una aplicación esté segura.

Problema a observar: la misma marca ficticia visible en HTTP y cifrada en TLS. No usar contraseñas de ejemplo del portal, TOTP, cookies o exámenes. No capturar Wi-Fi «por si acaso»: seleccionar exclusivamente el tráfico local preparado.

Si Wireshark no está instalado en otro equipo, ir a su web oficial, instalarlo incluyendo Npcap y herramientas de consola; aceptar los permisos de instalación conscientemente. Comprobar con `"C:\Program Files\Wireshark\dumpcap.exe" -D` y localizar **Adapter for loopback traffic capture**. En nuestro equipo se ejecutó realmente con Wireshark4.4.9/Npcap; no se supone que esté instalado en todos los computadores.

1. Abrir CMD en la raíz y levantar el laboratorio separado:

```bat
docker compose -f labs\compose.red.yaml up -d
```

`-f` usa otra receta Compose y otro proyecto. Solo ofrece una marca fija en HTTP8082/HTTPS8444. No monta la base, RSA/TOTP o sobres del portal y no puede listar carpetas del repositorio.

2. Abrir Wireshark. En la lista de interfaces, doble clic en loopback o abrir opciones y seleccionar solo esa interfaz. Antes de empezar, poner el **filtro de captura**:

```text
host 127.0.0.1 and (tcp port 8082 or tcp port 8444)
```

El filtro decide qué paquetes se guardan; excluye el portal8443 y las pruebas8445. No es igual al filtro de visualización que se escribe después en la barra superior. Si el filtro no es aceptado, detenerse y corregirlo antes de generar tráfico; no ampliar a toda la red.

3. En otra CMD generar dos consultas sin cookies:

```bat
curl.exe http://127.0.0.1:8082/marca
curl.exe --ssl-revoke-best-effort --cacert certs\ca\ca.crt https://127.0.0.1:8444/marca
```

`--cacert` indica qué raíz valida el servidor. El curl Windows/Schannel puede pedir revocación que una CA local no publica; `--ssl-revoke-best-effort` conserva comprobación de cadena/nombre y permite la ausencia de ese servicio local. No es `--insecure`. No agregar `-b` ni copiar cookies.

No usar un navegador ya autenticado para este intercambio: las cookies se vinculan al host y pueden viajar entre puertos. curl/urllib sin almacén de cookies evitan ese problema.

4. Pulsar el cuadrado rojo de detener captura. Guardar como `.qa\red\mi-comparacion.pcapng`, fuera de Git. Abrir filtro de visualización:

```text
tcp.port == 8082 || tcp.port == 8444
```

5. Probar `tcp.flags.syn == 1`: SYN y SYN-ACK muestran el comienzo de las conexiones TCP. Revisar origen/destino, puertos y tiempos. Ambos extremos son el computador local; las direcciones MAC de un enlace físico no tienen por qué aparecer como en Ethernet en una captura loopback.

6. Seleccionar el flujo HTTP8082. Si no se identifica, clic derecho → Decode As → HTTP. Clic derecho → Follow → TCP Stream. Deben aparecer ruta `/marca`, cabeceras y `SOBRE-LAB-HTTP-HTTPS-2026` en claro. Cerrar el stream y limpiar el filtro de flujo que Wireshark haya dejado.

7. Filtrar `tcp.port == 8444`. Decode As TLS si hace falta. Revisar ClientHello/ServerHello y registros TLS. Follow TCP Stream no muestra el cuerpo HTTP como texto: muestra bytes TLS. Las IP, puertos, tamaño y tiempos siguen visibles. TLS1.3 cifra parte del handshake; no esperar que todos los certificados o campos sean visibles en toda captura.

8. Filtro `tcp contains "SOBRE-LAB-HTTP-HTTPS-2026"`: debe encontrar la marca solo en HTTP. No proporcionar claves de sesión al analizador ni activar SSLKEYLOGFILE en este ensayo. Un analizador que recibe las claves podría descifrar: eso sería otro experimento.

9. Alternativa automática reproducible:

```bat
python scripts\capturar_comunicaciones.py
```

Captura ocho segundos, genera ambas consultas reales, usa tshark y guarda `.qa/red/http-https.pcapng` con resumen JSON. Nuestra captura real tuvo marca visible en un paquete HTTP, cero apariciones en claro en HTTPS, cinco registros TLS cifrados y cuatro paquetes con SYN/SYN-ACK. Los conteos pueden cambiar entre ejecuciones; no memorizar esos números como si fueran el protocolo. Lo importante es el flujo y las verificaciones.

10. Detener el laboratorio al terminar:

```bat
docker compose -f labs\compose.red.yaml down
```

Repetir requiere levantarlo otra vez e iniciar otra captura. Si no aparece ningún paquete, revisar interfaz loopback, filtro, puertos y que el laboratorio esté activo. Si no aparece HTTP como protocolo, revisar Decode As. No concluir que «todo está cifrado» porque se capturó la interfaz equivocada.

Qué decir: «Esta captura es auténtica y usa solo datos ficticios. TCP transporta ambos flujos; TLS protege el contenido de uno. También validé el certificado, no solo observé caracteres ilegibles».

### Demostración 4: entender VLAN y ACL antes de configurar Cisco

Una **MAC** identifica una interfaz en el enlace local. Un switch aprende por qué puerto se alcanza cada MAC. Una **VLAN** divide un switch en grupos lógicos que no comparten el mismo dominio de broadcast. No significa «cifrado» ni «conexión privada a Internet». Un **router** comunica redes diferentes; una **puerta de enlace** es la dirección a la que un equipo manda tráfico destinado a otra red.

Una **ACL** es una lista ordenada de reglas: permitir o denegar según origen/destino/protocolo/puerto. El orden y la interfaz donde se aplica son importantes. Una ACL stateless no recuerda conversaciones como un firewall stateful; no presentar ambos como idénticos. Un puerto access lleva la VLAN de un equipo final; un trunk transporta varias VLAN etiquetadas entre switch/router.

En la maqueta hay docentes VLAN10, servidores VLAN20 y estudiantes VLAN30. El estudiante puede abrir HTTPS del servidor web, pero no administrar el switch ni llegar al servidor AAA. La profesora puede gestionar por el acceso previsto. Estas IP son del simulador: no se escriben en el adaptador de Windows.

La receta completa, clic por clic y comando por comando, está en `labs/network/README.md`. Incluye tabla de dispositivos/puertos/IP, comparación plana, CLI `switch-core.cfg`, `router-r1.cfg`, comprobación `show vlan brief`, `show interfaces trunk`, `show access-lists` y pruebas permitidas/denegadas. Leer primero la tabla de cableado; pegar una configuración para Fa0/1 cuando conectaste Fa0/8 no hace funcionar la red.

Packet Tracer9 está instalado y se logró abrir su interfaz. **No hay un `.pkt` validado ni resultados de ping/VLAN/ACL/WLAN/RADIUS ejecutados por esta entrega**. Debes completar la receta, guardar el archivo desde Packet Tracer, cerrarlo y reabrirlo antes de presentarlo como evidencia. El diagrama y los `.cfg` son material preparado, no un sustituto de ejecutar la simulación.

Para repetir: guardar una copia antes de ACL/AAA, abrir esa copia y usar Realtime/Fast Forward. En Simulation seleccionar ARP/ICMP/TCP, avanzar un evento y revisar dónde se descarta la petición. Conservar fallos y causas en la ficha P5. No usar un archivo vacío con extensión `.pkt` ni un dibujo como prueba de conectividad.

Qué decir después de ejecutarlo: «Las VLAN separan redes; el router y la ACL deciden cruces. Esta maqueta representa una política, no protege por sí misma los contenedores reales de Docker». Hasta ejecutarlo, decir que está diseñado y pendiente de validación.

### Demostración 5: WLAN, WPA2 y RADIUS

**WLAN** es una red local inalámbrica. **SSID** es el nombre visible de esa red. **WPA2 Personal** protege el enlace radio con una clave compartida y cifrado AES-CCMP; no es la clave AES del documento. Una contraseña compartida débil sigue siendo un problema. **WPA2-Enterprise** usa autenticación individual/802.1X con un servidor compatible, normalmente RADIUS; no afirmar que existe solo por seleccionar WPA2 Personal.

**RADIUS** es un protocolo de AAA para consultar identidades de red. En C4 el switch consulta a Server-PT antes de permitir administración. No reemplaza la cuenta docente de SQLite ni el TOTP de la web. Cada sistema tiene sus identidades de ensayo y límites.

El manual prepara dos prácticas separadas: WRT300N + Laptop/WPC300N con WPA2 Personal y RADIUS para administración del switch. En WLAN: Physical apagar laptop/cambiar módulo/encender; GUI Wireless configurar SSID/cifrado; PC Wireless conectar y probar clave buena/mala. En RADIUS: Server → Services → AAA, cliente switch/IP/secreto, usuario ficticio; switch con AAA/SSH; probar usuario válido e inválido. No reutilizar ninguna contraseña real.

La capacidad efectiva depende del dispositivo/IOS de Packet Tracer. Si rechaza un comando o no tiene la opción AAA/HTTPS, registrar versión y limitación; no marcar «funciona» basándose en que lo dice una guía. Los detalles y recuperación de consola local están en el manual. No se necesita instalar un servidor RADIUS real en Windows para esta práctica.

### Demostración 6: NAC sin bloquear el computador

**NAC**, Network Access Control, combina identidad y estado de un dispositivo para decidir dónde puede conectarse. Por ejemplo: portátil docente conocido y actualizado puede administrar; equipo desconocido no entra; uno conocido sin actualización recibe una restricción. La **postura** es ese conjunto de condiciones de seguridad, no la hora del examen.

```bat
python -m labs.nac.modelo
```

El script crea objetos de ejemplo. No lee el antivirus real, no autentica tu Wi-Fi y no instala reglas. `Equipo` representa identidad/tipo/condiciones; `Zona` guarda reglas y padre; `admitir` devuelve permitir/rechazar/restringir. Una regla hija puede reemplazar la heredada. Lo definido solo en la hija no aparece en el padre. Si no hay permiso explícito, default deny.

Resultado esperado y probado: docente conforme permitido en administración; estudiante conforme permitido para web; estudiante en administración rechazado; desconocido rechazado; conocido sin actualizar restringido. La demostración de ámbitos permite 3306 en una zona interna y lo rechaza fuera; ese puerto ilustra la clase, no significa que nuestro portal haya migrado de SQLite a MySQL.

Para repetir, ejecutar de nuevo: todos los datos se recrean en memoria y no hay que restaurar adaptadores de Windows. Las pruebas automatizadas verifican estas decisiones. Qué decir: «Es un modelo de decisión académico, no un NAC empresarial que esté filtrando mi red».

### Demostración 7: ARP y MITM con tablas ficticias

**ARP** relaciona una IP local con una MAC para entregar tramas. No es una contraseña ni un cifrado. Una **tabla ARP** guarda asociaciones aprendidas. **MITM**, intermediario, describe una situación donde alguien se coloca en el camino de una comunicación. Una asociación ARP fraudulenta puede desviar tráfico hacia una MAC equivocada.

```bat
python -m labs.arp.modelo
```

El modelo muestra una puerta `192.0.2.1` asociada primero a la MAC del router y después a la de un intermediario ficticio. No ejecuta `arp -s`, no envía paquetes ni modifica el sistema. Los rangos/MAC son de ejemplo. Comparar ambas tablas y explicar hacia quién se entregarían las tramas.

TLS correctamente validado dificulta leer/modificar contenido sin que falle el canal, pero no corrige ARP, no oculta todos los metadatos y no garantiza que el intermediario deje pasar los paquetes. Aceptar un certificado falso o entregar claves al adversario cambia el modelo de amenaza. No capturar credenciales para «demostrar» esto.

Repetir el comando restaura las tablas iniciales en memoria. Qué decir: «Representé el engaño que muestra C9 p.8 y su consecuencia; no hice envenenamiento ARP real. La captura HTTP/HTTPS es otro ensayo controlado y auténtico».

### Preguntas para la sustentación de redes

| Pregunta | Respuesta correcta con nuestro proyecto |
|---|---|
| ¿Cambiar 8080 por 8443 crea HTTPS? | No; hay que configurar TLS/certificado en Nginx y validar la conexión. |
| ¿Qué comprueba el certificado? | Cadena/firma, vigencia y nombre/IP del servidor; no que el estudiante esté asignado. |
| ¿Confiaste en una clave privada? | No. Se importó solo el certificado público de la CA, con autorización y huella revisada. |
| ¿Por qué no ignorar la advertencia? | Dejaría sin validar identidad del servidor; corregimos CA/SAN o fecha, no ocultamos el error. |
| ¿TLS sustituye AES y SHA? | No: TLS protege el viaje; el sobre protege almacenamiento y referencia aprobada. |
| ¿Se ve algo en una captura HTTPS? | IP, puertos, tamaños, tiempos y partes del handshake; el cuerpo va cifrado sin claves de sesión. |
| ¿El saludo TCP cifra datos? | No; establece la conexión fiable. TLS negocia protección encima de TCP. |
| ¿La VLAN protege Docker? | No; Packet Tracer es una maqueta separada. Docker usa sus redes internas reales. |
| ¿Una VLAN impide cualquier acceso? | Separa broadcast; el enrutamiento/ACL y políticas determinan los cruces. |
| ¿ACL equivale a firewall stateful? | No. La lista preparada filtra paquetes sin seguir sesiones. |
| ¿WPA2 basta para abrir el examen? | No. Protege el enlace radio y la aplicación todavía exige identidad, asignación, hora e integridad. |
| ¿RADIUS es el login TOTP del portal? | No; la práctica autentica administración de red con otro servicio de ensayo. |
| ¿Tu NAC está bloqueando Windows? | No, es un modelo Python probado con datos de ejemplo y ámbitos. |
| ¿Ejecutaste MITM o ARP spoofing? | No, mostré tablas simuladas; la captura real solo tiene la marca del laboratorio autorizado. |
| ¿Guardaste un `.pkt` funcional? | No en esta entrega; están manual/configuraciones y falta ejecutar y guardar la maqueta. |
| ¿Qué pasa si se pierde el certificado TLS? | Nginx no arranca correctamente; no activa autenticación HTTP. Recuperar respaldo/renovar explícitamente. |

La evidencia de etapa4 diferencia exactamente implementación real, captura real, modelos ejecutados y simulación Cisco pendiente. La siguiente etapa5 tratará SQLi/controles DevSecOps/carga local cuando se solicite; no se anticipa aquí.

## Etapa 3: explicación desde cero y demostración personal

La etapa 3 añade documentos reales al sistema existente. Esta sección describe lo implementado; las secciones históricas de 1/2A/2B que aparecen después explican lo que existía al cerrar cada etapa. La guía es privada para estudiar, no texto para poner en la aplicación. La descripción técnica de entrega está en [CRIPTOGRAFIA_SOBRE.md](CRIPTOGRAFIA_SOBRE.md).

### Primero: qué estamos protegiendo

Un archivo contiene **bytes**, números que representan sus letras y saltos de línea. Por ejemplo, `Pregunta 1` es una secuencia de bytes. Queremos guardar esa secuencia sin que alguien que solo copie el archivo del almacén pueda leerla, y queremos devolver exactamente la secuencia aprobada por el docente.

**Confidencialidad** significa limitar quién puede conocer el contenido. **Integridad** significa detectar que el contenido recuperado no coincide con el aprobado. **Autenticación** comprueba quién eres. **Autorización** decide si puedes hacer una operación. Son problemas relacionados pero diferentes. Cifrar no comprueba por sí solo que sean las ocho, y tener una contraseña de estudiante no permite abrir cualquier evaluación.

**Cifrar** transforma los bytes legibles en otros bytes mediante un algoritmo y una clave. **Descifrar** recupera los originales usando la clave adecuada. No es cambiar la extensión `.txt` a otra, ni esconder el archivo con CSS. En el volumen hay bytes producidos realmente por una biblioteca criptográfica.

Poner una contraseña en una pantalla puede limitar el acceso a esa pantalla, pero no garantiza que el archivo del disco esté cifrado. Algunos formatos protegidos con contraseña sí usan cifrado internamente; no todas las protecciones con contraseña son iguales. Aquí la contraseña identifica la cuenta mediante Argon2id. Una clave AES diferente protege el documento. No usamos la contraseña del docente como clave AES.

### AES y sus números, sin memorizar fórmulas

AES es un algoritmo de cifrado **simétrico**: una misma clave permite cifrar y descifrar. Nuestra clave tiene 256 bits, equivalentes a 32 bytes. Se genera al azar con una fuente diseñada para criptografía. No es `1234`, ni una frase inventada, ni una constante del código.

GCM es el modo que usamos con AES. Además del ciphertext (el contenido cifrado), produce una etiqueta de autenticación o **tag**. Al descifrar, la biblioteca comprueba esa etiqueta. Si la comprobación falla, no devuelve el texto. Nuestra etiqueta tiene 128 bits, 16 bytes. La guardamos unida al cifrado.

También usamos un **nonce**: un valor de 96 bits, 12 bytes, que acompaña a una operación. No es una contraseña y puede guardarse con los metadatos. Lo peligroso sería volver a cifrar con la misma clave AES y el mismo nonce. Nuestro `cifrar` genera ambos de nuevo cada vez. Dos publicaciones del mismo texto producen cifrados distintos.

Los **datos autenticados adicionales**, AAD, no se ocultan, pero se incluyen en la comprobación GCM. Aquí identifican formato, evaluación y versión. Es como escribir el número del examen y de su edición en el sello. Si alguien intenta intercambiar un sobre entre evaluaciones o versiones, la autenticación no coincide.

Decir que GCM autentica el cifrado no significa que compruebe la cuenta docente ni que sea una firma digital. Comprueba una relación criptográfica entre clave, nonce, AAD y ciphertext/tag. Identidad y permisos se revisan aparte.

### RSA: proteger la llave pequeña

RSA es **asimétrico**: tiene una clave pública y otra privada relacionadas matemáticamente. La pública permite proteger un dato; la privada permite recuperarlo en este uso de cifrado. Compartir la pública no equivale a revelar la privada.

Nuestro servidor genera RSA de 3072 bits una vez. De esa privada obtiene la pública. No cifra todo el examen con RSA: RSA tiene un límite de tamaño y resulta más adecuado aquí para proteger los 32 bytes de la clave AES. AES protege el archivo; RSA protege la clave AES. Eso se llama **cifrado híbrido**.

RSA-OAEP es el esquema de cifrado RSA que usa la biblioteca. Está configurado con SHA-256 y MGF1-SHA256. No basta escribir la palabra RSA y aplicar operaciones matemáticas propias: el esquema completo importa. En `app/crypto.py`, `oaep`, `cifrar` y `descifrar` utilizan las primitivas de `cryptography`.

La AES envuelta por RSA se guarda en SQLite. La AES en claro solo se usa en la memoria del proceso. La privada RSA se guarda en `/data/secrets/sobre-rsa.pem`, con permiso 0600. El programa puede usarla; no se envía al navegador ni aparece en la bitácora. No la abras para tomar capturas. Nginx no monta ese volumen.

Si la privada se pierde, una copia del documento cifrado no permite recuperarlo por sí sola. Generar otro par RSA no recupera los documentos anteriores. Por eso el sistema se niega a regenerarla si faltó cuando ya hay documentos. Reiniciar los contenedores conserva el volumen; borrar el volumen no es reiniciar.

### SHA-256: comparar lo aprobado

Un **hash** es una huella calculada a partir de los bytes. SHA-256 produce 256 bits, que solemos representar como 64 caracteres hexadecimales. No es una clave para descifrar. El hash no permite volver al texto original.

Al publicar calculamos la huella del original y la guardamos como referencia de esa versión. Al recuperar el documento calculamos otra huella y la comparamos. Cambiar una letra normalmente produce una huella completamente distinta; criptográficamente se busca que encontrar colisiones sea impracticable, no una promesa matemática de que dos archivos cualesquiera nunca puedan compartir huella.

La referencia debe estar protegida. Si un atacante administra el volumen y cambia a la vez documento, claves y huella esperada, SHA-256 por sí solo no descubre quién era el autor legítimo. Nuestra protección es contra cuentas web ordinarias que no tienen acceso al almacén ni un campo para editar la huella. El docente sí puede publicar deliberadamente otra versión, que establece otra referencia.

### Por qué usamos GCM y SHA-256

Son dos preguntas diferentes:

1. GCM pregunta: «¿Se puede autenticar este cifrado con esta clave, nonce y contexto?».
2. SHA-256 pregunta: «¿Los bytes recuperados son los que aprobamos al publicar esta versión?».

En el caso A de la demostración rompemos un byte cifrado. GCM falla antes de recuperar texto. En el caso B, la herramienta local puede usar la clave del servidor para cifrar correctamente un texto con una letra cambiada. GCM lo acepta, porque es un cifrado válido, pero la huella es distinta de la original. Entonces falla SHA-256. No son dos mensajes simulados: son dos fallos distintos ejecutados realmente.

El caso B requiere permisos del operador de Docker. Un estudiante normal no dispone de un endpoint para volver a cifrar o alterar el archivo. Esa herramienta es una prueba controlada de la referencia aprobada, no una vulnerabilidad web deliberada.

### Recorrido exacto: desde seleccionar el archivo hasta descargarlo

1. Abres Docker Desktop con contenedores Linux. Desde CMD arrancas los dos servicios. No necesitas instalar la biblioteca criptográfica en Windows: está en la imagen Python.
2. Entras como docente con la contraseña ya configurada y el código actual del autenticador. No reinicialices cuentas existentes.
3. Abres la tarjeta de la evaluación. Su título y fecha de apertura indican cuál vas a publicar; cada tarjeta tiene su propio formulario.
4. Pulsas el selector de archivo y eliges un `.txt` UTF-8. El control nativo muestra el nombre. Puedes prepararlo con Bloc de notas usando texto ficticio. No hace falta copiarlo dentro de Docker.
5. Pulsas **Publicar documento protegido**. El navegador manda un POST multipart con el archivo y el token CSRF de la sesión. El servidor comprueba docente/MFA, sesión vigente, origen y CSRF. No confía en que el botón estuviera visible.
6. `leer_carga` de `app/documents.py` limita el cuerpo. `validar_texto` de `app/storage.py` comprueba tamaño, extensión, UTF-8, contenido no vacío y ausencia de controles binarios; prepara un nombre seguro. Un Content-Type que diga texto no vuelve válido un ejecutable.
7. `publicar_en_transaccion` confirma que la evaluación existe, crea una versión nueva y calcula la huella de los bytes exactos. La asignación y apertura que ya existían no se duplican ni se cambian con la subida.
8. `privada` abre la RSA existente o la crea solamente en la primera publicación. `cifrar` genera AES/nonce nuevos, cifra el documento y envuelve AES con la pública RSA.
9. `escribir_atomico` escribe solo ciphertext en un archivo temporal privado, sincroniza y lo renombra. SQLite guarda los metadatos y la referencia. La auditoría registra la publicación; el navegador vuelve al panel con la confirmación.
10. En otra ventana privada entras como estudiante. Las ventanas separadas permiten tener cookies y cuentas distintas en el mismo computador.
11. El panel muestra la evaluación asignada, la apertura, el reloj grande y el estado. **Comprobar acceso** consulta realmente al backend. La indicación dura al menos 600 ms para ser perceptible, pero la petición se manda de inmediato. «Verificación completada» significa que hubo respuesta, no necesariamente que se autorizó la descarga. La hora real no se añade a esta confirmación visual.
12. `resolver_documento` de `app/documents.py` utiliza la política de `app/policy.py`. Revisa sesión real, rol estudiante, asignación y fecha/hora del laboratorio. Vuelve a validar dentro del bloqueo que protege la lectura de versión y la bitácora.
13. Antes de apertura no descifra. Si ya corresponde y hay archivo, `recuperar` abre el ciphertext, utiliza RSA para recuperar AES, autentica GCM y compara SHA-256 con la referencia.
14. Si todo está correcto, la disponibilidad permite mostrar **Descargar documento**. Al pulsarlo hay otra petición al servidor y se repiten las comprobaciones: no se reutiliza un permiso antiguo guardado por JavaScript.
15. `descargar_documento` devuelve el documento completo con nombre seguro, attachment y no-store. Si algo falla, no construye una respuesta con bytes del examen ni manda un fragmento antes de terminar.

La interfaz muestra nombres, fechas y estados útiles. No necesita enseñar la clave, el hash completo o el motivo criptográfico interno a un estudiante. La auditoría local permite explicar al profesor qué control falló.

### Qué se guarda y dónde

| Lugar | Contenido | Qué no debes mostrar en una evidencia |
|---|---|---|
| SQLite `/data/portal.sqlite3` | Cuentas/sesiones existentes; tabla `documentos` con versión, tamaño, nombre, fecha, SHA, creador, descriptores de original/activo; eventos | Dump de sesiones, derivados de contraseñas o tokens |
| `/data/sobres` | Archivos `.gcm`: ciphertext y etiqueta, identificados al azar | No se necesita publicar el almacén completo |
| `/data/secrets/sobre-rsa.pem` | Privada RSA persistente | Su contenido completo o parcial |
| `/data/secrets/docente.totp` | Secreto del autenticador ya existente | Su contenido, URI o códigos |
| Memoria del proceso | Texto mientras se carga/verifica y AES mientras se usa | Volcados de memoria o depuración con secretos |
| Computador del estudiante | Copia original después de una descarga autorizada | Datos reales de otras personas |

En SQLite, `original` selecciona la copia cifrada aprobada y `activo` la que se consulta ahora. Normalmente apuntan a la misma. La herramienta puede activar otra copia conservando original y SHA. Restaurar vuelve al descriptor original. No modifica contraseñas, TOTP, asignaciones o reloj.

El volumen se llama `identidad` por compatibilidad con las etapas anteriores. Ahora contiene también sobres y RSA. Que el nombre sea antiguo no significa que exista un servidor nuevo: siguen siendo dos servicios y una sola SQLite. Un volumen conserva datos entre reinicios, pero no es un respaldo contra su eliminación.

### Demostración guiada, un comando a la vez

Estos comandos se escriben en **CMD**, desde la carpeta del proyecto. La fecha es de ensayo; puedes mantenerla aunque el día real sea otro. Las cuentas ya deben existir.

```bat
cd /d C:\Users\juanv\Proyectos\el-sobre-de-las-ocho
docker compose up -d --build --wait --wait-timeout 120
docker compose exec app python -m app.demo preparar --fecha 2026-11-09
start http://127.0.0.1:8080/acceso
```

Espera a que Compose indique servicios saludables. Entra con cada cuenta en ventanas diferentes. El comando `preparar` de 2B configura evaluación/asignación y detiene el reloj a las 07:59:59. **No borra un documento publicado**.

Primero demuestra la subida docente real con tu `.txt`. Para preparar rápidamente una muestra reproducible existe una alternativa:

```bat
docker compose exec app python -m app.demo sobre preparar
docker compose exec app python -m app.demo sobre estado
```

Atención: `sobre preparar` publica la muestra y sustituye el documento actual de ese caso. No lo uses para restaurar tu archivo personalizado: para eso existe `sobre restaurar`. La muestra no contiene un examen real ni secretos. `estado` muestra GCM correcto, integridad verdadera y dos huellas iguales. Puedes decir: «El programa recuperó el contenido con las primitivas reales y comparó su huella con la referencia». Ver bytes ilegibles por sí solo no demostraría seguridad.

Con el estudiante pulsa **Comprobar acceso**: a las 07:59:59 debe aparecer el candado cerrado y no debe mostrarse un enlace habilitado. Explica: «El rechazo lo decide Python, no el botón». Luego:

```bat
docker compose exec app python -m app.demo reloj fijar 2026-11-09T08:00:00
```

Vuelve a comprobar. Debe aparecer acceso autorizado, documento verificado y enlace de descarga. Descarga y abre el `.txt`: sus bytes deben ser los publicados. Las pruebas automáticas comparan bytes, no solo que exista un archivo.

Para demostrar que la hora no es suficiente:

```bat
docker compose exec app python -m app.demo asignacion retirar
```

Comprobar → restricción por no asignada. Una URL guardada también recibe 403. Reponer:

```bat
docker compose exec app python -m app.demo asignacion asignar
```

Caso A:

```bat
docker compose exec app python -m app.demo sobre alterar-gcm
docker compose exec app python -m app.demo sobre estado
```

En el navegador, comprobar acceso o intentar la URL de descarga. Debe bloquearse con 409, sin documento. En terminal GCM no supera autenticación. Explica: «Cambié los bytes cifrados; la etiqueta ya no coincide». Volver al original:

```bat
docker compose exec app python -m app.demo sobre restaurar
```

Descargar otra vez para comprobar que se recuperó. Caso B:

```bat
docker compose exec app python -m app.demo sobre alterar-hash
docker compose exec app python -m app.demo sobre estado
```

Aquí GCM debe figurar correcto, pero las huellas deben ser distintas e integridad falsa. Comprobar/descargar → 409. Explica: «Esta copia está cifrada correctamente, pero no contiene lo aprobado. La referencia original no se actualizó y SHA-256 lo detectó».

```bat
docker compose exec app python -m app.demo sobre restaurar
docker compose exec app python -m app.demo sobre auditoria
```

Comprueba otra descarga original. En la auditoría identifica `autenticacion_gcm_fallida`, `discrepancia_sha256`, `original_verificado` y `restaurar`. El instante real del evento es distinto de la referencia didáctica. No intentes alinear ambos cambiando Windows.

Para cerrar el ensayo y dejarlo listo para repetir:

```bat
docker compose exec app python -m app.demo preparar --fecha 2026-11-09
```

Para probar persistencia, restaura primero, deja apertura a las ocho, descarga, ejecuta `docker compose restart`, espera servicios saludables con `docker compose up -d --wait --wait-timeout 120`, y descarga con la sesión aún vigente. Debe ser el mismo contenido. Una sesión realmente vencida requiere iniciar sesión otra vez: reiniciar no debe volverla inmortal. Nunca uses `down -v` para este ensayo.

### Mensajes y diagnóstico sin improvisar

| Mensaje/resultado | Significado y siguiente paso |
|---|---|
| Examen bloqueado / falta un segundo | La referencia del recurso aún está antes de la apertura; fijar las ocho y comprobar |
| Acceso autorizado / horario cumplido | Se superaron reglas; revisar también si el documento ya está publicado |
| Documento pendiente de publicación | La evaluación existe, pero aún no tiene sobre; publicar como docente |
| Evaluación no asignada | Cumplir horario no sustituye la asignación; reponer con CLI autorizada |
| Entrega bloqueada por integridad | No se mandó el examen; consultar la bitácora y restaurar el original |
| Verificación completada | La consulta terminó; leer el estado final para saber si permite o rechaza |
| Disponibilidad no verificada | Error de transporte/servicio; no asumir que el estado anterior sigue vigente; reintentar |
| 400 / 413 al publicar | Formato, contenido, nombre o tamaño no admitido; revisar el TXT |
| 401 | Sesión ausente, incompleta o vencida; entrar nuevamente |
| 403 en publicación | Rol/MFA/CSRF/origen no válido; no intentar saltarse el control cambiando JavaScript |
| Clave no disponible en estado local | No generar otra ni borrar datos; recuperar un respaldo privado consistente |

### Preguntas difíciles y respuestas correctas

| Pregunta del docente | Respuesta con nuestro proyecto |
|---|---|
| ¿AES-256 significa contraseña de 256 caracteres? | No. La clave aleatoria tiene 256 bits, 32 bytes; es independiente de la contraseña de acceso. |
| ¿Dónde está la clave AES? | Se usa temporalmente en memoria; en disco solo permanece envuelta con RSA-OAEP. |
| ¿La pública RSA puede abrir el examen? | En este esquema de cifrado la pública protege AES; la privada la recupera. No es un uso de firma digital. |
| ¿Por qué no usar solo RSA? | El tamaño de entrada de RSA-OAEP es limitado. AES cifra el archivo eficientemente y RSA protege su pequeña clave. |
| ¿Cómo sabes que no estás simulando cifrado? | Las pruebas recuperan los bytes reales, OAEP con otra privada falla y modificar ciphertext/tag produce InvalidTag. |
| ¿GCM ya no comprueba integridad? | Sí autentica el cifrado. SHA compara además el texto recuperado con la referencia de la versión aprobada; el caso B lo distingue. |
| ¿Por qué no MD5 como el taller? | El taller C1 muestra la idea del hash con MD5; el proyecto usa SHA-256 según F3 y las decisiones de implementación. |
| ¿Un atacante podría cambiar archivo y hash? | Si administra el volumen podría alterar ambos. No afirmamos protección contra el dueño de Docker; las cuentas web no pueden editar la referencia directamente. |
| ¿Una clave distinta para dos documentos importa? | Separa material por publicación y evita reutilizar clave/nonce. AAD también vincula recurso y versión. |
| ¿Restaurar reutiliza un nonce de manera peligrosa? | No vuelve a cifrar: selecciona los mismos bytes del original ya cifrado. Toda nueva operación de cifrado genera AES/nonce nuevos. |
| ¿Qué pasa si el servidor cae a mitad de escribir? | Primero escribe un temporal y lo renombra completo; después confirma metadatos. Puede quedar un huérfano, pero no se autoriza texto parcial. No prometemos tolerancia a cualquier fallo físico. |
| ¿Por qué no hay descarga antes de las ocho si conozco la URL? | El GET vuelve a comprobar sesión, rol, asignación y apertura en backend antes de descifrar. |
| ¿El reloj simulado afecta TOTP? | No. Sesiones y TOTP mantienen tiempo real; solo la apertura usa la referencia del laboratorio. |
| ¿Es confidencial la conexión HTTP actual? | No. El cifrado en disco no cifra la red. TLS y su evidencia corresponden a etapa 4. |
| ¿El administrador puede ejecutar la alteración desde la web? | No hay endpoint de laboratorio. Se requiere la herramienta local dentro de Docker. |
| ¿El sistema borra lo que el estudiante descargó? | No. no-store evita caché intencional del portal, pero no revoca una copia guardada legítimamente. |

Para verificar, ejecutar la suite en la imagen de pruebas y el recorrido de navegador como indica CRIPTOGRAFIA_SOBRE. La ficha `docs/evidencias/etapa-03.md` contiene los resultados realmente observados. No presentar TLS, Wireshark, NAC o análisis de vulnerabilidades como realizados en esta etapa.

## Archivo histórico de aprendizaje de etapas 1, 2A y 2B

**Estado histórico anterior a etapa 3; consultar el capítulo vigente de arriba para cifrado y descarga.** Cuentas, sesiones, TOTP y permisos por rol ya funcionan; asignaciones y horario también funcionan; cifrado y descarga todavía no. La especificación principal es `docs/planificacion/Fase_3_Diseno_El_sobre_de_las_ocho.pdf` (F3). Para relacionar cada concepto con la clase y página original, consulta MATRIZ_CLASES. Esta guía no forma parte de las pantallas del producto ni de una entrega pública; estar ignorada no retira la copia que ya estaba versionada en Git.

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
