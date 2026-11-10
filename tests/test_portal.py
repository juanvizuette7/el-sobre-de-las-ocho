"""Contratos de la etapa 1: salud real, portada honesta y recursos públicos."""

from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.main import crear_aplicacion


@pytest.fixture
def cliente(tmp_path):
    """Proporciona peticiones HTTP sin depender de un servidor externo."""
    with TestClient(crear_aplicacion(Configuracion(tmp_path)), base_url="http://127.0.0.1:8080") as cliente_http:
        yield cliente_http


def test_salud_tiene_contrato_minimo(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "status": "ok", "servicio": "el-sobre-de-las-ocho", "etapa": 1,
    }


class RecursosHTML(HTMLParser):
    """Obtiene recursos y enlaces internos de la portada ya renderizada."""

    def __init__(self):
        super().__init__()
        self.recursos = []
        self.enlaces = []
        self.ids = set()
        self.formularios = 0

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if "id" in atributos:
            self.ids.add(atributos["id"])
        if tag in {"script", "img"}:
            self.recursos.append(atributos["src"])
        if tag == "link":
            self.recursos.append(atributos["href"])
        if tag == "a":
            self.enlaces.append(atributos["href"])
        if tag == "form":
            self.formularios += 1


def test_portada_y_recursos_funcionan_sin_servicios_externos(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert '<html lang="es">' in respuesta.text
    assert "La entrega de exámenes aún no está habilitada" in respuesta.text
    assert all(nombre in respuesta.text for nombre in ["Portal docente", "Portal estudiante", "Laboratorio de seguridad"])
    assert 'id="recorrido"' not in respuesta.text
    assert "Acceso administrativo pendiente de habilitación" in respuesta.text
    pagina = RecursosHTML()
    pagina.feed(respuesta.text)
    assert pagina.formularios == 0
    assert not any("laboratorio" in enlace or "admin" in enlace for enlace in pagina.enlaces)
    # Sin autenticación implementada, no existe ninguna entrada administrativa.
    for ruta_administrativa in ["/laboratorio", "/admin", "/admin/laboratorio"]:
        assert cliente.get(ruta_administrativa).status_code == 404
    for enlace in pagina.enlaces:
        if enlace.startswith("#"):
            assert enlace[1:] in pagina.ids
        else:
            assert cliente.get(enlace).status_code == 200
    for recurso in pagina.recursos:
        # Las URL generadas pueden ser absolutas, pero deben pertenecer al portal.
        assert recurso.startswith(("http://127.0.0.1:8080/static/", "/static/"))
        assert cliente.get(recurso).status_code == 200


@pytest.mark.parametrize("ruta,codigo", [("/.env",404), ("/docs/RESUMEN_PROYECTO.md",404), ("/static/../main.py",404), ("/docente",401), ("/descargar",404), ("/docs",404), ("/openapi.json",404)])
def test_rutas_no_publicas_o_futuras_no_existen(cliente, ruta, codigo):
    assert cliente.get(ruta).status_code == codigo
