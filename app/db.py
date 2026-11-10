"""Persistencia SQLite privada, consultas parametrizadas y transacciones cortas."""

import os
import sqlite3
from contextlib import contextmanager

from app.config import Configuracion

ESQUEMA = """
CREATE TABLE IF NOT EXISTS cuentas (
    id INTEGER PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('DOCENTE', 'ESTUDIANTE')),
    clave_hash TEXT NOT NULL,
    activa INTEGER NOT NULL DEFAULT 1,
    ultimo_paso_totp INTEGER NOT NULL DEFAULT -1
);
CREATE TABLE IF NOT EXISTS sesiones (
    token_hash TEXT PRIMARY KEY,
    cuenta_id INTEGER REFERENCES cuentas(id),
    nivel TEXT NOT NULL CHECK (nivel IN ('anonima', 'mfa', 'completa')),
    csrf TEXT NOT NULL,
    creada INTEGER NOT NULL,
    vence INTEGER NOT NULL,
    mfa_verificada INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS sesiones_vencimiento ON sesiones(vence);
CREATE TABLE IF NOT EXISTS intentos (
    clave TEXT PRIMARY KEY,
    inicio INTEGER NOT NULL,
    cantidad INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY,
    instante INTEGER NOT NULL,
    cuenta_id INTEGER REFERENCES cuentas(id),
    accion TEXT NOT NULL,
    resultado TEXT NOT NULL,
    motivo TEXT NOT NULL
);
"""


def inicializar_base(config: Configuracion) -> None:
    """Prepara almacenamiento, sin crear cuentas o secretos automáticamente."""
    config.datos.mkdir(parents=True, exist_ok=True, mode=0o700)
    with conexion(config) as db:
        db.executescript(ESQUEMA)
    os.chmod(config.base_datos, 0o600)


@contextmanager
def conexion(config: Configuracion, escritura: bool = False):
    """Cierra cada conexión y revierte escrituras fallidas; MFA usa bloqueo atómico."""
    db = sqlite3.connect(config.base_datos, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        if escritura:
            db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
