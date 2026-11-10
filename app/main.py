"""Aplicación FastAPI: portada pública, identidad, paneles privados y salud."""

import secrets
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.auth import router
from app.config import Configuracion, configuracion_entorno
from app.db import inicializar_base
from app.security import derivar_clave
from app.evaluations import router as router_evaluaciones
from app.documents import router as router_documentos

DIRECTORIO_APP = Path(__file__).resolve().parent


def crear_aplicacion(config: Configuracion | None = None) -> FastAPI:
    """Permite aislar la base de cada prueba sin tocar las cuentas del portal."""
    config = config or configuracion_entorno()

    @asynccontextmanager
    async def ciclo_vida(aplicacion):
        inicializar_base(config)
        aplicacion.state.hash_senuelo = derivar_clave(secrets.token_urlsafe(32))
        yield

    aplicacion = FastAPI(title="El sobre de las ocho", docs_url=None, redoc_url=None,
                        openapi_url=None, lifespan=ciclo_vida)
    aplicacion.state.config = config
    aplicacion.state.plantillas = Jinja2Templates(directory=DIRECTORIO_APP / "templates")
    aplicacion.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    aplicacion.mount("/static", StaticFiles(directory=DIRECTORIO_APP / "static"), name="static")
    aplicacion.include_router(router)
    aplicacion.include_router(router_evaluaciones)
    aplicacion.include_router(router_documentos)

    @aplicacion.middleware("http")
    async def proteger_respuestas(request: Request, siguiente):
        respuesta = await siguiente(request)
        if not request.url.path.startswith("/static/"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    @aplicacion.exception_handler(HTTPException)
    async def error_http(request: Request, error: HTTPException):
        respuesta = aplicacion.state.plantillas.TemplateResponse(
            request=request, name="error.html", context={"mensaje": error.detail, "codigo": error.status_code})
        respuesta.status_code = error.status_code
        return respuesta

    @aplicacion.exception_handler(sqlite3.Error)
    async def error_almacenamiento(request: Request, error: sqlite3.Error):
        # Un fallo de almacenamiento no debe habilitar acceso ni exponer SQL o rutas.
        return await error_http(request, HTTPException(503, "El servicio no está disponible temporalmente."))

    @aplicacion.get("/")
    def inicio(request: Request):
        """Mantiene la portada pública sin emitir sesión automáticamente."""
        return aplicacion.state.plantillas.TemplateResponse(request=request, name="index.html")

    @aplicacion.get("/health")
    def salud():
        """Conserva el contrato de infraestructura de etapa 1; no acredita MFA."""
        return {"status": "ok", "servicio": "el-sobre-de-las-ocho", "etapa": 1}

    return aplicacion


app = crear_aplicacion()
