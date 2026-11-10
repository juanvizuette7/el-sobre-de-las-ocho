"use strict";

// El navegador presenta la decisión recibida; no compara fechas ni concede permisos.
document.querySelectorAll("[data-availability]").forEach((boton) => {
  boton.addEventListener("click", async () => {
    const resultado = document.getElementById(
      boton.getAttribute("aria-controls"),
    );
    const controlador = new AbortController();
    const mensaje = resultado.querySelector("[data-availability-message]");
    const reloj = boton
      .closest(".evaluation-card")
      .querySelector("[data-time-display]");
    const espera = window.setTimeout(() => controlador.abort(), 5000);
    boton.disabled = true;
    boton.setAttribute("aria-busy", "true");
    mensaje.textContent = "Consultando disponibilidad…";
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
        typeof decision.autorizado !== "boolean" ||
        typeof decision.presentacion?.mensaje !== "string" ||
        !["ok", "restricted"].includes(decision.presentacion.estado)
      ) {
        throw new Error("Respuesta no válida");
      }
      const vista = decision.presentacion;
      if (
        vista.estado === "ok" &&
        !(respuesta.status === 200 && decision.autorizado)
      ) {
        throw new Error("Respuesta no coherente");
      }
      mensaje.textContent = vista.mensaje;
      resultado.dataset.state = vista.estado;
      if (reloj) {
        reloj.hidden = !vista.reloj || !vista.apertura;
        // Los textos y el instante ISO proceden del servidor, sin reloj local ni cuenta atrás.
        for (const [tipo, datos] of [
          ["lab", vista.reloj],
          ["open", vista.apertura],
        ]) {
          const hora = reloj.querySelector(`[data-${tipo}-time]`);
          hora.textContent = datos?.hora || "";
          hora.dateTime = datos?.iso || "";
          reloj.querySelector(`[data-${tipo}-date]`).textContent =
            datos?.fecha || "";
        }
      }
    } catch {
      mensaje.textContent =
        "No fue posible comprobar la disponibilidad. Inténtalo de nuevo.";
      resultado.dataset.state = "error";
      if (reloj) reloj.hidden = true;
    } finally {
      window.clearTimeout(espera);
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
    }
  });
});
