"""Administración local interactiva; no existe una ruta HTTP de aprovisionamiento."""

import argparse
import getpass
import os
import secrets
import sys

import pyotp

from app.audit import registrar
from app.config import configuracion_entorno
from app.db import conexion, inicializar_base
from app.security import derivar_clave, paso_totp


def solicitar_clave(rol: str) -> str:
    """Lee sin eco ni argumentos de proceso; exige confirmación y 12–128 caracteres."""
    clave = getpass.getpass(f"Contraseña de {rol} (12–128 caracteres): ")
    if not 12 <= len(clave) <= 128 or clave != getpass.getpass("Confirmar contraseña: "):
        raise ValueError("Longitud o confirmación de contraseña incorrecta.")
    return clave


def guardar_cuentas(config, clave_docente: str, clave_estudiante: str, secreto: str, paso: int):
    """Crea exactamente dos identidades; no sobrescribe cuentas o secreto existentes."""
    if secrets.compare_digest(clave_docente.encode(), clave_estudiante.encode()):
        raise ValueError("Las cuentas deben usar contraseñas diferentes.")
    hashes = [derivar_clave(clave_docente), derivar_clave(clave_estudiante)]
    carpeta = config.datos / "secrets"
    carpeta.mkdir(mode=0o700, exist_ok=True)
    ruta = carpeta / "docente.totp"
    creado = False
    try:
        with conexion(config, escritura=True) as db:
            if db.execute("SELECT COUNT(*) FROM cuentas").fetchone()[0]:
                raise ValueError("Las cuentas ya están inicializadas. No se modificaron.")
            descriptor = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            creado = True
            with os.fdopen(descriptor, "w", encoding="ascii") as archivo:
                archivo.write(secreto)
            db.executemany("INSERT INTO cuentas(nombre,rol,clave_hash,ultimo_paso_totp) VALUES(?,?,?,?)",
                           [("docente", "DOCENTE", hashes[0], paso),
                            ("estudiante", "ESTUDIANTE", hashes[1], -1)])
            registrar(db, "aprovisionamiento", "permitido", "cuentas_locales_creadas")
    except Exception:
        # Solo retira el archivo que esta operación acaba de crear si falla el alta.
        if creado:
            ruta.unlink(missing_ok=True)
        raise


def principal():
    """Los comandos privilegiados requieren terminal local y acceso al contenedor."""
    parser = argparse.ArgumentParser(description="Administración local de identidades ficticias")
    parser.add_argument("accion", choices=["inicializar", "revocar-sesiones"])
    argumentos = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error("Se requiere una terminal interactiva; no se aceptan contraseñas por tubería.")
    config = configuracion_entorno()
    inicializar_base(config)
    try:
        with conexion(config) as db:
            existentes = db.execute("SELECT COUNT(*) FROM cuentas").fetchone()[0]
        if argumentos.accion == "revocar-sesiones":
            if input("Escriba REVOCAR para cerrar todas las sesiones: ") != "REVOCAR":
                raise ValueError("Operación cancelada.")
            with conexion(config, escritura=True) as db:
                db.execute("DELETE FROM sesiones")
                registrar(db, "administracion", "permitido", "sesiones_revocadas")
            print("Sesiones revocadas.")
            return
        if existentes:
            raise ValueError("Las cuentas ya están inicializadas. No se modificaron.")
        docente = solicitar_clave("docente")
        estudiante = solicitar_clave("estudiante")
        secreto = pyotp.random_base32()
        print("Enrolamiento privado: no capture, registre ni comparta esta pantalla.")
        print("Secreto para autenticador TOTP:", secreto)
        print("URI para un autenticador local compatible:")
        print(pyotp.TOTP(secreto).provisioning_uri(name="docente", issuer_name="El sobre de las ocho"))
        paso = paso_totp(secreto, getpass.getpass("Código actual del autenticador: "))
        if paso is None:
            raise ValueError("Código no válido. No se crearon cuentas; repita el enrolamiento.")
        guardar_cuentas(config, docente, estudiante, secreto, paso)
        print("Cuentas docente y estudiante inicializadas. Espere al siguiente código para iniciar sesión.")
    except (ValueError, OSError) as error:
        # Los mensajes previstos no incluyen valores de credenciales o códigos.
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    principal()
