"""RBAC de paneles y política ABAC reutilizable de disponibilidad de evaluaciones."""

from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, Request

from app.audit import registrar
from app.db import conexion
from app.sessions import NOMBRE_COOKIE, buscar
from app.clock import interpretar_instante, leer_reloj


@dataclass(frozen=True)
class DecisionDisponibilidad:
    codigo: int
    motivo: str
    mensaje: str
    evaluacion: dict | None = None


def decidir_disponibilidad(db, sesion, evaluacion_id: str, instante: datetime | None) -> DecisionDisponibilidad:
    """Evalúa identidad, rol, asignación y fecha en ese orden; no entrega archivos."""
    if not sesion or sesion["nivel"] != "completa":
        return DecisionDisponibilidad(401, "sesion_incompleta", "Inicia sesión para consultar esta evaluación.")
    if sesion["rol"] != "ESTUDIANTE":
        return DecisionDisponibilidad(403, "rol_incorrecto", "Esta consulta está reservada al estudiante asignado.")
    evaluacion = db.execute(
        """SELECT e.* FROM evaluaciones e JOIN asignaciones a ON a.evaluacion_id=e.id
           WHERE e.id=? AND a.cuenta_id=?""", (evaluacion_id, sesion["cuenta_id"]),
    ).fetchone()
    if not evaluacion:
        # La misma respuesta evita revelar metadatos de evaluaciones ajenas o ausentes.
        return DecisionDisponibilidad(403, "evaluacion_no_asignada", "No tienes esta evaluación asignada.")
    datos = dict(evaluacion)
    if instante is None:
        return DecisionDisponibilidad(503, "configuracion_horaria_invalida", "La disponibilidad no puede comprobarse temporalmente.")
    if instante < interpretar_instante(datos["apertura"]):
        return DecisionDisponibilidad(403, "fuera_de_horario", "El acceso está restringido hasta la fecha y hora de apertura.", datos)
    return DecisionDisponibilidad(200, "apertura_cumplida", "Acceso autorizado por asignación y horario. La descarga de documentos aún no está habilitada.", datos)


def consultar_disponibilidad(config, token: str | None, evaluacion_id: str) -> dict:
    """Revalida identidad y atributos persistidos y registra ambos tiempos atómicamente."""
    with conexion(config, escritura=True) as db:
        sesion = buscar(db, token)
        try:
            instante = leer_reloj(db)
        except ValueError:
            instante = None
        hora_decision = instante.isoformat() if instante else None
        try:
            decision = decidir_disponibilidad(db, sesion, evaluacion_id, instante)
        except ValueError:
            # Una configuración ausente/corrupta nunca se convierte en apertura.
            decision = DecisionDisponibilidad(503, "configuracion_horaria_invalida", "La disponibilidad no puede comprobarse temporalmente.")
        registrar(db, "consultar_disponibilidad", "permitido" if decision.codigo == 200 else "denegado",
                  decision.motivo, sesion["cuenta_id"] if sesion else None,
                  evaluacion_id, hora_decision)
    return {
        "codigo": decision.codigo,
        "evaluacion_id": evaluacion_id,
        "autorizado": decision.codigo == 200,
        "motivo": decision.motivo,
        "mensaje": decision.mensaje,
        "evaluacion": decision.evaluacion,
        "hora_referencia": hora_decision if decision.evaluacion else None,
        "zona_horaria": "America/Bogota",
        "descarga_habilitada": False,
    }


def exigir_rol(rol: str):
    """Revalida cuenta, sesión completa y rol desde SQLite, nunca desde formularios."""
    def comprobar(request: Request):
        config = request.app.state.config
        with conexion(config, escritura=True) as db:
            sesion = buscar(db, request.cookies.get(NOMBRE_COOKIE))
            codigo = 401 if not sesion or sesion["nivel"] != "completa" else 403 if sesion["rol"] != rol else 200
            if codigo == 200 and rol == "DOCENTE" and not sesion["mfa_verificada"]:
                codigo = 401
            registrar(db, "acceso_panel", "permitido" if codigo == 200 else "denegado",
                      "rol_valido" if codigo == 200 else "sesion_incompleta" if codigo == 401 else "rol_incorrecto",
                      sesion["cuenta_id"] if sesion else None)
        if codigo != 200:
            raise HTTPException(codigo, "Inicia sesión para continuar." if codigo == 401 else "No tienes permiso para acceder a esta área.")
        return dict(sesion)
    return comprobar
