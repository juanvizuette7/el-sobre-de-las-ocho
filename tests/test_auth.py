"""Pruebas de seguridad con cuentas y bases temporales, independientes del portal."""

import json
import re
import secrets
import time
from types import SimpleNamespace

import pyotp
import pytest
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.db import conexion
from app.main import crear_aplicacion
from app.manage import guardar_cuentas
from app.security import derivar_clave, paso_totp
from app.sessions import NOMBRE_COOKIE, huella


def csrf(respuesta):
    return re.search(r'name="csrf" value="([^"]+)"', respuesta.text)[1]


@pytest.fixture
def entorno(tmp_path):
    config = Configuracion(tmp_path)
    claves = {"docente": secrets.token_urlsafe(20), "estudiante": secrets.token_urlsafe(20)}
    secreto = pyotp.random_base32()
    with TestClient(crear_aplicacion(config), base_url=config.origen,
                    headers={"Origin": config.origen}, follow_redirects=False) as cliente:
        guardar_cuentas(config, claves["docente"], claves["estudiante"], secreto, -1)
        yield cliente, config, claves, secreto


def login(entorno, nombre="estudiante", clave=None, **extras):
    cliente, _, claves, _ = entorno
    token = csrf(cliente.get("/acceso"))
    return cliente.post("/acceso", data={"csrf": token, "usuario": nombre,
                                         "clave": clave or claves.get(nombre, "inexistente"), **extras})


def mfa(entorno, codigo=None):
    cliente, _, _, secreto = entorno
    token = csrf(cliente.get("/acceso/totp"))
    return cliente.post("/acceso/totp", data={"csrf": token, "codigo": codigo or pyotp.TOTP(secreto).now()})


def test_login_estudiante_y_rbac(entorno):
    cliente, _, _, _ = entorno
    assert login(entorno).status_code == 303
    assert cliente.get("/estudiante").status_code == 200
    assert cliente.get("/docente").status_code == 403
    assert cliente.get("/admin").status_code == 404


@pytest.mark.parametrize("nombre", ["estudiante", "no_existe"])
def test_error_generico_credenciales(entorno, nombre):
    respuesta = login(entorno, nombre, "incorrecta")
    assert respuesta.status_code == 401
    assert "Usuario o contraseña incorrectos" in respuesta.text
    assert 'value="incorrecta"' not in respuesta.text


def test_docente_requiere_dos_factores(entorno):
    cliente, _, _, _ = entorno
    assert login(entorno, "docente").headers["location"] == "/acceso/totp"
    assert cliente.get("/docente").status_code == 401
    assert cliente.get("/estudiante").status_code == 401
    assert mfa(entorno).headers["location"] == "/docente"
    assert cliente.get("/docente").status_code == 200
    assert cliente.get("/estudiante").status_code == 403


def test_codigo_incorrecto_y_repeticion(entorno):
    cliente, _, _, secreto = entorno
    login(entorno, "docente")
    incorrecto = next(f"{i:06d}" for i in range(10) if paso_totp(secreto, f"{i:06d}") is None)
    assert mfa(entorno, incorrecto).status_code == 401
    codigo = pyotp.TOTP(secreto).now()
    assert mfa(entorno, codigo).status_code == 303
    panel = cliente.get("/docente")
    cliente.post("/salir", data={"csrf": csrf(panel)})
    login(entorno, "docente")
    assert mfa(entorno, codigo).status_code == 401
    assert cliente.get("/docente").status_code == 401


@pytest.mark.parametrize("ruta", ["/docente", "/estudiante", "/acceso/totp"])
def test_sin_sesion(entorno, ruta):
    assert entorno[0].get(ruta).status_code == 401


def test_rotacion_salida_e_invalidacion(entorno):
    cliente, config, _, _ = entorno
    inicial = cliente.get("/acceso")
    anterior = cliente.cookies.get(NOMBRE_COOKIE)
    login(entorno)
    actual = cliente.cookies.get(NOMBRE_COOKIE)
    assert actual != anterior
    with conexion(config) as db:
        assert not db.execute("SELECT 1 FROM sesiones WHERE token_hash=?", (huella(anterior),)).fetchone()
    panel = cliente.get("/estudiante")
    assert cliente.post("/salir", data={"csrf": csrf(panel)}).status_code == 303
    cliente.cookies.set(NOMBRE_COOKIE, actual)
    assert cliente.get("/estudiante").status_code == 401
    cliente.cookies.clear()
    assert cliente.get("/estudiante").status_code == 401
    assert "HttpOnly" in inicial.headers["set-cookie"]
    assert "SameSite=lax" in inicial.headers["set-cookie"]


def test_rotacion_mfa(entorno):
    cliente, config, _, _ = entorno
    login(entorno, "docente")
    pendiente = cliente.cookies.get(NOMBRE_COOKIE)
    mfa(entorno)
    assert cliente.cookies.get(NOMBRE_COOKIE) != pendiente
    with conexion(config) as db:
        assert not db.execute("SELECT 1 FROM sesiones WHERE token_hash=?", (huella(pendiente),)).fetchone()


@pytest.mark.parametrize("nivel", ["anonima", "mfa", "completa"])
def test_sesiones_vencidas(entorno, nivel):
    cliente, config, _, _ = entorno
    if nivel == "anonima":
        cliente.get("/acceso")
    else:
        login(entorno, "docente" if nivel == "mfa" else "estudiante")
    with conexion(config, True) as db:
        db.execute("UPDATE sesiones SET vence=?", (int(time.time()) - 1,))
    assert cliente.get("/docente" if nivel == "mfa" else "/estudiante").status_code == 401
    if nivel == "mfa":
        assert cliente.get("/acceso/totp").status_code == 401


@pytest.mark.parametrize("ataque", ["sin_token", "token_falso", "origen_ajeno", "sin_origen", "unicode"])
def test_csrf_login(entorno, ataque):
    cliente, _, claves, _ = entorno
    token = csrf(cliente.get("/acceso"))
    datos = {"usuario": "estudiante", "clave": claves["estudiante"], "csrf": token}
    if ataque == "sin_token":
        datos.pop("csrf")
    if ataque == "token_falso":
        datos["csrf"] = "alterado"
    if ataque == "unicode":
        datos["csrf"] = "á"
    if ataque == "origen_ajeno":
        cliente.headers["Origin"] = "http://ajeno.invalid"
    if ataque == "sin_origen":
        del cliente.headers["Origin"]
    assert cliente.post("/acceso", data=datos).status_code == 403
    assert cliente.get("/estudiante").status_code == 401


def test_csrf_mfa_y_salida(entorno):
    cliente, _, _, secreto = entorno
    login(entorno, "docente")
    assert cliente.post("/acceso/totp", data={"codigo": pyotp.TOTP(secreto).now()}).status_code == 403
    mfa(entorno)
    assert cliente.post("/salir", data={"csrf": "alterado"}).status_code == 403
    assert cliente.get("/docente").status_code == 200


def test_manipulacion_rol_no_eleva_privilegios(entorno):
    cliente, config, _, _ = entorno
    login(entorno, rol="DOCENTE", mfa="true")
    assert cliente.get("/docente?rol=DOCENTE").status_code == 403
    # Incluso un cambio administrativo de rol requiere una sesión con MFA comprobado.
    with conexion(config, True) as db:
        db.execute("UPDATE cuentas SET rol='DOCENTE' WHERE nombre='estudiante'")
    assert cliente.get("/docente").status_code == 401


def test_cuenta_desactivada_revoca_acceso(entorno):
    cliente, config, _, _ = entorno
    login(entorno)
    with conexion(config, True) as db:
        db.execute("UPDATE cuentas SET activa=0 WHERE nombre='estudiante'")
    assert cliente.get("/estudiante").status_code == 401


def test_limite_persistente_credenciales(entorno):
    cliente, _, _, _ = entorno
    for _ in range(5):
        assert login(entorno, clave="fallo").status_code == 401
    cliente.cookies.clear()
    assert login(entorno, clave="fallo").status_code == 429


def test_rate_limit_auditoria_y_recuperacion(entorno, monkeypatch):
    import app.sessions as sesiones

    cliente, config, _, _ = entorno
    reloj = [int(time.time())]
    monkeypatch.setattr(sesiones, "time", SimpleNamespace(time=lambda: reloj[0]))
    for _ in range(config.limite_intentos):
        assert login(entorno, clave="clave-ficticia-incorrecta").status_code == 401
    assert login(entorno, clave="clave-ficticia-incorrecta").status_code == 429
    with conexion(config) as db:
        assert db.execute(
            "SELECT 1 FROM eventos WHERE accion='autenticacion' AND motivo='limite_intentos'"
        ).fetchone()

    reloj[0] += config.ventana_intentos + 1
    cliente.cookies.clear()
    assert login(entorno, clave="clave-ficticia-incorrecta").status_code == 401
    with conexion(config) as db:
        assert db.execute(
            "SELECT 1 FROM eventos WHERE accion='autenticacion' AND motivo='credenciales_invalidas'"
        ).fetchone()


def test_limite_persistente_mfa(entorno):
    _, _, _, secreto = entorno
    login(entorno, "docente")
    incorrecto = next(f"{i:06d}" for i in range(10) if paso_totp(secreto, f"{i:06d}") is None)
    for _ in range(5):
        assert mfa(entorno, incorrecto).status_code == 401
    assert mfa(entorno).status_code == 429


def test_sin_secretos_en_respuestas_auditoria_o_db(entorno, caplog):
    cliente, config, claves, secreto = entorno
    respuestas = [login(entorno, "docente"), cliente.get("/acceso/totp"), mfa(entorno), cliente.get("/docente")]
    with conexion(config) as db:
        eventos = json.dumps([dict(f) for f in db.execute("SELECT * FROM eventos")])
        hashes = [f[0] for f in db.execute("SELECT clave_hash FROM cuentas")]
        dump = "\n".join(db.iterdump())
    texto = "\n".join(r.text for r in respuestas) + eventos + caplog.text
    for sensible in [*claves.values(), secreto, pyotp.TOTP(secreto).now(), *hashes]:
        assert sensible not in texto
    assert secreto not in dump
    assert all(c not in dump for c in claves.values())
    assert all(h.startswith("$argon2id$") for h in hashes)
    assert "no-store" in respuestas[-1].headers["cache-control"]
    assert cliente.cookies.get(NOMBRE_COOKIE) not in dump
    assert cliente.get("/data/portal.sqlite3").status_code == 404
    assert cliente.get("/secrets/docente.totp").status_code == 404


def test_sal_individual_y_alta_no_sobrescribe(entorno):
    _, config, claves, secreto = entorno
    assert derivar_clave(claves["docente"]) != derivar_clave(claves["docente"])
    with pytest.raises(ValueError):
        guardar_cuentas(config, claves["docente"], claves["estudiante"], pyotp.random_base32(), -1)
    assert (config.datos / "secrets/docente.totp").read_text() == secreto


def test_cookie_secure_al_configurar_https(tmp_path):
    config = Configuracion(tmp_path, origen="https://127.0.0.1:8443")
    with TestClient(crear_aplicacion(config), base_url=config.origen) as cliente:
        assert "; Secure" in cliente.get("/acceso").headers["set-cookie"]


def test_reinicio_preserva_sesion(entorno):
    cliente, config, _, _ = entorno
    login(entorno)
    token = cliente.cookies.get(NOMBRE_COOKIE)
    with TestClient(crear_aplicacion(config), base_url=config.origen) as reiniciado:
        reiniciado.cookies.set(NOMBRE_COOKIE, token)
        assert reiniciado.get("/estudiante").status_code == 200


def test_falta_secreto_bloquea_mfa(entorno):
    cliente, config, _, _ = entorno
    login(entorno, "docente")
    (config.datos / "secrets/docente.totp").unlink()
    assert mfa(entorno).status_code == 503
    assert cliente.get("/docente").status_code == 401


def test_revocacion_local_y_cli_no_interactiva(entorno, monkeypatch, capsys):
    import io
    from app import manage
    cliente, config, _, _ = entorno
    login(entorno)
    class Terminal(io.StringIO):
        def isatty(self):
            return True
    monkeypatch.setattr("sys.stdin", Terminal())
    monkeypatch.setattr("sys.argv", ["manage", "revocar-sesiones"])
    monkeypatch.setattr(manage, "configuracion_entorno", lambda: config)
    monkeypatch.setattr("builtins.input", lambda _: "REVOCAR")
    manage.principal()
    assert cliente.get("/estudiante").status_code == 401
    monkeypatch.setattr("sys.stdin", io.StringIO())
    with pytest.raises(SystemExit):
        manage.principal()
    assert "terminal interactiva" in capsys.readouterr().err


@pytest.mark.parametrize("valido", [True, False])
def test_alta_cli_confirma_autenticador(tmp_path, monkeypatch, capsys, valido):
    from types import SimpleNamespace
    from app import manage
    config = Configuracion(tmp_path)
    secreto = pyotp.random_base32()
    claves = [secrets.token_urlsafe(20), secrets.token_urlsafe(20)]
    codigo = pyotp.TOTP(secreto).now() if valido else next(f"{i:06d}" for i in range(10) if paso_totp(secreto, f"{i:06d}") is None)
    respuestas = iter([claves[0], claves[0], claves[1], claves[1], codigo])
    monkeypatch.setattr("sys.stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("sys.argv", ["manage", "inicializar"])
    monkeypatch.setattr(manage, "configuracion_entorno", lambda: config)
    monkeypatch.setattr(manage.pyotp, "random_base32", lambda: secreto)
    monkeypatch.setattr(manage.getpass, "getpass", lambda _: next(respuestas))
    if valido:
        manage.principal()
    else:
        with pytest.raises(SystemExit):
            manage.principal()
    with conexion(config) as db:
        assert db.execute("SELECT COUNT(*) FROM cuentas").fetchone()[0] == (2 if valido else 0)
    salida = capsys.readouterr()
    assert all(clave not in salida.out + salida.err for clave in claves)
