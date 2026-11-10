"use strict";

// El navegador presenta la decisión recibida; no compara fechas ni concede permisos.
document.querySelectorAll("[data-availability]").forEach((boton) => {
  boton.addEventListener("click", async () => {
    if (boton.disabled) return;
    const tarjeta = boton.closest(".evaluation-card");
    const resultado = tarjeta.querySelector(".availability-result");
    const confirmacion = tarjeta.querySelector("[data-query-feedback]");
    const descarga = tarjeta.querySelector("[data-download]");
    const documento = tarjeta.querySelector("[data-document-message]");
    const controlador = new AbortController();
    const mensaje = resultado.querySelector("[data-availability-message]");
    const titulo = resultado.querySelector("[data-availability-title]");
    const reloj = boton
      .closest(".evaluation-card")
      .querySelector("[data-time-display]");
    const espera = window.setTimeout(() => controlador.abort(), 5000);
    boton.disabled = true;
    boton.setAttribute("aria-busy", "true");
    confirmacion.textContent = "Consultando el servidor...";
    confirmacion.dataset.state = "loading";
    mensaje.textContent = "Esperando respuesta del servidor.";
    titulo.textContent = "Comprobando acceso";
    resultado.dataset.state = "loading";
    if (descarga) descarga.hidden = true;
    // Duración mínima de la indicación visual, independiente del tiempo de red.
    // La petición se inicia inmediatamente; este plazo no representa procesamiento.
    const indicacionVisible = new Promise((resolver) =>
      window.setTimeout(resolver, 600),
    );
    try {
      const respuesta = await fetch(boton.dataset.availability, {
        cache: "no-store",
        signal: controlador.signal,
        headers: { Accept: "application/json" },
      });
      const decision = await respuesta.json();
      window.clearTimeout(espera);
      if (
        respuesta.status >= 500 ||
        typeof decision.mensaje !== "string" ||
        typeof decision.autorizado !== "boolean" ||
        typeof decision.presentacion?.mensaje !== "string" ||
        typeof decision.presentacion?.titulo !== "string" ||
        typeof decision.presentacion?.detalle !== "string" ||
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
      await indicacionVisible;
      titulo.textContent = vista.titulo;
      mensaje.textContent = vista.detalle;
      resultado.dataset.state = vista.estado;
      if (documento) documento.textContent = decision.estado_documento;
      if (descarga) descarga.hidden = decision.descarga_habilitada !== true;
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
      const etiqueta = document.createElement("strong");
      etiqueta.textContent = "Verificación completada";
      confirmacion.replaceChildren(etiqueta);
      confirmacion.dataset.state = "complete";
    } catch {
      window.clearTimeout(espera);
      await indicacionVisible;
      titulo.textContent = "Disponibilidad no verificada";
      mensaje.textContent =
        "No fue posible comprobar la disponibilidad. Inténtalo de nuevo.";
      resultado.dataset.state = "error";
      if (reloj) reloj.hidden = true;
      if (documento)
        documento.textContent = "Disponibilidad del documento no verificada.";
      if (descarga) descarga.hidden = true;
      confirmacion.textContent =
        "La verificación no se completó. Vuelve a comprobar el acceso.";
      confirmacion.dataset.state = "error";
    } finally {
      window.clearTimeout(espera);
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
    }
  });
});
