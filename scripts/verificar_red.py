"""Pruebas reales de TLS/certificados/redirección; no envía credenciales ni toca datos privados."""

import json
import socket
import ssl
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CA = RAIZ / "certs/ca/ca.crt"


class SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, nueva_url):
        return None


def verificar():
    resultados = []
    contexto = ssl.create_default_context(cafile=str(CA))
    for nombre in ("127.0.0.1", "localhost"):
        with socket.create_connection(("127.0.0.1", 8443), timeout=5) as red:
            with contexto.wrap_socket(red, server_hostname=nombre) as tls:
                assert tls.version() in ("TLSv1.2", "TLSv1.3")
                resultados.append(f"Certificado/cadena/SAN validado para {nombre}")
    for version in (ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3):
        especifico = ssl.create_default_context(cafile=str(CA))
        especifico.minimum_version = especifico.maximum_version = version
        with socket.create_connection(("127.0.0.1", 8443), timeout=5) as red:
            with especifico.wrap_socket(red, server_hostname="127.0.0.1") as tls:
                resultados.append(f"Negociación real {tls.version()} / {tls.cipher()[0]}")
    for version in (ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1_1):
        obsoleto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        obsoleto.load_verify_locations(str(CA))
        obsoleto.minimum_version = obsoleto.maximum_version = version
        obsoleto.set_ciphers("ALL:@SECLEVEL=0")
        try:
            with socket.create_connection(("127.0.0.1", 8443), timeout=5) as red:
                obsoleto.wrap_socket(red, server_hostname="127.0.0.1")
            raise AssertionError("Nginx aceptó TLS obsoleto")
        except ssl.SSLError as fallo:
            assert "PROTOCOL_VERSION" in fallo.reason, fallo.reason
            resultados.append(f"{version.name} rechazado por alerta de protocolo del servidor")
    for contexto_malo, nombre, descripcion in [
        (ssl.create_default_context(), "127.0.0.1", "CA no confiada en cliente aislado"),
        (contexto, "nombre-equivocado.invalid", "SAN incorrecto")]:
        # El contexto sin CA usa solo el almacén OpenSSL, no el almacén de Windows.
        if descripcion.startswith("CA"):
            contexto_malo = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        try:
            with socket.create_connection(("127.0.0.1", 8443), timeout=5) as red:
                contexto_malo.wrap_socket(red, server_hostname=nombre)
            raise AssertionError("Se aceptó un certificado no válido")
        except ssl.SSLCertVerificationError:
            resultados.append(descripcion + ": conexión rechazada")
    plano = urllib.request.build_opener(SinRedireccion())
    for ruta in ("/acceso", "/docente", "/evaluaciones/evaluacion-001/documento"):
        for metodo in ("GET", "POST"):
            peticion = urllib.request.Request("http://127.0.0.1:8080" + ruta, method=metodo,
                                             data=b"dato-ficticio" if metodo == "POST" else None)
            try:
                plano.open(peticion, timeout=5)
                raise AssertionError("HTTP atendió una operación sensible")
            except urllib.error.HTTPError as respuesta:
                assert respuesta.code == 308
                assert respuesta.headers["Location"] == "https://127.0.0.1:8443" + ruta
                resultados.append(f"HTTP {metodo} {ruta}: 308 a HTTPS, sin contenido privado")
    for ruta, codigo in [("/health",200), ("/acceso",200), ("/docente",401),
                          ("/data/portal.sqlite3",404), ("/secrets/sobre-rsa.pem",404),
                          ("/sobres",404), ("/certs/ca/ca.key",404), ("/tls/server.key",404)]:
        try:
            respuesta = urllib.request.urlopen("https://127.0.0.1:8443" + ruta, context=contexto, timeout=5)
        except urllib.error.HTTPError as error:
            respuesta = error
        assert respuesta.code == codigo
        assert respuesta.headers["X-Content-Type-Options"] == "nosniff"
        assert respuesta.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert "geolocation=()" in respuesta.headers["Permissions-Policy"]
        resultados.append(f"HTTPS {ruta}: {codigo}, cabeceras presentes")
    destino = RAIZ / ".qa/red"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "tls-resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(resultados))
    print(f"{len(resultados)} comprobaciones de red/TLS aprobadas")


if __name__ == "__main__":
    verificar()
