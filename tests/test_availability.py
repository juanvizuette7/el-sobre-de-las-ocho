"""Horario, asignación, migración y aislamiento respecto a identidad de 2A."""

import json
import sqlite3
import time
from datetime import date, datetime, timezone

import pyotp
import pytest
from fastapi.testclient import TestClient

from test_auth import entorno, login, mfa, csrf
from app.clock import BOGOTA, cambiar_reloj, interpretar_instante, leer_reloj
from app.config import Configuracion
from app.db import conexion, inicializar_base
from app.demo import ID_EVALUACION, cambiar_asignacion, preparar_ensayo, principal, estado_reloj, consultar_auditoria
from app.main import crear_aplicacion
from app.security import derivar_clave
from app.sessions import NOMBRE_COOKIE

FECHA = date(2026, 11, 9)
RUTA = f"/evaluaciones/{ID_EVALUACION}/disponibilidad"


@pytest.fixture
def ensayo(entorno):
    preparar_ensayo(entorno[1], FECHA)
    return entorno


def fijar(config, hora):
    with conexion(config, True) as db:
        cambiar_reloj(db, interpretar_instante(hora if "T" in hora else f"2026-11-09T{hora}"))


@pytest.mark.parametrize("hora,esperado", [("07:59:59",403), ("08:00:00",200), ("08:01:00",200)])
def test_limite_inclusive(ensayo, hora, esperado):
    cliente, config, _, _ = ensayo
    login(ensayo)
    fijar(config, hora)
    respuesta = cliente.get(RUTA)
    assert respuesta.status_code == esperado
    assert respuesta.json()["autorizado"] == (esperado == 200)
    assert respuesta.json()["descarga_habilitada"] is False
    assert "content-disposition" not in respuesta.headers
    assert "no-store" in respuesta.headers["cache-control"]


def test_consulta_informa_hora_real_independiente_del_reloj_simulado(ensayo):
    login(ensayo)
    fijar(ensayo[1], "2035-01-01T07:59:59")
    antes = datetime.now(BOGOTA)
    respuesta = ensayo[0].get(RUTA).json()
    despues = datetime.now(BOGOTA)
    consulta = respuesta["presentacion"]["consulta"]
    assert antes <= datetime.fromisoformat(consulta["iso"]) <= despues
    assert respuesta["hora_referencia"].startswith("2035-01-01T07:59:59")
    assert consulta["fecha"] and consulta["hora"]


@pytest.mark.parametrize("instante,codigo", [("2026-11-08T08:01:00",403), ("2026-11-09T12:59:59+00:00",403), ("2026-11-09T13:00:00+00:00",200), ("2026-11-10T07:00:00",200)])
def test_fecha_completa_y_equivalencia_utc(ensayo, instante, codigo):
    login(ensayo)
    fijar(ensayo[1], instante)
    assert ensayo[0].get(RUTA).status_code == codigo


def test_otro_estudiante_no_asignado(ensayo):
    cliente, config, _, _ = ensayo
    clave = "solo-fixture-" + __import__('secrets').token_hex(16)
    with conexion(config, True) as db:
        db.execute("INSERT INTO cuentas(nombre,rol,clave_hash) VALUES(?,?,?)", ("tercero", "ESTUDIANTE", derivar_clave(clave)))
    fijar(config, "08:01:00")
    login(ensayo, "tercero", clave)
    respuesta = cliente.get(RUTA)
    assert respuesta.status_code == 403
    assert respuesta.json()["motivo"] == "evaluacion_no_asignada"
    assert respuesta.json()["evaluacion"] is None
    assert "Evaluación de laboratorio" not in cliente.get("/estudiante").text


def test_retirar_y_reasignar_sin_cambiar_sesion(ensayo):
    cliente, config, _, _ = ensayo
    login(ensayo)
    fijar(config, "08:01:00")
    token = cliente.cookies.get(NOMBRE_COOKIE)
    assert cliente.get(RUTA).status_code == 200
    cambiar_asignacion(config, "estudiante", False)
    assert cliente.get(RUTA).status_code == 403
    cambiar_asignacion(config, "estudiante", True)
    assert cliente.get(RUTA).status_code == 200
    assert cliente.cookies.get(NOMBRE_COOKIE) == token


def test_sin_sesion_y_docente_no_autorizan_como_estudiante(ensayo):
    cliente, config, _, _ = ensayo
    fijar(config, "08:01:00")
    assert cliente.get(RUTA).status_code == 401
    login(ensayo, "docente")
    assert cliente.get(RUTA).status_code == 401
    mfa(ensayo)
    assert cliente.get("/docente").status_code == 200
    assert cliente.get(RUTA).status_code == 403
    assert "Evaluación de laboratorio" in cliente.get("/docente").text


@pytest.mark.parametrize("ruta", ["/reloj", "/admin/reloj", "/evaluaciones/reloj", RUTA])
def test_estudiante_no_modifica_reloj(ensayo, ruta):
    cliente, config, _, _ = ensayo
    login(ensayo)
    antes = estado_reloj(config)
    assert cliente.post(ruta, json={"instante": "2026-11-09T08:01:00", "rol": "DOCENTE"}).status_code in (404,405)
    assert estado_reloj(config)["tiempo_didactico"] == antes["tiempo_didactico"]
    assert cliente.get(RUTA).status_code == 403


def test_parametros_del_navegador_no_sustituyen_atributos(ensayo):
    cliente, config, _, _ = ensayo
    login(ensayo)
    respuesta = cliente.get(RUTA + "?hora=08:01:00&apertura=2000-01-01&cuenta_id=1&autorizado=true")
    assert respuesta.status_code == 403
    assert respuesta.json()["motivo"] == "fuera_de_horario"
    assert cliente.get("/evaluaciones/ajena/disponibilidad").status_code == 403


def test_reloj_no_afecta_totp_ni_caducidad(ensayo):
    cliente, config, _, secreto = ensayo
    login(ensayo, "docente")
    with conexion(config) as db:
        sesion_antes = dict(db.execute("SELECT * FROM sesiones WHERE nivel='mfa'").fetchone())
    codigo = pyotp.TOTP(secreto).now()
    fijar(config, "2035-01-01T08:01:00")
    with conexion(config) as db:
        sesion_despues = dict(db.execute("SELECT * FROM sesiones WHERE nivel='mfa'").fetchone())
    assert sesion_despues == sesion_antes
    assert mfa(ensayo, codigo).status_code == 303
    assert cliente.get("/docente").status_code == 200
    with conexion(config, True) as db:
        fila = db.execute("SELECT creada,vence FROM sesiones WHERE nivel='completa'").fetchone()
        assert fila[1] - fila[0] == config.duracion_sesion
        db.execute("UPDATE sesiones SET vence=?", (int(time.time()) - 1,))
    fijar(config, "2000-01-01T07:59:59")
    assert cliente.get("/docente").status_code == 401


def test_sesion_estudiante_expira_con_reloj_fijo(ensayo):
    cliente, config, _, _ = ensayo
    login(ensayo)
    fijar(config, "08:01:00")
    with conexion(config, True) as db:
        db.execute("UPDATE sesiones SET vence=?", (int(time.time()) - 1,))
    assert cliente.get(RUTA).status_code == 401


def test_reinicio_no_abre_y_preparar_restauracion_repetible(ensayo):
    cliente, config, _, _ = ensayo
    login(ensayo)
    token = cliente.cookies.get(NOMBRE_COOKIE)
    with TestClient(crear_aplicacion(config), base_url=config.origen) as reiniciado:
        reiniciado.cookies.set(NOMBRE_COOKIE, token)
        assert reiniciado.get(RUTA).status_code == 403
        assert estado_reloj(config)["tiempo_didactico"].endswith("07:59:59-05:00")
        fijar(config, "08:00:00")
        assert reiniciado.get(RUTA).status_code == 200
        preparar_ensayo(config, FECHA)
        assert reiniciado.get(RUTA).status_code == 403


def test_modo_normal_lee_tiempo_real_y_no_el_fijo(ensayo, monkeypatch):
    config = ensayo[1]
    esperado = interpretar_instante("2026-11-11T10:11:12")
    monkeypatch.setattr("app.clock.ahora_real", lambda: esperado)
    with conexion(config, True) as db:
        assert cambiar_reloj(db, None) == esperado
    assert estado_reloj(config)["modo"] == "normal"
    with conexion(config) as db:
        assert leer_reloj(db) == esperado


def test_auditoria_separa_relojes_y_recurso(ensayo):
    cliente, config, claves, secreto = ensayo
    login(ensayo)
    for hora in ["07:59:59", "08:00:00"]:
        fijar(config, hora)
        cliente.get(RUTA)
    with conexion(config) as db:
        filas = [dict(fila) for fila in db.execute("SELECT * FROM eventos WHERE accion='consultar_disponibilidad' ORDER BY id")]
        cuenta_id = db.execute("SELECT id FROM cuentas WHERE nombre='estudiante'").fetchone()[0]
    assert [f["motivo"] for f in filas] == ["fuera_de_horario", "apertura_cumplida"]
    assert all(f["cuenta_id"] == cuenta_id and f["evaluacion_id"] == ID_EVALUACION for f in filas)
    assert all(abs(f["instante"] - time.time()) < 20 for f in filas)
    assert filas[0]["instante_didactico"].endswith("07:59:59-05:00")
    assert filas[1]["instante_didactico"].endswith("08:00:00-05:00")
    texto = json.dumps(filas)
    assert all(s not in texto for s in [*claves.values(), secreto, cliente.cookies.get(NOMBRE_COOKIE)])
    exportado = consultar_auditoria(config, 1)
    assert len(exportado) == 1 and exportado[0]["motivo"] == "apertura_cumplida"
    assert exportado[0]["usuario_id"] == cuenta_id
    assert "tiempo_real" in exportado[0] and "tiempo_didactico" in exportado[0]


@pytest.mark.parametrize("elemento", ["reloj", "apertura"])
def test_configuracion_corrupta_bloquea(ensayo, elemento):
    cliente, config, _, _ = ensayo
    login(ensayo)
    with conexion(config, True) as db:
        if elemento == "reloj":
            db.execute("UPDATE reloj_evaluaciones SET instante_fijo='invalido'")
        else:
            db.execute("UPDATE evaluaciones SET apertura='invalida'")
    assert cliente.get(RUTA).status_code == 503
    cliente.cookies.clear()
    assert cliente.get(RUTA).status_code == 401


def test_migracion_aditiva_conserva_datos_2a(tmp_path):
    config = Configuracion(tmp_path)
    db = sqlite3.connect(config.base_datos)
    db.execute("CREATE TABLE eventos(id INTEGER PRIMARY KEY,instante INTEGER,cuenta_id INTEGER,accion TEXT,resultado TEXT,motivo TEXT)")
    db.execute("INSERT INTO eventos VALUES(1,123,NULL,'salida','permitido','sesion_revocada')")
    db.commit()
    db.close()
    inicializar_base(config)
    inicializar_base(config)
    with conexion(config) as db:
        fila = db.execute("SELECT * FROM eventos").fetchone()
        assert fila["instante"] == 123 and fila["motivo"] == "sesion_revocada"
        assert fila["evaluacion_id"] is None and fila["instante_didactico"] is None


def test_cli_fijar_estado_normal_y_retirar(ensayo, monkeypatch, capsys):
    config = ensayo[1]
    monkeypatch.setattr("app.demo.configuracion_entorno", lambda: config)
    for argumentos in [["reloj", "fijar", "2026-11-09T08:00:00"], ["reloj", "estado"], ["asignacion", "retirar"], ["reloj", "normal"], ["preparar", "--fecha", "2026-11-09"], ["auditoria", "--limite", "2"]]:
        monkeypatch.setattr("sys.argv", ["demo", *argumentos])
        principal()
    assert estado_reloj(config)["tiempo_didactico"].endswith("07:59:59-05:00")
    assert '"modo": "normal"' in capsys.readouterr().out
    monkeypatch.setattr("sys.argv", ["demo", "reloj", "fijar", "invalido"])
    with pytest.raises(SystemExit):
        principal()


def test_panel_asignado_muestra_estado_real_y_no_documento(ensayo):
    cliente, config, _, _ = ensayo
    login(ensayo)
    cerrado = cliente.get("/estudiante")
    assert "Evaluación de laboratorio" in cerrado.text and "Examen bloqueado" in cerrado.text
    assert "Falta 1 segundo para la apertura" in cerrado.text
    assert "Aún no hay un documento publicado." in cerrado.text
    assert "Documento pendiente de publicación" not in cerrado.text
    assert "America/Bogota" in cerrado.text
    fijar(config, "08:00:00")
    abierto = cliente.get("/estudiante")
    assert "Horario cumplido" in abierto.text and "Acceso autorizado" in abierto.text
    assert cliente.get("/descargar").status_code == 404


def test_reinicio_no_recrea_reloj_perdido_en_modo_normal(ensayo):
    cliente, config, _, _ = ensayo
    login(ensayo)
    token = cliente.cookies.get(NOMBRE_COOKIE)
    with conexion(config, True) as db:
        db.execute("DELETE FROM reloj_evaluaciones")
    with TestClient(crear_aplicacion(config), base_url=config.origen) as reiniciado:
        reiniciado.cookies.set(NOMBRE_COOKIE, token)
        assert reiniciado.get(RUTA).status_code == 503
        preparar_ensayo(config, FECHA)
        assert reiniciado.get(RUTA).status_code == 403
