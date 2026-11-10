"""Carga y entrega reales, fallos cerrados y restauración sin modificar identidad."""

import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from test_auth import entorno, login, mfa, csrf
from test_availability import fijar
from app.config import Configuracion
from app.crypto import huella
from app.db import conexion, inicializar_base
from app.demo import preparar_ensayo
from app.main import crear_aplicacion
from app.sessions import NOMBRE_COOKIE
from app.storage import (FalloSobre, MAX_ARCHIVO, TEXTO_PRUEBA, estado_sobre, operacion_local,
                         recuperar, ruta_sobre, validar_texto)

RUTA = "/evaluaciones/evaluacion-001/documento"
DISP = "/evaluaciones/evaluacion-001/disponibilidad"


@pytest.fixture
def ensayo(entorno):
    preparar_ensayo(entorno[1], date(2026, 11, 9))
    return entorno


def cargar(ensayo, nombre="parcial.txt", contenido=TEXTO_PRUEBA, token=None, origen=None):
    cliente, config, _, _ = ensayo
    token = csrf(cliente.get("/docente")) if token is None else token
    if "\\" in nombre:
        # El cliente HTTP normal elimina rutas Windows: enviar aquí el encabezado hostil real.
        cuerpo = (f'--prueba\r\nContent-Disposition: form-data; name="csrf"\r\n\r\n{token}\r\n'
                  f'--prueba\r\nContent-Disposition: form-data; name="documento"; filename="{nombre}"\r\n'
                  'Content-Type: text/plain\r\n\r\n').encode() + contenido + b'\r\n--prueba--\r\n'
        return cliente.post(RUTA, content=cuerpo, headers={"Content-Type": "multipart/form-data; boundary=prueba", "Origin": origen or config.origen})
    return cliente.post(RUTA, data={"csrf": token}, files={"documento": (nombre, contenido, "text/plain")},
                        headers={"Origin": origen or config.origen})


def publicar(ensayo):
    login(ensayo, "docente")
    mfa(ensayo)
    assert cargar(ensayo).status_code == 303


def salir(ensayo, rol):
    cliente = ensayo[0]
    cliente.post("/salir", data={"csrf": csrf(cliente.get("/" + rol))})


def test_carga_real_y_almacen_privado(ensayo):
    publicar(ensayo)
    cliente, config, _, _ = ensayo
    assert "parcial.txt" in cliente.get("/docente").text
    with conexion(config) as db:
        documento = db.execute("SELECT * FROM documentos").fetchone()
        assert documento["sha256"] == huella(TEXTO_PRUEBA)
        assert recuperar(config, db, documento) == TEXTO_PRUEBA
        datos = ruta_sobre(config, json.loads(documento["activo"])["id"]).read_bytes()
        assert TEXTO_PRUEBA not in datos
    assert (config.datos / "secrets/sobre-rsa.pem").stat().st_mode & 0o777 == 0o600
    for ruta in ["/data/sobres", "/sobres", "/secrets/sobre-rsa.pem", "/static/parcial.txt", "/data/portal.sqlite3"]:
        assert cliente.get(ruta).status_code == 404


@pytest.mark.parametrize("rol,codigo", [(None, 401), ("estudiante", 403), ("docente", 401)])
def test_carga_requiere_docente_y_mfa(ensayo, rol, codigo):
    if rol:
        login(ensayo, rol)
    assert cargar(ensayo, token="invalido").status_code == codigo
    assert not list(ensayo[1].datos.glob("sobres/*.gcm"))


@pytest.mark.parametrize("token,origen", [("inventado", None), (None, "http://otro.local")])
def test_carga_rechaza_csrf_y_origen(ensayo, token, origen):
    login(ensayo, "docente")
    mfa(ensayo)
    assert cargar(ensayo, token=token, origen=origen).status_code == 403


@pytest.mark.parametrize("nombre,contenido", [
    ("parcial.pdf", b"%PDF-1.7"), ("parcial.txt", b"%PDF\x00\xff"),
    ("parcial.txt", b"MZ\x00\x01"), ("parcial.txt", b""),
    ("parcial.txt", b"  \n"), ("../parcial.txt", b"Texto"),
    ("C:\\parcial.txt", b"Texto"), ("parcial.txt", b"a" * (MAX_ARCHIVO + 1)),
])
def test_valida_carga_tamano_formato_nombre(ensayo, nombre, contenido):
    login(ensayo, "docente")
    mfa(ensayo)
    respuesta = cargar(ensayo, nombre, contenido)
    if "\\" in nombre:
        # python-multipart normaliza los nombres Windows a su basename antes de entregarlos.
        assert respuesta.status_code == 303
        with conexion(ensayo[1]) as db:
            assert db.execute("SELECT nombre FROM documentos").fetchone()[0] == "parcial.txt"
        with pytest.raises(ValueError):
            validar_texto(nombre, contenido)
        return
    assert respuesta.status_code == 400
    with conexion(ensayo[1]) as db:
        assert db.execute("SELECT count(*) FROM documentos").fetchone()[0] == 0


def test_limite_cuerpo_y_texto_unicode(ensayo):
    login(ensayo, "docente")
    mfa(ensayo)
    assert cargar(ensayo, contenido=b"a" * (MAX_ARCHIVO + 20000)).status_code == 413
    assert validar_texto("Evaluación segura.txt", "Pregunta: ¿Qué significa integridad?\n".encode()) == "Evaluacion-segura.txt"


@pytest.mark.parametrize("tipo", [None, "text/plain"])
def test_carga_sin_formulario_multipart_devuelve_error_claro(ensayo, tipo):
    login(ensayo, "docente")
    mfa(ensayo)
    headers = {"Content-Type": tipo} if tipo else {}
    assert ensayo[0].post(RUTA, content=b"cuerpo no multipart", headers=headers).status_code == 400


def test_alteracion_hash_conserva_texto_utf8_con_bom(ensayo):
    login(ensayo, "docente")
    mfa(ensayo)
    assert cargar(ensayo, contenido="\ufeffÉtica e integridad\n".encode()).status_code == 303
    operacion_local(ensayo[1], "evaluacion-001", "alterar-hash")
    with conexion(ensayo[1]) as db:
        fila = db.execute("SELECT * FROM documentos").fetchone()
        alterado = recuperar(ensayo[1], db, fila, comprobar_hash=False)
        assert alterado.decode("utf-8").startswith("\ufeffX")
        assert huella(alterado) != fila["sha256"]


@pytest.mark.parametrize("hora,codigo", [("07:59:59",403), ("08:00:00",200), ("08:01:00",200)])
def test_descarga_limite_y_bytes_exactos(ensayo, hora, codigo):
    publicar(ensayo)
    salir(ensayo, "docente")
    login(ensayo)
    fijar(ensayo[1], hora)
    respuesta = ensayo[0].get(RUTA)
    assert respuesta.status_code == codigo
    assert (respuesta.content == TEXTO_PRUEBA) == (codigo == 200)
    if codigo == 200:
        assert "attachment" in respuesta.headers["content-disposition"]
        assert "no-store" in respuesta.headers["cache-control"]
        assert respuesta.headers["x-content-type-options"] == "nosniff"
        assert ensayo[0].get(DISP).json()["descarga_habilitada"] is True
    else:
        assert "content-disposition" not in respuesta.headers


@pytest.mark.parametrize("caso,codigo", [("anonimo",401), ("docente",403), ("sin_asignacion",403), ("vencida",401), ("ajeno",403)])
def test_descarga_no_autorizada(ensayo, caso, codigo):
    publicar(ensayo)
    salir(ensayo, "docente")
    fijar(ensayo[1], "08:01:00")
    if caso != "anonimo":
        login(ensayo, "docente" if caso == "docente" else "estudiante")
        if caso == "docente":
            mfa(ensayo, __import__('pyotp').TOTP(ensayo[3]).at(__import__('time').time()+30))
    if caso in ("sin_asignacion", "vencida"):
        with conexion(ensayo[1], True) as db:
            if caso == "sin_asignacion":
                db.execute("DELETE FROM asignaciones")
            else:
                db.execute("UPDATE sesiones SET vence=0")
    respuesta = ensayo[0].get(RUTA if caso != "ajeno" else "/evaluaciones/otro/documento")
    assert respuesta.status_code == codigo
    assert TEXTO_PRUEBA not in respuesta.content


@pytest.mark.parametrize("accion,motivo", [("alterar-gcm","autenticacion_gcm_fallida"), ("alterar-hash","discrepancia_sha256")])
def test_dos_alteraciones_reales_y_restauracion(ensayo, accion, motivo):
    publicar(ensayo)
    salir(ensayo, "docente")
    login(ensayo)
    config = ensayo[1]
    fijar(config, "08:00:00")
    with conexion(config) as db:
        esperado = db.execute("SELECT sha256 FROM documentos").fetchone()[0]
        identidad = [tuple(fila) for fila in db.execute("SELECT * FROM cuentas")]
    secreto = (config.datos / "secrets/docente.totp").read_bytes()
    token = ensayo[0].cookies.get(NOMBRE_COOKIE)
    operacion_local(config, "evaluacion-001", accion)
    estado = estado_sobre(config, "evaluacion-001")
    if accion == "alterar-hash":
        assert estado["autenticacion_gcm"] == "correcta" and estado["integridad"] is False
    else:
        assert estado["autenticacion_gcm"] == "no_superada"
    respuesta = ensayo[0].get(RUTA)
    assert respuesta.status_code == 409 and TEXTO_PRUEBA not in respuesta.content
    assert "content-disposition" not in respuesta.headers
    vista = ensayo[0].get(DISP).json()
    assert vista["codigo"] == 409 and vista["descarga_habilitada"] is False
    assert motivo == vista["motivo"]
    with conexion(config) as db:
        assert db.execute("SELECT sha256 FROM documentos").fetchone()[0] == esperado
        assert db.execute("SELECT 1 FROM eventos WHERE accion='verificar_integridad' AND motivo=?", (motivo,)).fetchone()
    operacion_local(config, "evaluacion-001", "restaurar")
    assert ensayo[0].get(RUTA).content == TEXTO_PRUEBA
    assert ensayo[0].cookies.get(NOMBRE_COOKIE) == token
    assert (config.datos / "secrets/docente.totp").read_bytes() == secreto
    with conexion(config) as db:
        assert [tuple(fila) for fila in db.execute("SELECT * FROM cuentas")] == identidad
        assert db.execute("SELECT instante_fijo FROM reloj_evaluaciones").fetchone()[0].endswith("08:00:00-05:00")
        assert db.execute("SELECT 1 FROM eventos WHERE motivo='restaurar'").fetchone()


def test_reemplazo_y_reinicio_conservan_clave_y_version(ensayo):
    publicar(ensayo)
    config = ensayo[1]
    clave = (config.datos / "secrets/sobre-rsa.pem").read_bytes()
    assert cargar(ensayo, contenido=b"Segundo original\n").status_code == 303
    assert len(list((config.datos / "sobres").glob("*.gcm"))) == 1
    salir(ensayo, "docente")
    login(ensayo)
    fijar(config, "08:00:00")
    with TestClient(crear_aplicacion(config), base_url=config.origen) as nuevo:
        nuevo.cookies.set(NOMBRE_COOKIE, ensayo[0].cookies.get(NOMBRE_COOKIE))
        assert nuevo.get(RUTA).content == b"Segundo original\n"
    assert (config.datos / "secrets/sobre-rsa.pem").read_bytes() == clave


@pytest.mark.parametrize("falta", ["archivo", "clave", "hash", "metadatos"])
def test_faltantes_y_metadatos_manipulados_no_entregan(ensayo, falta):
    publicar(ensayo)
    salir(ensayo, "docente")
    login(ensayo)
    config = ensayo[1]
    fijar(config, "08:00:00")
    with conexion(config, True) as db:
        fila = db.execute("SELECT * FROM documentos").fetchone()
        if falta == "archivo":
            ruta_sobre(config, json.loads(fila["activo"])["id"]).unlink()
        elif falta == "clave":
            (config.datos / "secrets/sobre-rsa.pem").unlink()
        elif falta == "hash":
            db.execute("UPDATE documentos SET sha256='' ")
        else:
            meta = json.loads(fila["activo"])
            meta["id"] = "../../secrets/docente.totp"
            db.execute("UPDATE documentos SET activo=?", (json.dumps(meta),))
    respuesta = ensayo[0].get(RUTA)
    assert respuesta.status_code == 409 and TEXTO_PRUEBA not in respuesta.content
    if falta == "clave":
        operacion = lambda: operacion_local(config, "evaluacion-001", "preparar")
        with pytest.raises(FalloSobre):
            operacion()
        assert not (config.datos / "secrets/sobre-rsa.pem").exists()


def test_auditoria_y_denegacion_antes_de_leer_cifrado(ensayo, monkeypatch):
    publicar(ensayo)
    salir(ensayo, "docente")
    login(ensayo)
    config = ensayo[1]
    def lectura_prohibida(*args):
        raise AssertionError("No debe descifrar antes de apertura")
    monkeypatch.setattr("app.documents.recuperar", lectura_prohibida)
    assert ensayo[0].get(RUTA).status_code == 403
    with conexion(config) as db:
        evento = db.execute("SELECT * FROM eventos WHERE accion='descargar_documento' ORDER BY id DESC").fetchone()
        assert evento["motivo"] == "fuera_de_horario" and evento["cuenta_id"]
        assert evento["instante_didactico"].endswith("07:59:59-05:00")
        assert evento["instante"] > 0
        assert all(valor not in json.dumps([dict(f) for f in db.execute("SELECT * FROM eventos")]) for valor in ensayo[2].values())


def test_documento_ausente_y_laboratorio_no_web(ensayo):
    login(ensayo)
    fijar(ensayo[1], "08:00:00")
    assert ensayo[0].get(RUTA).status_code == 404
    assert ensayo[0].get(DISP).json()["descarga_habilitada"] is False
    for ruta in ["/sobre/alterar-hash", "/laboratorio/sobre", "/evaluaciones/evaluacion-001/restaurar"]:
        assert ensayo[0].post(ruta).status_code == 404


def test_fallo_auditoria_impide_entrega(ensayo, monkeypatch):
    publicar(ensayo)
    salir(ensayo, "docente")
    login(ensayo)
    fijar(ensayo[1], "08:00:00")
    import sqlite3
    def fallo(*args, **kwargs):
        raise sqlite3.OperationalError("fallo de prueba")
    monkeypatch.setattr("app.documents.registrar", fallo)
    respuesta = ensayo[0].get(RUTA)
    assert respuesta.status_code == 503 and TEXTO_PRUEBA not in respuesta.content


def test_fallo_escritura_no_sustituye_version_publicada(ensayo, monkeypatch):
    publicar(ensayo)
    with conexion(ensayo[1]) as db:
        version = db.execute("SELECT version FROM documentos").fetchone()[0]
    def fallo(*args, **kwargs):
        raise OSError("interrupción de escritura de prueba")
    monkeypatch.setattr("app.storage.escribir_atomico", fallo)
    assert cargar(ensayo, contenido=b"Reemplazo interrumpido").status_code == 503
    with conexion(ensayo[1]) as db:
        fila = db.execute("SELECT * FROM documentos").fetchone()
        assert fila["version"] == version
        assert recuperar(ensayo[1], db, fila) == TEXTO_PRUEBA


def test_cuota_no_sustituye_documento(ensayo, monkeypatch):
    publicar(ensayo)
    monkeypatch.setattr("app.storage.MAX_ALMACEN", 1)
    assert cargar(ensayo, contenido=b"Otra version").status_code == 503
    with conexion(ensayo[1]) as db:
        assert recuperar(ensayo[1], db, db.execute("SELECT * FROM documentos").fetchone()) == TEXTO_PRUEBA


@pytest.mark.parametrize("identificador", ["..", "a%5Cb", "a%22b"])
def test_identificador_hostil_no_accede_al_almacen(ensayo, identificador):
    login(ensayo)
    respuesta = ensayo[0].get(f"/evaluaciones/{identificador}/documento")
    assert respuesta.status_code in (404, 422)
    assert TEXTO_PRUEBA not in respuesta.content
