"""Reloj persistente de apertura; no sustituye el tiempo de identidad ni del sistema."""

from datetime import datetime
from zoneinfo import ZoneInfo

BOGOTA = ZoneInfo("America/Bogota")


def interpretar_instante(valor: str) -> datetime:
    """Interpreta fecha y hora ISO; valores sin offset se entienden en Bogotá."""
    if "T" not in valor:
        raise ValueError("Use fecha y hora completas: AAAA-MM-DDTHH:MM:SS.")
    instante = datetime.fromisoformat(valor)
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=BOGOTA)
    return instante.astimezone(BOGOTA)


def ahora_real() -> datetime:
    """Lee tiempo real únicamente como referencia del reloj de evaluaciones."""
    return datetime.now(BOGOTA)


def leer_reloj(db) -> datetime:
    """Un modo fijo permanece detenido y persiste tras reiniciar servicios."""
    fila = db.execute("SELECT instante_fijo FROM reloj_evaluaciones WHERE id=1").fetchone()
    if fila is None:
        raise ValueError("Falta el estado del reloj de evaluaciones.")
    return interpretar_instante(fila[0]) if fila[0] is not None else ahora_real()


def cambiar_reloj(db, instante: datetime | None) -> datetime:
    """Solo la utilidad local invoca esta escritura; None restablece tiempo real."""
    valor = instante.astimezone(BOGOTA).isoformat() if instante is not None else None
    db.execute("""INSERT INTO reloj_evaluaciones(id,instante_fijo) VALUES(1,?)
               ON CONFLICT(id) DO UPDATE SET instante_fijo=excluded.instante_fijo""", (valor,))
    return leer_reloj(db)
