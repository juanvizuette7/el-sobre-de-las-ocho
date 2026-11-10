"use strict";

// El navegador presenta la decisión recibida; no compara fechas ni concede permisos.
document.querySelectorAll("[data-availability]").forEach((boton) => {
  boton.addEventListener("click", async () => {
    const resultado = document.getElementById(
      boton.getAttribute("aria-controls"),
    );
    const controlador = new AbortController();
    const espera = window.setTimeout(() => controlador.abort(), 5000);
    boton.disabled = true;
    boton.setAttribute("aria-busy", "true");
    resultado.textContent = "Consultando disponibilidad…";
    resultado.dataset.state = "loading";
    try {
      const respuesta = await fetch(boton.dataset.availability, {
        cache: "no-store",
        signal: controlador.signal,
        headers: { Accept: "application/json" },
      });
      const decision = await respuesta.json();
      if (
        typeof decision.mensaje !== "string" ||
        typeof decision.autorizado !== "boolean"
      ) {
        throw new Error("Respuesta no válida");
      }
      resultado.textContent = decision.mensaje;
      resultado.dataset.state =
        respuesta.status === 200 && decision.autorizado ? "ok" : "restricted";
    } catch {
      resultado.textContent =
        "No fue posible comprobar la disponibilidad. Inténtalo de nuevo.";
      resultado.dataset.state = "error";
    } finally {
      window.clearTimeout(espera);
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
    }
  });
});
