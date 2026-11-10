"use strict";

// El envío sigue siendo HTML nativo: los controles de seguridad son del servidor.
document.querySelectorAll("[data-auth-form]").forEach((formulario) => {
  formulario.addEventListener("submit", () => {
    formulario.querySelector('button[type="submit"]').disabled = true;
    formulario.setAttribute("aria-busy", "true");
    formulario.querySelector(".form-status").textContent =
      "Procesando solicitud…";
  });
});
const errorFormulario = document.querySelector(".form-error");
if (errorFormulario) errorFormulario.focus();

// Restaura controles cuando el navegador recupera una página de su historial.
window.addEventListener("pageshow", () => {
  document.querySelectorAll("[data-auth-form]").forEach((formulario) => {
    formulario.removeAttribute("aria-busy");
    formulario.querySelector('button[type="submit"]').disabled = false;
    formulario.querySelector(".form-status").textContent = "";
  });
});
