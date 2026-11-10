"""Entrada HTTP de la etapa 1: portada, recursos públicos y salud del proceso."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

DIRECTORIO_APP = Path(__file__).resolve().parent

# La portada funciona sin CDN; no se habilita documentación interactiva externa.
app = FastAPI(title="El sobre de las ocho", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=DIRECTORIO_APP / "static"), name="static")
plantillas = Jinja2Templates(directory=DIRECTORIO_APP / "templates")


class EstadoSalud(BaseModel):
    """Contrato pequeño de salud; no representa controles de seguridad futuros."""

    status: str
    servicio: str
    etapa: int


@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request) -> HTMLResponse:
    """Renderiza la portada; no crea sesiones ni simula permisos de descarga."""
    return plantillas.TemplateResponse(request=request, name="index.html")


@app.get("/health", response_model=EstadoSalud)
async def salud() -> EstadoSalud:
    """Confirma que FastAPI puede responder, sin consultar datos sensibles."""
    return EstadoSalud(status="ok", servicio="el-sobre-de-las-ocho", etapa=1)
