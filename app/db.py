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
    motivo TEXT NOT NULL,
    evaluacion_id TEXT,
    instante_didactico TEXT
);
CREATE TABLE IF NOT EXISTS evaluaciones (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    apertura TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asignaciones (
    evaluacion_id TEXT NOT NULL REFERENCES evaluaciones(id),
    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
    PRIMARY KEY (evaluacion_id, cuenta_id)
);
CREATE TABLE IF NOT EXISTS reloj_evaluaciones (
    id INTEGER PRIMARY KEY CHECK (id=1),
    instante_fijo TEXT
);
-- Solo una instalación sin evaluaciones puede adoptar tiempo normal por defecto.
-- Si se pierde el reloj de una instalación preparada, no se abre por recuperación implícita.
INSERT OR IGNORE INTO reloj_evaluaciones(id, instante_fijo)
SELECT 1, NULL WHERE NOT EXISTS (SELECT 1 FROM evaluaciones);
"""


def inicializar_base(config: Configuracion) -> None:
    """Prepara almacenamiento, sin crear cuentas o secretos automáticamente."""
    config.datos.mkdir(parents=True, exist_ok=True, mode=0o700)
    with conexion(config) as db:
        db.executescript(ESQUEMA)
    # Migración aditiva: conserva cuentas, sesiones y eventos de instalaciones 2A.
    with conexion(config, escritura=True) as db:
        columnas = {fila[1] for fila in db.execute("PRAGMA table_info(eventos)")}
        if "evaluacion_id" not in columnas:
            db.execute("ALTER TABLE eventos ADD COLUMN evaluacion_id TEXT")
        if "instante_didactico" not in columnas:
            db.execute("ALTER TABLE eventos ADD COLUMN instante_didactico TEXT")
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
