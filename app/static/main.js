"use strict";

const botonSalud = document.querySelector("#health-check");
const resultadoSalud = document.querySelector("#health-result");

// La consulta de salud comprueba disponibilidad; no valida controles de entrega.
if (botonSalud && resultadoSalud)
  botonSalud.addEventListener("click", async () => {
    botonSalud.disabled = true;
    botonSalud.setAttribute("aria-busy", "true");
    resultadoSalud.textContent = "Consultando disponibilidad…";
    resultadoSalud.dataset.state = "loading";
    const controlador = new AbortController();
    const tiempoLimite = window.setTimeout(() => controlador.abort(), 5000);

    try {
      const respuesta = await fetch("/health", {
        cache: "no-store",
        signal: controlador.signal,
        headers: { Accept: "application/json" },
      });
      if (!respuesta.ok) throw new Error("Respuesta no disponible");
      const datos = await respuesta.json();
      if (
        datos.status !== "ok" ||
        datos.servicio !== "el-sobre-de-las-ocho" ||
        datos.etapa !== 1
      ) {
        throw new Error("Respuesta inesperada");
      }
      resultadoSalud.textContent = "El portal está disponible.";
      resultadoSalud.dataset.state = "ok";
    } catch {
      resultadoSalud.textContent =
        "No fue posible comprobar la disponibilidad del portal. Inténtalo de nuevo.";
      resultadoSalud.dataset.state = "error";
    } finally {
      window.clearTimeout(tiempoLimite);
      botonSalud.disabled = false;
      botonSalud.removeAttribute("aria-busy");
    }
  });
