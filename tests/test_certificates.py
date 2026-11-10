"""Regresión de certificados TLS y recursos seguros del portal."""

import shutil

import pytest
from cryptography import x509
from fastapi.testclient import TestClient

from app.certificates import comprobar, generar
from app.config import Configuracion
from app.main import crear_aplicacion


@pytest.fixture(scope="module")
def certificados(tmp_path_factory):
    ruta = tmp_path_factory.mktemp("ca-local")
    generar(ruta)
    return ruta


def test_certificado_cadena_san_vigencia_y_persistencia(certificados):
    original = (certificados / "ca/ca.key").read_bytes()
    assert comprobar(certificados)["san"] == ["127.0.0.1", "localhost"]
    assert generar(certificados)["sha256_ca"] == comprobar(certificados)["sha256_ca"]
    assert (certificados / "ca/ca.key").read_bytes() == original
    cert = x509.load_pem_x509_certificate((certificados / "nginx/server.crt").read_bytes())
    assert not cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca


@pytest.mark.parametrize("archivo", ["nginx/server.key", "nginx/server.crt", "ca/ca.crt"])
def test_certificados_incompletos_no_regeneran(certificados, tmp_path, archivo):
    copia = tmp_path / "certs"
    shutil.copytree(certificados, copia)
    privada = (copia / "ca/ca.key").read_bytes()
    (copia / archivo).unlink()
    with pytest.raises(ValueError):
        generar(copia)
    assert (copia / "ca/ca.key").read_bytes() == privada


def test_certificado_y_clave_incompatibles_rechazados(certificados, tmp_path):
    copia = tmp_path / "certs"
    shutil.copytree(certificados, copia)
    (copia / "nginx/server.key").write_bytes((copia / "lab/server.key").read_bytes())
    with pytest.raises(ValueError):
        comprobar(copia)


def test_cookie_secure_y_recursos_del_mismo_origen(tmp_path):
    config = Configuracion(tmp_path, origen="https://127.0.0.1:8443")
    with TestClient(crear_aplicacion(config), base_url=config.origen) as cliente:
        respuesta = cliente.get("/acceso")
        cookie = respuesta.headers["set-cookie"].lower()
        assert "secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
        assert 'href="/static/' in respuesta.text
        assert 'src="http://' not in respuesta.text and 'href="http://' not in respuesta.text
