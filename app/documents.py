"""Publicación autenticada y entrega completa del sobre sobre la política existente."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from app.audit import registrar
from app.clock import leer_reloj
from app.db import conexion
from app.policy import DecisionDisponibilidad, consultar_disponibilidad, decidir_disponibilidad, exigir_rol
from app.sessions import NOMBRE_COOKIE, buscar
from app.storage import (FalloSobre, MAX_ARCHIVO, limpiar_huerfanos, metadatos,
                         publicar_en_transaccion, recuperar, tiempo_recurso)

router = APIRouter()
ID_VALIDO = r"^[a-zA-Z0-9_-]{1,64}$"


def resolver_documento(config, token, identificador, entregar=False):
    """Reutiliza RBAC/ABAC; ningún fallo permite emitir bytes parciales del examen."""
    decision = consultar_disponibilidad(config, token, identificador)
    contenido = None
    with conexion(config, True) as db:
        sesion = buscar(db, token)
        referencia = tiempo_recurso(db)
        # Revalidar dentro del bloqueo que protege lectura, versión, integridad y auditoría.
        try:
            actual = decidir_disponibilidad(db, sesion, identificador,
                                           leer_reloj(db) if referencia else None) if decision["autorizado"] else None
        except ValueError:
            actual = DecisionDisponibilidad(503, "configuracion_horaria_invalida", "La disponibilidad no puede comprobarse temporalmente.")
        if actual and actual.codigo != 200:
            decision.update(codigo=actual.codigo, autorizado=False, motivo=actual.motivo,
                            mensaje=actual.mensaje, evaluacion=actual.evaluacion,
                            hora_referencia=referencia if actual.evaluacion else None)
        if actual and actual.codigo == 200:
            decision["hora_referencia"] = referencia
        documento = db.execute("SELECT * FROM documentos WHERE evaluacion_id=?", (identificador,)).fetchone() if decision["evaluacion"] else None
        decision["documento"] = metadatos(documento)
        decision["estado_documento"] = "Documento protegido disponible." if documento else "Aún no hay un documento publicado."
        if decision["autorizado"] and documento:
            try:
                contenido = recuperar(config, db, documento)
                decision["descarga_habilitada"] = True
                decision["estado_documento"] = "Documento verificado. Disponible para descarga."
            except FalloSobre as fallo:
                decision.update(codigo=409, autorizado=False, motivo=fallo.motivo,
                                mensaje="Integridad comprometida. La entrega del documento está bloqueada.",
                                estado_documento="No se pudo verificar la integridad del documento. La entrega está bloqueada.")
                registrar(db, "verificar_integridad", "denegado", fallo.motivo,
                          sesion["cuenta_id"] if sesion else None, identificador, referencia)
        if entregar and decision["autorizado"] and not documento:
            decision.update(codigo=404, motivo="documento_no_publicado", mensaje="El documento aún no ha sido publicado.")
        if entregar:
            registrar(db, "descargar_documento", "permitido" if decision["descarga_habilitada"] else "denegado",
                      "original_verificado" if decision["descarga_habilitada"] else decision["motivo"],
                      sesion["cuenta_id"] if sesion else None, identificador, referencia)
    return decision, contenido


def autorizar_carga(request: Request):
    """Reutiliza RBAC/MFA y registra el propósito de los rechazos de publicación."""
    try:
        return exigir_rol("DOCENTE")(request)
    except HTTPException as fallo:
        with conexion(request.app.state.config, True) as db:
            sesion = buscar(db, request.cookies.get(NOMBRE_COOKIE))
            registrar(db, "publicar_documento", "denegado", "identidad_o_rol_invalido",
                      sesion["cuenta_id"] if sesion else None,
                      request.path_params.get("evaluacion_id"), tiempo_recurso(db))
        raise fallo


async def leer_carga(request):
    """Acota el cuerpo completo antes del parser, incluso con transferencia fragmentada."""
    if not request.headers.get("content-type", "").lower().startswith("multipart/form-data;"):
        raise HTTPException(400, "Formulario de documento no válido.")
    cuerpo = bytearray()
    async for bloque in request.stream():
        cuerpo.extend(bloque)
        if len(cuerpo) > MAX_ARCHIVO + 16384:
            raise HTTPException(413, "El documento no puede superar 512 KiB.")

    async def flujo():
        yield bytes(cuerpo)

    try:
        return await MultiPartParser(request.headers, flujo(), max_files=1, max_fields=2,
                                     max_part_size=MAX_ARCHIVO + 16384).parse()
    except (MultiPartException, ValueError):
        raise HTTPException(400, "Formulario de documento no válido.") from None


@router.post("/evaluaciones/{evaluacion_id}/documento")
async def subir_documento(request: Request, evaluacion_id: str = Path(pattern=ID_VALIDO),
                          sesion=Depends(autorizar_carga)):
    """Valida rol/MFA antes de procesar archivos y revalida sesión/CSRF al publicar."""
    config = request.app.state.config
    try:
        campos = await leer_carga(request)
    except HTTPException:
        with conexion(config, True) as db:
            registrar(db, "publicar_documento", "denegado", "formulario_invalido", sesion["cuenta_id"], evaluacion_id, tiempo_recurso(db))
        raise
    try:
        archivo = campos.get("documento")
        token = campos.get("csrf")
        contenido = await archivo.read(MAX_ARCHIVO + 1) if isinstance(archivo, UploadFile) else b""
        with conexion(config, True) as db:
            actual = buscar(db, request.cookies.get(NOMBRE_COOKIE))
            if not actual or actual["nivel"] != "completa":
                codigo, motivo = 401, "sesion_incompleta"
            elif actual["rol"] != "DOCENTE" or not actual["mfa_verificada"]:
                codigo, motivo = 403, "rol_incorrecto"
            elif (not isinstance(token, str) or not token.isascii() or len(token) > 128
                  or not secrets.compare_digest(actual["csrf"], token)
                  or request.headers.get("origin") != config.origen):
                codigo, motivo = 403, "csrf_invalido"
            else:
                codigo, motivo = 200, None
            if codigo != 200:
                registrar(db, "publicar_documento", "denegado", motivo, sesion["cuenta_id"], evaluacion_id)
            else:
                try:
                    publicar_en_transaccion(config, db, evaluacion_id,
                                            archivo.filename if isinstance(archivo, UploadFile) else "",
                                            contenido, actual["cuenta_id"])
                except ValueError as fallo:
                    codigo, motivo = 400, str(fallo)
                    registrar(db, "publicar_documento", "denegado", "archivo_invalido", actual["cuenta_id"], evaluacion_id, tiempo_recurso(db))
                except (FalloSobre, OSError):
                    codigo, motivo = 503, "No se pudo almacenar el documento de forma segura."
                    registrar(db, "publicar_documento", "denegado", "almacen_no_disponible", actual["cuenta_id"], evaluacion_id, tiempo_recurso(db))
        if codigo != 200:
            raise HTTPException(codigo, motivo if codigo in (400, 503) else "La solicitud no pudo validarse. Inicia sesión y vuelve a intentarlo.")
        limpiar_huerfanos(config)
        return RedirectResponse("/docente?publicado=1", 303)
    finally:
        await campos.close()


@router.get("/evaluaciones/{evaluacion_id}/documento")
def descargar_documento(request: Request, evaluacion_id: str = Path(pattern=ID_VALIDO)):
    decision, contenido = resolver_documento(request.app.state.config, request.cookies.get(NOMBRE_COOKIE),
                                            evaluacion_id, entregar=True)
    if not decision["descarga_habilitada"]:
        raise HTTPException(decision["codigo"], decision["mensaje"])
    return Response(contenido, media_type="text/plain; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="{decision["documento"]["nombre"]}"',
        "Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff"})
