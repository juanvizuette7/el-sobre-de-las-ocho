"""Formato visual de horarios y decisiones existentes; no concede permisos."""

from datetime import datetime
from math import ceil

from app.clock import BOGOTA

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre")


def fecha_hora_visual(valor: str | None, apertura: bool = False) -> dict | None:
    """Formatea un instante explícito del servidor sin depender del locale del equipo."""
    if not valor:
        return None
    try:
        instante = datetime.fromisoformat(valor)
        if instante.tzinfo is None:
            return None
        instante = instante.astimezone(BOGOTA)
    except (ValueError, TypeError):
        return None
    periodo = "a. m." if instante.hour < 12 else "p. m."
    hora = f"{instante.hour % 12 or 12}:{instante.minute:02d}"
    if not apertura or instante.second:
        hora += f":{instante.second:02d}"
    return {"iso": instante.isoformat(), "hora": f"{hora} {periodo}",
            "fecha": f"{DIAS[instante.weekday()]}, {instante.day} de {MESES[instante.month - 1]} de {instante.year}"}


def presentar_programacion(hora_referencia: str | None, apertura: str | None) -> dict:
    """Separa referencia del laboratorio y apertura programada en el modelo de vista."""
    return {"reloj": fecha_hora_visual(hora_referencia),
            "apertura": fecha_hora_visual(apertura, apertura=True)}


def presentar_decision(decision: dict) -> dict:
    """Añade textos de interfaz al resultado original sin cambiar su código o atributos."""
    evaluacion = decision.get("evaluacion") or {}
    vista = presentar_programacion(decision.get("hora_referencia"), evaluacion.get("apertura"))
    vista.update(estado="restricted", mensaje=decision["mensaje"])
    if decision["codigo"] == 200 and decision["autorizado"] and decision["motivo"] == "apertura_cumplida":
        vista.update(estado="ok", mensaje="Horario cumplido. Acceso autorizado")
    elif decision["motivo"] == "fuera_de_horario" and not decision["autorizado"]:
        vista["mensaje"] = "Examen bloqueado. El acceso está restringido hasta la apertura"
        if vista["reloj"] and vista["apertura"]:
            segundos = ceil((datetime.fromisoformat(vista["apertura"]["iso"]) -
                             datetime.fromisoformat(vista["reloj"]["iso"])).total_seconds())
            if segundos == 1:
                vista["mensaje"] = "Examen bloqueado. Falta 1 segundo para la apertura"
    elif decision["motivo"] == "evaluacion_no_asignada":
        vista["mensaje"] = "Acceso restringido. No tienes esta evaluación asignada. Cumplir el horario no autoriza el acceso sin asignación."
    return {**decision, "presentacion": vista}
