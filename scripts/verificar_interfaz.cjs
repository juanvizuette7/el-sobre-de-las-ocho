/* Revisión opcional en Chrome instalado; Playwright vive en .qa, fuera del portal. */
const { chromium } = require("../.qa/node_modules/playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const AxeBuilder = require("../.qa/node_modules/@axe-core/playwright").default;

async function verificar() {
  fs.mkdirSync(".qa/capturas", { recursive: true });
  const navegador = await chromium.launch({
    channel: "chrome",
    headless: true,
  });
  const errores = [];
  const resumen = [];
  try {
    const contexto = await navegador.newContext();
    const pagina = await contexto.newPage();
    pagina.on("pageerror", (error) => errores.push(error.message));
    const peticionesExternas = [];
    pagina.on("request", (request) => {
      if (!request.url().startsWith("https://127.0.0.1:8443/"))
        peticionesExternas.push(request.url());
    });
    for (const ancho of [1440, 768, 390, 320]) {
      await pagina.setViewportSize({ width: ancho, height: 900 });
      const respuesta = await pagina.goto("https://127.0.0.1:8443/", {
        waitUntil: "networkidle",
      });
      assert.equal(respuesta.status(), 200);
      await pagina.locator("h1").waitFor();
      // Medimos el estado final, sin muestrear colores durante la entrada animada.
      await pagina.locator(".envelope-art").evaluate(async (elemento) => {
        await Promise.all(
          elemento.getAnimations().map((animacion) => animacion.finished),
        );
      });
      assert.equal(
        await pagina.evaluate(
          () => document.documentElement.scrollWidth > window.innerWidth,
        ),
        false,
        `Desbordamiento a ${ancho}px`,
      );
      await pagina.screenshot({
        path: `.qa/capturas/portal-${ancho}.png`,
        fullPage: true,
      });
      resumen.push(
        `Portada ${ancho}px: HTTP 200, sin desbordamiento horizontal`,
      );
      const accesibilidad = await new AxeBuilder({ page: pagina })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      assert.deepEqual(
        accesibilidad.violations.map(({ id, nodes }) => ({
          id,
          elementos: nodes.map(({ target }) => target),
        })),
        [],
        `Accesibilidad a ${ancho}px`,
      );
      resumen.push(
        `axe WCAG A/AA ${ancho}px: sin infracciones detectadas automáticamente`,
      );
    }
    await pagina.keyboard.press("Tab");
    assert.equal(
      await pagina
        .locator(".skip-link")
        .evaluate((elemento) => elemento === document.activeElement),
      true,
    );
    await pagina.keyboard.press("Enter");
    assert.equal(await pagina.evaluate(() => location.hash), "#contenido");
    await pagina.getByRole("link", { name: "Conocer el portal" }).click();
    assert.equal(await pagina.evaluate(() => location.hash), "#areas");
    resumen.push(
      "Teclado: salto a contenido y navegación por anclas correctos",
    );

    const boton = pagina.getByRole("button", { name: "Comprobar conexión" });
    const resultado = pagina.locator("#health-result");
    await boton.click();
    await pagina.waitForFunction(
      () => document.querySelector("#health-result").dataset.state === "ok",
    );
    assert.equal(await resultado.textContent(), "El portal está disponible.");
    resumen.push("Botón de salud: respuesta real correcta");
    await pagina.route("**/health", (ruta) =>
      ruta.fulfill({ status: 503, body: "No disponible" }),
    );
    await boton.click();
    await pagina.waitForFunction(
      () => document.querySelector("#health-result").dataset.state === "error",
    );
    assert.equal(await boton.isEnabled(), true);
    resumen.push(
      "Fallo HTTP simulado solo en navegador: mensaje de error y botón recuperado",
    );
    await pagina.unroute("**/health");
    await pagina.route("**/health", (ruta) =>
      ruta.fulfill({
        status: 200,
        contentType: "application/json",
        body: '{"status":"ok"}',
      }),
    );
    await boton.click();
    await pagina.waitForFunction(
      () => document.querySelector("#health-result").dataset.state === "error",
    );
    resumen.push("Contrato JSON incompleto simulado: no muestra éxito");
    await pagina.unroute("**/health");
    await pagina.route("**/health", async (ruta) => {
      await new Promise((resolve) => setTimeout(resolve, 5500));
      await ruta.abort().catch(() => {});
    });
    await boton.click();
    await pagina.waitForFunction(
      () => document.querySelector("#health-result").dataset.state === "error",
      null,
      { timeout: 7000 },
    );
    assert.equal(await boton.isEnabled(), true);
    resumen.push("Espera superior a 5 s simulada: timeout y botón recuperado");
    await pagina.unroute("**/health");
    await pagina.emulateMedia({ reducedMotion: "reduce" });
    assert.equal(
      await pagina
        .locator(".envelope-art")
        .evaluate((elemento) => getComputedStyle(elemento).animationName),
      "none",
    );
    resumen.push("Preferencia de movimiento reducido respetada");
    assert.deepEqual(errores, []);
    assert.deepEqual(peticionesExternas, []);
    const sinJavaScript = await navegador.newContext({
      javaScriptEnabled: false,
    });
    const paginaSimple = await sinJavaScript.newPage();
    await paginaSimple.goto("https://127.0.0.1:8443/");
    assert.equal(await paginaSimple.locator("noscript a").isVisible(), true);
    await paginaSimple.locator("noscript a").click();
    assert.match(
      await paginaSimple.locator("body").textContent(),
      /"status":"ok"/,
    );
    resumen.push("Sin JavaScript: portada y alternativa de salud utilizables");
    resumen.push("Sin excepciones JavaScript ni peticiones externas");
    console.log(resumen.join("\n"));
    fs.writeFileSync(".qa/interfaz-resultados.txt", resumen.join("\n") + "\n");
  } finally {
    await navegador.close();
  }
}

verificar().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
