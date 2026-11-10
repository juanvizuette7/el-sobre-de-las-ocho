"""Sesiones opacas de servidor; la cookie no almacena rol ni identidad."""

import hashlib
import secrets
import time

NOMBRE_COOKIE = "sobre_sesion"


def huella(token: str) -> str:
    """Solo se conserva una huella SHA-256 del token aleatorio en SQLite."""
    return hashlib.sha256(token.encode()).hexdigest()


def buscar(db, token: str | None):
    """Comprueba vigencia y estado actual de cuenta en cada consulta."""
    if not token or len(token) > 128:
        return None
    return db.execute(
        """SELECT s.*, c.nombre, c.rol, c.activa FROM sesiones s
        LEFT JOIN cuentas c ON c.id=s.cuenta_id
        WHERE s.token_hash=? AND s.vence>? AND (c.activa=1 OR s.cuenta_id IS NULL)""",
        (huella(token), int(time.time())),
    ).fetchone()


def crear(db, nivel: str, duracion: int, cuenta_id=None, anterior: str | None = None, mfa=False):
    """Rota token y CSRF; elimina el token anterior dentro de la transacción."""
    ahora = int(time.time())
    db.execute("DELETE FROM sesiones WHERE vence<=?", (ahora,))
    if anterior:
        db.execute("DELETE FROM sesiones WHERE token_hash=?", (huella(anterior),))
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.execute("INSERT INTO sesiones VALUES(?,?,?,?,?,?,?)",
               (huella(token), cuenta_id, nivel, csrf, ahora, ahora + duracion, int(mfa)))
    return token, csrf


def fijar_cookie(respuesta, token: str, config, duracion: int):
    """Secure se activa automáticamente cuando el origen configurado usa HTTPS."""
    respuesta.set_cookie(NOMBRE_COOKIE, token, max_age=duracion, httponly=True,
                         secure=config.cookie_secure, samesite="lax", path="/")


def excede_limite(db, clave: str, limite: int, ventana: int) -> bool:
    """Cuenta intentos en SQLite, incluso al reiniciar o renovar el navegador."""
    ahora = int(time.time())
    db.execute("DELETE FROM intentos WHERE inicio<=?", (ahora - ventana,))
    clave_hash = huella(clave)
    fila = db.execute("SELECT cantidad FROM intentos WHERE clave=?", (clave_hash,)).fetchone()
    if fila and fila[0] >= limite:
        return True
    db.execute("""INSERT INTO intentos VALUES(?,?,1) ON CONFLICT(clave)
               DO UPDATE SET cantidad=cantidad+1""", (clave_hash, ahora))
    return False
