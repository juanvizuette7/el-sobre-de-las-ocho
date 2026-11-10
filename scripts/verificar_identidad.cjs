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
      PORTAL_ORIGIN: http://127.0.0.1:8081
    read_only: true
    tmpfs:
      - /data:uid=10001,gid=10001,mode=0700
      - /tmp
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
    ports: ["127.0.0.1:8081:8080"]
    volumes:
      - type: bind
        source: ${ruta("infra/nginx/nginx.conf")}
        target: /etc/nginx/nginx.conf
        read_only: true
      - type: bind
        source: ${ruta("infra/nginx/default.conf")}
        target: /etc/nginx/conf.d/default.conf
        read_only: true
    networks: [entrada, portal]
    depends_on:
      app:
        condition: service_healthy
networks:
  entrada: {}
  portal:
    internal: true
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
    navegador = await chromium.launch({ channel: "chrome", headless: true });
    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();
    pagina.on("response", (r) =>
      respuestas.push(
        `${r.request().method()} ${new URL(r.url()).pathname} ${r.status()}`,
      ),
    );
    const errores = [];
    pagina.on("pageerror", (e) => errores.push(e.message));
    const url = "http://127.0.0.1:8081";
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
    await pagina.getByRole("button", { name: "Cerrar sesión" }).click();
    await pagina.waitForURL("**/acceso");
    resumen.push(
      "Docente: contraseña insuficiente, TOTP real aceptado, panel privado y salida",
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
    docker(["down"]);
  }
}

verificar().catch(() => {
  console.error(
    "La verificación de identidad falló. Revise los asertos del script; no se imprimen credenciales.",
  );
  process.exitCode = 1;
});
