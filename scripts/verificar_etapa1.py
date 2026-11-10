"""Comprueba el portal real desde Windows con Python estándar y Docker CLI.

Ejecutar desde la raíz, después de docker compose up -d --wait.
No sustituye P1–P10 ni realiza pruebas ofensivas.
"""

import json
import subprocess
import urllib.error
import urllib.request

URL_PORTAL = "http://127.0.0.1:8080"


def comando_docker(*argumentos: str) -> str:
    """Ejecuta un comando de solo lectura y propaga un fallo de Docker."""
    return subprocess.check_output(["docker", *argumentos], text=True, encoding="utf-8")


def comprobar(condicion: bool, descripcion: str) -> None:
    """Detiene la verificación ante un resultado distinto al esperado."""
    if not condicion:
        raise RuntimeError(descripcion)
    print(f"OK: {descripcion}")


def verificar() -> None:
    """Valida exposición, salud y respuestas del proxy que se está ejecutando."""
    configuracion = json.loads(comando_docker("compose", "config", "--format", "json"))
    comprobar(set(configuracion["services"]) == {"app", "nginx"}, "exactamente dos servicios principales")
    for servicio in ["app", "nginx"]:
        identificador = comando_docker("compose", "ps", "-q", servicio).strip()
        comprobar(bool(identificador), f"contenedor {servicio} iniciado")
        contenedor = json.loads(comando_docker("inspect", identificador))[0]
        comprobar(contenedor["State"]["Health"]["Status"] == "healthy", f"salud Docker de {servicio}")
        comprobar(contenedor["Config"]["User"] not in {"", "0", "root"}, f"{servicio} ejecuta sin root")
        comprobar(contenedor["HostConfig"]["ReadonlyRootfs"], f"sistema de archivos de {servicio} de solo lectura")
        enlaces = contenedor["HostConfig"].get("PortBindings") or {}
        if servicio == "app":
            comprobar(not enlaces, "FastAPI no publica puertos en Windows")
            redes = contenedor["NetworkSettings"]["Networks"]
            comprobar(len(redes) == 1, "FastAPI solo pertenece a una red")
            red = json.loads(comando_docker("network", "inspect", next(iter(redes))))[0]
            comprobar(red["Internal"], "la red de FastAPI es interna")
        else:
            comprobar(enlaces == {"8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8080"}]}, "Nginx solo publica 127.0.0.1:8080")

    with urllib.request.urlopen(URL_PORTAL + "/health", timeout=5) as respuesta:
        comprobar(respuesta.status == 200, "salud HTTP 200 a través de Nginx")
        comprobar(json.load(respuesta) == {"status": "ok", "servicio": "el-sobre-de-las-ocho", "etapa": 1}, "contrato JSON de salud")
        comprobar(respuesta.headers.get("Server") == "nginx", "banner sin número de versión")
        comprobar(respuesta.headers.get("X-Content-Type-Options") == "nosniff", "cabecera nosniff")
        comprobar(respuesta.headers.get("X-Frame-Options") == "SAMEORIGIN", "cabecera SAMEORIGIN")
        comprobar(bool(respuesta.headers.get("Content-Security-Policy")), "política de recursos del mismo origen")

    for ruta, tipo in [("/", "text/html"), ("/static/styles.css", "text/css"), ("/static/main.js", "javascript"), ("/static/favicon.svg", "image/svg+xml")]:
        with urllib.request.urlopen(URL_PORTAL + ruta, timeout=5) as respuesta:
            comprobar(respuesta.status == 200 and tipo in respuesta.headers["Content-Type"], f"recurso y tipo de contenido {ruta}")
    for ruta in ["/.env", "/docs/RESUMEN_PROYECTO.md", "/docente", "/descargar"]:
        try:
            urllib.request.urlopen(URL_PORTAL + ruta, timeout=5)
        except urllib.error.HTTPError as error:
            comprobar(error.code == 404, f"ruta no publicada {ruta}")
        else:
            raise RuntimeError(f"Ruta inesperadamente accesible: {ruta}")


if __name__ == "__main__":
    verificar()
