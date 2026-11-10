"""Auditoría de identidad con campos estructurados y sin cuerpos de solicitud."""

import time


def registrar(db, accion: str, resultado: str, motivo: str, cuenta_id: int | None = None):
    """Recibe únicamente motivos internos; nunca entradas, cookies, claves u OTP."""
    db.execute(
        "INSERT INTO eventos(instante, cuenta_id, accion, resultado, motivo) VALUES(?,?,?,?,?)",
        (int(time.time()), cuenta_id, accion, resultado, motivo),
    )
