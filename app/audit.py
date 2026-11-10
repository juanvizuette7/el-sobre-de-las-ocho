"""Auditoría de identidad con campos estructurados y sin cuerpos de solicitud."""

import time


def registrar(db, accion: str, resultado: str, motivo: str, cuenta_id: int | None = None,
              evaluacion_id: str | None = None, instante_didactico: str | None = None):
    """Recibe únicamente motivos internos; nunca entradas, cookies, claves u OTP."""
    db.execute(
        """INSERT INTO eventos(instante, cuenta_id, accion, resultado, motivo,
           evaluacion_id, instante_didactico) VALUES(?,?,?,?,?,?,?)""",
        (int(time.time()), cuenta_id, accion, resultado, motivo, evaluacion_id, instante_didactico),
    )
