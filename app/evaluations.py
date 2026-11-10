"""Consultas de metadatos de evaluación sobre la persistencia y política existentes."""

from fastapi import APIRouter, Path, Request
from fastapi.responses import JSONResponse

from app.db import conexion
from app.policy import consultar_disponibilidad
from app.sessions import NOMBRE_COOKIE

router = APIRouter()


def evaluaciones_del_panel(request: Request, sesion, docente: bool) -> list[dict]:
    """La lista estudiante se obtiene por asignación, nunca mediante un ID de cliente."""
    config = request.app.state.config
    with conexion(config) as db:
        if docente:
            filas = db.execute(
                """SELECT e.*, c.nombre AS estudiante FROM evaluaciones e
                   LEFT JOIN asignaciones a ON a.evaluacion_id=e.id
                   LEFT JOIN cuentas c ON c.id=a.cuenta_id ORDER BY e.id""",
            ).fetchall()
            return [dict(fila) for fila in filas]
        ids = [fila[0] for fila in db.execute(
            "SELECT evaluacion_id FROM asignaciones WHERE cuenta_id=? ORDER BY evaluacion_id",
            (sesion["cuenta_id"],),
        )]
    return [consultar_disponibilidad(config, request.cookies.get(NOMBRE_COOKIE), identificador)
            for identificador in ids]


@router.get("/evaluaciones/{evaluacion_id}/disponibilidad")
def disponibilidad(request: Request, evaluacion_id: str = Path(pattern=r"^[a-zA-Z0-9_-]{1,64}$")):
    """Expone una decisión real JSON; un 200 no representa descarga o integridad."""
    decision = consultar_disponibilidad(request.app.state.config, request.cookies.get(NOMBRE_COOKIE), evaluacion_id)
    return JSONResponse(decision, status_code=decision["codigo"])
