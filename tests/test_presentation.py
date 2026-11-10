"""Contratos visuales de fecha/hora sin modificar la decisión de autorización."""

import pytest

from app.presentation import fecha_hora_visual, presentar_decision


@pytest.mark.parametrize("iso,hora,fecha", [
    ("2026-11-09T07:59:59-05:00", "7:59:59 a. m.", "lunes, 9 de noviembre de 2026"),
    ("2026-11-10T20:00:01-05:00", "8:00:01 p. m.", "martes, 10 de noviembre de 2026"),
    ("2026-11-10T00:00:00-05:00", "12:00:00 a. m.", "martes, 10 de noviembre de 2026"),
    ("2026-11-10T17:00:00+00:00", "12:00:00 p. m.", "martes, 10 de noviembre de 2026"),
])
def test_formato_espanol_y_hora_12(iso, hora, fecha):
    vista = fecha_hora_visual(iso)
    assert vista["hora"] == hora and vista["fecha"] == fecha


def test_limite_visual_y_decision_original_intacta():
    original = {"codigo": 403, "autorizado": False, "motivo": "fuera_de_horario",
                "mensaje": "Restricción del servidor", "hora_referencia": "2026-11-09T07:59:59-05:00",
                "evaluacion": {"apertura": "2026-11-09T08:00:00-05:00"}}
    vista = presentar_decision(original)
    assert vista["presentacion"]["mensaje"] == "Examen bloqueado. Falta 1 segundo para la apertura"
    assert vista["presentacion"]["apertura"]["hora"] == "8:00 a. m."
    assert "presentacion" not in original
    assert all(vista[clave] == valor for clave, valor in original.items())
    original.update(codigo=200, autorizado=True, motivo="apertura_cumplida", hora_referencia="2026-11-09T08:00:00-05:00")
    assert presentar_decision(original)["presentacion"]["mensaje"] == "Horario cumplido. Acceso autorizado"


def test_sin_asignacion_no_inventa_hora_ni_autoriza():
    original = {"codigo": 403, "autorizado": False, "motivo": "evaluacion_no_asignada",
                "mensaje": "No asignada", "evaluacion": None, "hora_referencia": None}
    vista = presentar_decision(original)["presentacion"]
    assert vista["reloj"] is None and vista["apertura"] is None
    assert vista["estado"] == "restricted"
    assert "Cumplir el horario no autoriza el acceso sin asignación" in vista["mensaje"]
