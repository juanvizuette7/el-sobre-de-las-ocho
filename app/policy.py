"""Dependencias de autorización RBAC; futuras reglas de recurso serán adicionales."""

from fastapi import HTTPException, Request

from app.audit import registrar
from app.db import conexion
from app.sessions import NOMBRE_COOKIE, buscar


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
