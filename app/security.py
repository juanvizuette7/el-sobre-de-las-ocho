"""Argon2id y TOTP sobre tiempo real; independientes del futuro reloj de apertura."""

import re
import secrets
import threading
import time

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Una verificación simultánea limita el consumo Argon2 dentro del contenedor.
ARGON2 = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
CERROJO_HASH = threading.Semaphore(1)


def derivar_clave(clave: str) -> str:
    """La biblioteca genera una sal aleatoria independiente en cada derivación."""
    with CERROJO_HASH:
        return ARGON2.hash(clave)


def verificar_clave(derivado: str, clave: str) -> bool:
    """Evita propagar detalles del derivado a la respuesta HTTP."""
    with CERROJO_HASH:
        try:
            return ARGON2.verify(derivado, clave)
        except (VerificationError, InvalidHashError):
            return False


def paso_totp(secreto: str, codigo: str, ahora: int | None = None) -> int | None:
    """Devuelve el paso coincidente de 30 s, con tolerancia de un paso por lado."""
    if not re.fullmatch(r"[0-9]{6}", codigo):
        return None
    paso_actual = (int(time.time()) if ahora is None else ahora) // 30
    totp = pyotp.TOTP(secreto)
    for paso in (paso_actual, paso_actual - 1, paso_actual + 1):
        if secrets.compare_digest(totp.at(paso * 30), codigo):
            return paso
    return None


def leer_secreto(config) -> str:
    """El secreto está en el volumen privado; no se entrega mediante rutas web."""
    return (config.datos / "secrets" / "docente.totp").read_text(encoding="ascii").strip()
