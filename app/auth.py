"""Acceso con CSRF, límites persistentes y elevación mediante TOTP."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from app.audit import registrar
from app.db import conexion
from app.evaluations import evaluaciones_del_panel
from app.policy import exigir_rol
from app.security import leer_secreto, paso_totp, verificar_clave
from app.sessions import NOMBRE_COOKIE, buscar, crear, excede_limite, fijar_cookie

router = APIRouter()


def pagina(request, nombre, **contexto):
    """Renderiza sin incorporar entradas sensibles al contexto."""
    return request.app.state.plantillas.TemplateResponse(request=request, name=nombre, context=contexto)


def destino(rol):
    return "/docente" if rol == "DOCENTE" else "/estudiante"


async def formulario_seguro(request: Request):
    """Exige token sincronizado y origen exacto, también en login, MFA y salida."""
    config = request.app.state.config
    cuerpo = await request.body()
    if len(cuerpo) > 8192 or not request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        raise HTTPException(400, "Solicitud no válida.")
    campos = await request.form(max_files=0, max_fields=6)
    with conexion(config, escritura=True) as db:
        sesion = buscar(db, request.cookies.get(NOMBRE_COOKIE))
        token = campos.get("csrf", "")
        valido = (sesion and isinstance(token, str) and token.isascii() and len(token) <= 128
                  and secrets.compare_digest(sesion["csrf"], token)
                  and request.headers.get("origin") == config.origen)
        if not valido:
            registrar(db, "solicitud", "denegado", "csrf_invalido", sesion["cuenta_id"] if sesion else None)
    if not valido:
        raise HTTPException(403, "La solicitud no pudo validarse. Vuelve a abrir el formulario.")
    return campos, dict(sesion)


@router.get("/acceso")
def acceso(request: Request):
    """Emite una sesión anónima para proteger el formulario de autenticación."""
    config = request.app.state.config
    token_nuevo = None
    with conexion(config, escritura=True) as db:
        sesion = buscar(db, request.cookies.get(NOMBRE_COOKIE))
        if sesion and sesion["nivel"] == "completa":
            return RedirectResponse(destino(sesion["rol"]), 303)
        if sesion and sesion["nivel"] == "mfa":
            return RedirectResponse("/acceso/totp", 303)
        if not sesion:
            token_nuevo, csrf = crear(db, "anonima", config.duracion_previa)
        else:
            csrf = sesion["csrf"]
    respuesta = pagina(request, "acceso.html", csrf=csrf, mfa=False)
    if token_nuevo:
        fijar_cookie(respuesta, token_nuevo, config, config.duracion_previa)
    return respuesta


@router.post("/acceso")
async def identificar(request: Request):
    """La contraseña docente habilita el desafío; no concede acceso privado."""
    config = request.app.state.config
    campos, sesion = await formulario_seguro(request)
    if sesion["nivel"] != "anonima":
        raise HTTPException(403, "Cierra la sesión actual antes de iniciar otra.")
    nombre = str(campos.get("usuario", "")).strip().lower()[:64]
    clave = str(campos.get("clave", ""))
    with conexion(config, escritura=True) as db:
        bloqueado = excede_limite(db, "clave:" + nombre, config.limite_intentos, config.ventana_intentos)
        bloqueado |= excede_limite(db, "origen:" + (request.client.host if request.client else "local"), 30, config.ventana_intentos)
        cuenta = db.execute("SELECT * FROM cuentas WHERE nombre=?", (nombre,)).fetchone()
        if bloqueado:
            registrar(db, "autenticacion", "denegado", "limite_intentos", cuenta["id"] if cuenta else None)
    if bloqueado:
        raise HTTPException(429, "Demasiados intentos. Espera cinco minutos antes de volver a intentarlo.")
    derivado = cuenta["clave_hash"] if cuenta else request.app.state.hash_senuelo
    valido = await run_in_threadpool(verificar_clave, derivado, clave[:256])
    if not cuenta or not cuenta["activa"] or not valido or not 1 <= len(clave) <= 128:
        with conexion(config, escritura=True) as db:
            registrar(db, "autenticacion", "denegado", "credenciales_invalidas", cuenta["id"] if cuenta else None)
        respuesta = pagina(request, "acceso.html", csrf=sesion["csrf"], mfa=False,
                           error="Usuario o contraseña incorrectos.")
        respuesta.status_code = 401
        return respuesta
    nivel = "mfa" if cuenta["rol"] == "DOCENTE" else "completa"
    duracion = config.duracion_mfa if nivel == "mfa" else config.duracion_sesion
    with conexion(config, escritura=True) as db:
        vigente = buscar(db, request.cookies.get(NOMBRE_COOKIE))
        if not vigente or vigente["nivel"] != "anonima":
            raise HTTPException(401, "La sesión expiró. Inicia sesión nuevamente.")
        token, _ = crear(db, nivel, duracion, cuenta["id"], request.cookies.get(NOMBRE_COOKIE))
        registrar(db, "autenticacion", "pendiente" if nivel == "mfa" else "permitido",
                  "segundo_factor_requerido" if nivel == "mfa" else "credenciales_validas", cuenta["id"])
    respuesta = RedirectResponse("/acceso/totp" if nivel == "mfa" else destino(cuenta["rol"]), 303)
    fijar_cookie(respuesta, token, config, duracion)
    return respuesta


@router.get("/acceso/totp")
def desafio_totp(request: Request):
    """No entrega el secreto, URI de enrolamiento ni códigos de autenticación."""
    with conexion(request.app.state.config) as db:
        sesion = buscar(db, request.cookies.get(NOMBRE_COOKIE))
    if not sesion or sesion["nivel"] != "mfa" or sesion["rol"] != "DOCENTE":
        raise HTTPException(401, "Inicia sesión para continuar.")
    return pagina(request, "acceso.html", csrf=sesion["csrf"], mfa=True)


@router.post("/acceso/totp")
async def completar_totp(request: Request):
    """Consume el paso TOTP atómicamente para impedir la repetición del código."""
    config = request.app.state.config
    campos, sesion = await formulario_seguro(request)
    if sesion["nivel"] != "mfa" or sesion["rol"] != "DOCENTE":
        raise HTTPException(401, "Inicia sesión para continuar.")
    try:
        secreto = leer_secreto(config)
        paso = paso_totp(secreto, str(campos.get("codigo", "")))
    except (OSError, ValueError):
        with conexion(config, escritura=True) as db:
            registrar(db, "mfa", "denegado", "secreto_no_disponible", sesion["cuenta_id"])
        raise HTTPException(503, "El servicio de autenticación no está disponible.") from None
    with conexion(config, escritura=True) as db:
        actual = buscar(db, request.cookies.get(NOMBRE_COOKIE))
        if not actual or actual["nivel"] != "mfa":
            raise HTTPException(401, "La sesión expiró. Inicia sesión nuevamente.")
        bloqueado = excede_limite(db, "mfa:" + str(actual["cuenta_id"]), config.limite_intentos, config.ventana_intentos)
        cuenta = db.execute("SELECT ultimo_paso_totp FROM cuentas WHERE id=?", (actual["cuenta_id"],)).fetchone()
        if bloqueado or paso is None or paso <= cuenta[0]:
            registrar(db, "mfa", "denegado", "limite_intentos" if bloqueado else "codigo_invalido_o_reutilizado", actual["cuenta_id"])
            token = None
        else:
            db.execute("UPDATE cuentas SET ultimo_paso_totp=? WHERE id=?", (paso, actual["cuenta_id"]))
            token, _ = crear(db, "completa", config.duracion_sesion, actual["cuenta_id"], request.cookies.get(NOMBRE_COOKIE), mfa=True)
            registrar(db, "mfa", "permitido", "segundo_factor_valido", actual["cuenta_id"])
    if not token:
        if bloqueado:
            raise HTTPException(429, "Demasiados intentos. Espera cinco minutos antes de volver a intentarlo.")
        respuesta = pagina(request, "acceso.html", csrf=sesion["csrf"], mfa=True,
                           error="Código incorrecto, vencido o ya utilizado.")
        respuesta.status_code = 401
        return respuesta
    respuesta = RedirectResponse("/docente", 303)
    fijar_cookie(respuesta, token, config, config.duracion_sesion)
    return respuesta


@router.post("/salir")
async def salir(request: Request):
    """Revoca sesión o desafío en servidor, además de eliminar la cookie."""
    _, sesion = await formulario_seguro(request)
    config = request.app.state.config
    with conexion(config, escritura=True) as db:
        db.execute("DELETE FROM sesiones WHERE token_hash=?", (sesion["token_hash"],))
        registrar(db, "salida", "permitido", "sesion_revocada", sesion["cuenta_id"])
    respuesta = RedirectResponse("/acceso", 303)
    respuesta.delete_cookie(NOMBRE_COOKIE, httponly=True, secure=config.cookie_secure, samesite="lax")
    return respuesta


@router.get("/docente")
def panel_docente(request: Request, sesion=Depends(exigir_rol("DOCENTE"))):
    """No habilita publicación ni controles administrativos."""
    return pagina(request, "panel.html", sesion=sesion, docente=True,
                  evaluaciones=evaluaciones_del_panel(request, sesion, docente=True))


@router.get("/estudiante")
def panel_estudiante(request: Request, sesion=Depends(exigir_rol("ESTUDIANTE"))):
    """Panel privado con asignaciones y decisión de disponibilidad, sin documentos."""
    return pagina(request, "panel.html", sesion=sesion, docente=False,
                  evaluaciones=evaluaciones_del_panel(request, sesion, docente=False))
