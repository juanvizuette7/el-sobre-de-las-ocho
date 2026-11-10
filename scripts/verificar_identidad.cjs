/* Recorrido real de identidad en dos contenedores temporales, con datos efímeros. */
const { chromium } = require("../.qa/node_modules/playwright");
const AxeBuilder = require("../.qa/node_modules/@axe-core/playwright").default;
const { execFileSync } = require("node:child_process");
const { randomBytes } = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const archivo = ".qa/compose-identidad.yaml";
const parametros = ["compose", "-f", archivo, "-p", "sobre-identidad-qa"];
function docker(args, input) {
  return execFileSync("docker", [...parametros, ...args], {
    input,
    encoding: "utf8",
    timeout: 120000,
  });
}

async function verificar() {
  fs.mkdirSync(".qa/capturas", { recursive: true });
  const ruta = (nombre) =>
    JSON.stringify(path.resolve(nombre).replaceAll("\\", "/"));
  fs.writeFileSync(
    archivo,
    `services:
  app:
    image: el-sobre-de-las-ocho-app:etapa1
    environment:
      PORTAL_ORIGIN: https://127.0.0.1:8445
    read_only: true
    tmpfs: [/tmp]
    volumes: [datos_prueba:/data]
    networks: [portal]
    healthcheck:
      test: [CMD, python, -c, "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 2s
      retries: 15
  nginx:
    image: nginx:stable-alpine@sha256:583b7f2fce1cdb8da5ad5c39ebd3c33b98b87d493190e548bdee1fa8c619c311
    user: "101:101"
    entrypoint: [nginx]
    command: [-g, "daemon off;"]
    read_only: true
    tmpfs: [/tmp]
    ports: ["127.0.0.1:8445:8443"]
    volumes:
      - type: bind
        source: ${ruta("infra/nginx/nginx.conf")}
        target: /etc/nginx/nginx.conf
        read_only: true
      - type: bind
        source: ${ruta("infra/nginx/default.conf")}
        target: /etc/nginx/conf.d/default.conf
        read_only: true
      - type: bind
        source: ${ruta("certs/nginx")}
        target: /etc/nginx/tls
        read_only: true
    networks: [entrada, portal]
    depends_on:
      app:
        condition: service_healthy
networks:
  entrada: {}
  portal:
    internal: true
volumes:
  datos_prueba: {}
`,
  );
  const estudiante = randomBytes(24).toString("base64url");
  const docente = randomBytes(24).toString("base64url");
  const resumen = [];
  let navegador;
  let etapa = "preparacion";
  const respuestas = [];
  try {
    docker(["up", "-d", "--wait", "--wait-timeout", "90"]);
    docker(
      [
        "exec",
        "-T",
        "app",
        "python",
        "-c",
        "import sys,json,pyotp; from app.manage import guardar_cuentas; from app.config import configuracion_entorno; c=json.load(sys.stdin); guardar_cuentas(configuracion_entorno(),c['docente'],c['estudiante'],pyotp.random_base32(),-1)",
      ],
      JSON.stringify({ docente, estudiante }),
    );
    const administrarEnsayo = (...args) =>
      docker(["exec", "-T", "app", "python", "-m", "app.demo", ...args]);
    administrarEnsayo("preparar", "--fecha", "2026-11-09");
    navegador = await chromium.launch({ channel: "chrome", headless: true });
    const contexto = await navegador.newContext({ ignoreHTTPSErrors: false });
    const pagina = await contexto.newPage();
    pagina.on("response", (r) =>
      respuestas.push(
        `${r.request().method()} ${new URL(r.url()).pathname} ${r.status()}`,
      ),
    );
    const errores = [];
    pagina.on("pageerror", (e) => errores.push(e.message));
    const url = "https://127.0.0.1:8445";
    for (const ancho of [1440, 390]) {
      await pagina.setViewportSize({ width: ancho, height: 900 });
      await pagina.goto(url + "/acceso");
      assert.equal(
        await pagina.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      const resultado = await new AxeBuilder({ page: pagina })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      assert.deepEqual(
        resultado.violations.map((v) => v.id),
        [],
      );
      await pagina.screenshot({
        path: `.qa/capturas/acceso-${ancho}.png`,
        fullPage: true,
      });
    }
    const acceso = async (usuario, clave) => {
      await pagina.goto(url + "/acceso");
      await pagina.getByLabel("Usuario", { exact: true }).fill(usuario);
      await pagina.getByLabel("Contraseña", { exact: true }).fill(clave);
      await pagina
        .getByRole("button", { name: "Continuar", exact: true })
        .click();
    };
    etapa = "acceso_estudiante";
    await acceso("estudiante", estudiante);
    await pagina.waitForURL("**/estudiante");
    etapa = "disponibilidad";
    const botonDisponibilidad = pagina.getByRole("button", {
      name: "Comprobar acceso",
    });
    const cookieHTTPS = (await contexto.cookies()).find(
      (c) => c.name === "sobre_sesion",
    );
    assert.equal(cookieHTTPS.secure, true);
    assert.equal(cookieHTTPS.httpOnly, true);
    assert.equal(cookieHTTPS.sameSite, "Lax");
    const rutaDisponibilidad =
      await botonDisponibilidad.getAttribute("data-availability");
    const capturasHorarias = new Set();
    const comprobarDisponibilidad = async (codigo) => {
      let solicitudes = 0;
      const contar = (r) => {
        if (new URL(r.url()).pathname === rutaDisponibilidad) solicitudes++;
      };
      pagina.on("request", contar);
      const inicio = performance.now();
      const pendiente = pagina.waitForResponse(
        (r) => new URL(r.url()).pathname === rutaDisponibilidad,
      );
      await botonDisponibilidad.click();
      // Carga perceptible y bloqueo incluso frente a eventos repetidos por código.
      assert.equal(await botonDisponibilidad.isDisabled(), true);
      assert.equal(await botonDisponibilidad.getAttribute("aria-busy"), "true");
      assert.equal(
        await pagina.locator("[data-query-feedback]").textContent(),
        "Consultando el servidor...",
      );
      await botonDisponibilidad.evaluate((boton) => {
        boton.click();
        boton.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      });
      const respuesta = await pendiente;
      assert.equal(respuesta.status(), codigo);
      const decision = await respuesta.json();
      assert.equal(decision.autorizado, codigo === 200);
      assert.equal(decision.descarga_habilitada, false);
      assert.equal(respuesta.headers()["content-disposition"], undefined);
      const vista = decision.presentacion;
      await pagina.waitForFunction(
        () =>
          document.querySelector("[data-query-feedback]")?.dataset.state ===
          "complete",
      );
      assert.ok(
        performance.now() - inicio >= 550,
        "La carga debe ser perceptible, incluso con respuesta rápida",
      );
      assert.equal(
        solicitudes,
        1,
        "Las pulsaciones repetidas no duplican consultas",
      );
      pagina.off("request", contar);
      assert.equal(await botonDisponibilidad.isEnabled(), true);
      assert.equal(await botonDisponibilidad.getAttribute("aria-busy"), null);
      assert.equal(
        await pagina.locator("[data-query-feedback] strong").textContent(),
        "Verificación completada",
      );
      assert.equal(
        await pagina.locator("[data-query-feedback] time").count(),
        0,
      );
      assert.equal(
        await pagina.locator("[data-query-feedback]").textContent(),
        "Verificación completada",
      );
      await pagina.waitForFunction(
        (texto) =>
          document.querySelector("[data-availability-message]")?.textContent ===
          texto,
        vista.detalle,
      );
      assert.equal(
        await pagina.locator("[data-availability-title]").textContent(),
        vista.titulo,
      );
      if (decision.motivo === "evaluacion_no_asignada") {
        assert.equal(vista.estado, "restricted");
        assert.match(
          vista.mensaje,
          /Cumplir el horario no autoriza el acceso sin asignación/,
        );
        assert.equal(
          await pagina.locator("[data-time-display]").isHidden(),
          true,
        );
      }
      const limite = vista.reloj?.hora;
      if (
        ["7:59:59 a. m.", "8:00:00 a. m."].includes(limite) &&
        !capturasHorarias.has(limite)
      ) {
        capturasHorarias.add(limite);
        assert.equal(vista.apertura.hora, "8:00 a. m.");
        assert.equal(vista.reloj.fecha, "lunes, 9 de noviembre de 2026");
        assert.equal(
          vista.mensaje,
          codigo === 200
            ? "Horario cumplido. Acceso autorizado"
            : "Examen bloqueado. Falta 1 segundo para la apertura",
        );
        assert.equal(
          await pagina.locator("[data-lab-time]").textContent(),
          limite,
        );
        assert.equal(
          await pagina.locator("[data-open-time]").textContent(),
          "8:00 a. m.",
        );
        for (const ancho of [1440, 390]) {
          await pagina.setViewportSize({ width: ancho, height: 900 });
          assert.equal(
            await pagina.evaluate(
              () => document.documentElement.scrollWidth > innerWidth,
            ),
            false,
          );
          const accesibilidad = await new AxeBuilder({ page: pagina })
            .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
            .analyze();
          assert.deepEqual(
            accesibilidad.violations.map((v) => v.id),
            [],
          );
          await pagina.evaluate(() => document.activeElement?.blur());
          await pagina.screenshot({
            path: `.qa/capturas/hora-${codigo}-${ancho}.png`,
            fullPage: true,
          });
        }
      }
    };
    await comprobarDisponibilidad(403);
    administrarEnsayo("reloj", "fijar", "2026-11-09T08:00:00");
    await comprobarDisponibilidad(200);
    administrarEnsayo("reloj", "fijar", "2026-11-09T08:01:00");
    await comprobarDisponibilidad(200);
    administrarEnsayo("asignacion", "retirar");
    await comprobarDisponibilidad(403);
    administrarEnsayo("asignacion", "asignar");
    await comprobarDisponibilidad(200);
    administrarEnsayo("preparar", "--fecha", "2026-11-09");
    await comprobarDisponibilidad(403);
    administrarEnsayo("reloj", "normal");
    const estadoNormal = JSON.parse(administrarEnsayo("reloj", "estado"));
    assert.equal(estadoNormal.modo, "normal");
    administrarEnsayo("preparar", "--fecha", "2026-11-09");
    await comprobarDisponibilidad(403);
    resumen.push(
      "Disponibilidad real: 07:59:59 → 403; 08:00:00 y 08:01:00 → 200 sin archivo; sin asignación → 403; restauración → 403",
    );
    resumen.push(
      "Presentación: fecha española, reloj 12 h con segundos, apertura separada y estados exactos a 07:59:59/08:00; escritorio/móvil y axe A/AA correctos",
    );
    // Fallo de transporte deliberado: no se fabrica ninguna respuesta de autorización.
    await pagina.route("**" + rutaDisponibilidad, (ruta) =>
      ruta.abort("failed"),
    );
    await botonDisponibilidad.click();
    await pagina.waitForFunction(
      () =>
        document.querySelector("[data-query-feedback]")?.dataset.state ===
        "error",
    );
    assert.equal(await botonDisponibilidad.isEnabled(), true);
    assert.equal(
      await pagina.locator(".availability-result").getAttribute("data-state"),
      "error",
    );
    assert.equal(await pagina.locator("[data-time-display]").isHidden(), true);
    assert.equal(await pagina.locator("[data-query-feedback] time").count(), 0);
    assert.match(
      await pagina.locator("[data-availability-title]").textContent(),
      /no verificada/,
    );
    await pagina.screenshot({
      path: ".qa/capturas/consulta-error-390.png",
      fullPage: true,
    });
    await pagina.unroute("**" + rutaDisponibilidad);
    await comprobarDisponibilidad(403);
    resumen.push(
      "4 comprobaciones del botón aprobadas: carga perceptible (mínimo 600 ms), confirmación sin hora real visible, error sin confirmación anterior y pulsaciones repetidas con una sola petición; recuperación real correcta",
    );
    assert.equal(
      (await contexto.cookies()).find((c) => c.name === "sobre_sesion")
        .httpOnly,
      true,
    );
    for (const ancho of [1440, 390]) {
      await pagina.setViewportSize({ width: ancho, height: 900 });
      assert.equal(
        await pagina.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      const resultado = await new AxeBuilder({ page: pagina })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      assert.deepEqual(
        resultado.violations.map((v) => v.id),
        [],
      );
      await pagina.screenshot({
        path: `.qa/capturas/panel-estudiante-${ancho}.png`,
        fullPage: true,
      });
    }
    assert.equal((await pagina.goto(url + "/docente")).status(), 403);
    await pagina.goto(url + "/estudiante");
    etapa = "salida_estudiante";
    await pagina.getByRole("button", { name: "Cerrar sesión" }).click();
    await pagina.waitForURL("**/acceso");
    assert.equal((await pagina.goto(url + "/estudiante")).status(), 401);
    resumen.push(
      "Estudiante: acceso real, RBAC 403 por URL docente, salida y posterior 401",
    );

    etapa = "acceso_docente";
    await acceso("docente", docente);
    await pagina.waitForURL("**/acceso/totp");
    assert.equal((await pagina.goto(url + "/docente")).status(), 401);
    await pagina.goto(url + "/acceso/totp");
    await pagina.screenshot({
      path: ".qa/capturas/totp-390.png",
      fullPage: true,
    });
    const codigo = docker([
      "exec",
      "-T",
      "app",
      "python",
      "-c",
      "import pyotp; from app.security import leer_secreto; from app.config import configuracion_entorno; print(pyotp.TOTP(leer_secreto(configuracion_entorno())).now())",
    ]).trim();
    // Adelantar solo el reloj del recurso no debe invalidar el desafío ni el OTP.
    administrarEnsayo("reloj", "fijar", "2035-01-01T08:01:00");
    etapa = "validar_totp";
    await pagina.getByLabel("Código del autenticador").fill(codigo);
    await pagina.getByRole("button", { name: "Verificar identidad" }).click();
    await pagina.waitForURL("**/docente");
    assert.match(
      await pagina.locator("body").textContent(),
      /Contraseña y segundo factor validados/,
    );
    const resultado = await new AxeBuilder({ page: pagina })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    assert.deepEqual(
      resultado.violations.map((v) => v.id),
      [],
    );
    await pagina.screenshot({
      path: ".qa/capturas/panel-docente-390.png",
      fullPage: true,
    });
    etapa = "publicacion_real_etapa3";
    const original = Buffer.from(
      "EL SOBRE DE LAS OCHO\nParcial ficticio publicado desde el navegador.\n",
    );
    await pagina.locator('input[type="file"]').setInputFiles({
      name: "parcial-demo.txt",
      mimeType: "text/plain",
      buffer: original,
    });
    assert.match(
      await pagina.locator('input[type="file"]').inputValue(),
      /parcial-demo.txt$/,
    );
    await pagina
      .getByRole("button", { name: "Publicar documento protegido" })
      .click();
    await pagina.waitForURL("**/docente?publicado=1");
    assert.match(
      await pagina.locator("body").textContent(),
      /Documento almacenado y protegido correctamente/,
    );
    const sobreEstado = () => JSON.parse(administrarEnsayo("sobre", "estado"));
    const publicado = sobreEstado();
    assert.equal(publicado.integridad, true);
    assert.equal(publicado.autenticacion_gcm, "correcta");
    for (const ancho of [1440, 390]) {
      await pagina.setViewportSize({ width: ancho, height: 900 });
      assert.equal(
        await pagina.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      const axe = await new AxeBuilder({ page: pagina })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      assert.deepEqual(
        axe.violations.map((v) => v.id),
        [],
      );
      await pagina.screenshot({
        path: `.qa/capturas/sobre-docente-${ancho}.png`,
        fullPage: true,
      });
    }
    await pagina.getByRole("button", { name: "Cerrar sesión" }).click();
    await pagina.waitForURL("**/acceso");
    etapa = "entrega_real_etapa3";
    await acceso("estudiante", estudiante);
    await pagina.waitForURL("**/estudiante");
    administrarEnsayo("reloj", "fijar", "2026-11-09T07:59:59");
    const rutaDocumento = url + "/evaluaciones/evaluacion-001/documento";
    assert.equal((await pagina.request.get(rutaDocumento)).status(), 403);
    await pagina.getByRole("button", { name: "Comprobar acceso" }).click();
    await pagina.waitForFunction(
      () =>
        document.querySelector("[data-query-feedback]")?.dataset.state ===
        "complete",
    );
    assert.equal(await pagina.locator("[data-download]").isHidden(), true);
    administrarEnsayo("reloj", "fijar", "2026-11-09T08:00:00");
    const comprobarSobre = async (codigo) => {
      const pendiente = pagina.waitForResponse(
        (r) => new URL(r.url()).pathname === rutaDisponibilidad,
      );
      await pagina.getByRole("button", { name: "Comprobar acceso" }).click();
      assert.equal((await pendiente).status(), codigo);
      await pagina.waitForFunction(
        () =>
          document.querySelector("[data-query-feedback]")?.dataset.state ===
          "complete",
      );
      assert.equal(
        await pagina.locator("[data-download]").isVisible(),
        codigo === 200,
      );
    };
    await comprobarSobre(200);
    const [descarga] = await Promise.all([
      pagina.waitForEvent("download"),
      pagina.getByRole("link", { name: "Descargar documento" }).click(),
    ]);
    assert.equal(descarga.suggestedFilename(), "parcial-demo.txt");
    assert.deepEqual(fs.readFileSync(await descarga.path()), original);
    for (const ancho of [1440, 390]) {
      await pagina.setViewportSize({ width: ancho, height: 900 });
      assert.equal(
        await pagina.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
      );
      const axe = await new AxeBuilder({ page: pagina })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      assert.deepEqual(
        axe.violations.map((v) => v.id),
        [],
      );
      await pagina.screenshot({
        path: `.qa/capturas/sobre-estudiante-${ancho}.png`,
        fullPage: true,
      });
    }
    etapa = "persistencia_real_etapa3";
    docker(["restart"]);
    docker(["up", "-d", "--wait", "--wait-timeout", "90"]);
    assert.deepEqual(
      await (await pagina.request.get(rutaDocumento)).body(),
      original,
    );
    assert.equal(sobreEstado().sha256_original, publicado.sha256_original);
    for (const alteracion of ["alterar-gcm", "alterar-hash"]) {
      administrarEnsayo("sobre", alteracion);
      const estado = sobreEstado();
      assert.equal(estado.sha256_original, publicado.sha256_original);
      assert.equal(
        estado.autenticacion_gcm,
        alteracion === "alterar-hash" ? "correcta" : "no_superada",
      );
      const rechazo = await pagina.request.get(rutaDocumento);
      assert.equal(rechazo.status(), 409);
      assert.equal((await rechazo.body()).includes(original), false);
      await comprobarSobre(409);
      assert.match(
        await pagina.locator("[data-document-message]").textContent(),
        /integridad/,
      );
      await pagina.screenshot({
        path: `.qa/capturas/sobre-${alteracion}-390.png`,
        fullPage: true,
      });
      administrarEnsayo("sobre", "restaurar");
      assert.deepEqual(
        await (await pagina.request.get(rutaDocumento)).body(),
        original,
      );
    }
    administrarEnsayo("asignacion", "retirar");
    assert.equal((await pagina.request.get(rutaDocumento)).status(), 403);
    administrarEnsayo("asignacion", "asignar");
    await comprobarSobre(200);
    const eventosSobre = JSON.parse(administrarEnsayo("sobre", "auditoria"));
    for (const motivo of [
      "sobre_publicado",
      "autenticacion_gcm_fallida",
      "discrepancia_sha256",
      "restaurar",
      "evaluacion_no_asignada",
      "original_verificado",
      "fuera_de_horario",
    ]) {
      assert.equal(
        eventosSobre.some((e) => e.motivo === motivo),
        true,
        motivo,
      );
    }
    const anonimo = await navegador.newContext();
    assert.equal((await anonimo.request.get(rutaDocumento)).status(), 401);
    await anonimo.close();
    await pagina.getByRole("button", { name: "Cerrar sesión" }).click();
    await pagina.waitForURL("**/acceso");
    resumen.push(
      "Etapa 3 real: carga docente por navegador, cifrado privado, descarga byte a byte a 08:00, 403 a 07:59:59/sin asignación, 401 anónimo, reinicio conserva claves/sesión/documento; GCM dañado y SHA discrepante → 409 sin archivo; restauración → original idéntico; auditoría y escritorio/móvil axe A/AA correctos",
    );
    resumen.push(
      "Docente: contraseña insuficiente, TOTP real aceptado, panel privado y salida",
    );
    resumen.push(
      "TOTP real y desafío conservados al fijar el reloj de evaluaciones en 2035",
    );
    const auditoria = JSON.parse(
      docker([
        "exec",
        "-T",
        "app",
        "python",
        "-c",
        "import json; from app.db import conexion; from app.config import configuracion_entorno; db=__import__('sqlite3').connect(configuracion_entorno().base_datos); db.row_factory=__import__('sqlite3').Row; print(json.dumps([dict(f) for f in db.execute(\"select * from eventos where accion='consultar_disponibilidad'\")]))",
      ]),
    );
    assert.equal(
      auditoria.some((e) => e.motivo === "fuera_de_horario"),
      true,
    );
    assert.equal(
      auditoria.some((e) => e.motivo === "apertura_cumplida"),
      true,
    );
    assert.equal(
      auditoria.some((e) => e.motivo === "evaluacion_no_asignada"),
      true,
    );
    assert.equal(
      auditoria.every(
        (e) =>
          e.evaluacion_id &&
          e.instante_didactico &&
          Number.isInteger(e.instante),
      ),
      true,
    );
    for (const sensible of [estudiante, docente, codigo])
      assert.equal(JSON.stringify(auditoria).includes(sensible), false);
    resumen.push(
      "Auditoría real de autorización: recurso, usuario, decisión y dos tiempos, sin credenciales",
    );
    assert.deepEqual(errores, []);
    const marcaPrivada = randomBytes(16).toString("hex");
    await pagina.request.get(`${url}/health?control_privado=${marcaPrivada}`);
    const logs = docker(["logs", "--no-color"]);
    assert.equal(logs.includes(marcaPrivada), false);
    for (const sensible of [estudiante, docente, codigo])
      assert.equal(logs.includes(sensible), false);
    resumen.push(
      "Acceso y paneles: escritorio/móvil sin desbordamiento; axe A/AA sin infracciones; sin excepciones JS",
    );
    resumen.push(
      "Credenciales y código no aparecen en logs; contenedores de prueba aislados del volumen real",
    );
    fs.writeFileSync(".qa/identidad-resultados.txt", resumen.join("\n") + "\n");
    console.log(resumen.join("\n"));
  } catch (error) {
    // Solo el encabezado del error: los registros de acciones pueden contener campos.
    console.error(etapa, error.name, String(error.message).split("\n")[0]);
    console.error(respuestas.slice(-8).join("\n"));
    throw error;
  } finally {
    if (navegador) await navegador.close();
    docker(["down", "--volumes"]);
  }
}

verificar().catch(() => {
  console.error(
    "La verificación de identidad falló. Revise los asertos del script; no se imprimen credenciales.",
  );
  process.exitCode = 1;
});
