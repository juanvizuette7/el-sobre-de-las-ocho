"""Almacén privado versionado y operaciones locales del sobre, sin rutas web."""

import hmac
import json
import os
import re
import secrets
import unicodedata
from datetime import datetime
from pathlib import Path

from cryptography.exceptions import InvalidTag

from app.audit import registrar
from app.clock import BOGOTA, leer_reloj
from app.crypto import aad, cargar_privada, cifrar, descifrar, huella, nueva_privada
from app.db import conexion
from app.presentation import fecha_hora_visual

MAX_ARCHIVO = 512 * 1024
MAX_ALMACEN = 32 * 1024 * 1024
TEXTO_PRUEBA = b"EL SOBRE DE LAS OCHO\nEvaluacion ficticia.\nPregunta 1: Explique confidencialidad e integridad.\n"


class FalloSobre(Exception):
    """Solo motivos internos fijos; la capa HTTP no publica detalles criptográficos."""
    def __init__(self, motivo):
        self.motivo = motivo
        super().__init__(motivo)


def validar_texto(nombre: str, contenido: bytes) -> str:
    """Lista permitida TXT/UTF-8; extensión y MIME por sí solos no validan bytes."""
    if not nombre or len(nombre) > 160 or any(c in nombre for c in '/\\') or any(ord(c) < 32 for c in nombre):
        raise ValueError("Nombre de archivo no válido.")
    if not nombre.lower().endswith(".txt"):
        raise ValueError("Selecciona un documento de texto UTF-8 con extensión .txt.")
    if not 0 < len(contenido) <= MAX_ARCHIVO:
        raise ValueError("El documento debe contener texto y no superar 512 KiB.")
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("El documento debe contener texto UTF-8 válido.") from None
    if not texto.strip() or any(unicodedata.category(c).startswith("C") and c not in '\n\r\t' for c in texto):
        raise ValueError("El documento contiene caracteres no permitidos.")
    seguro = unicodedata.normalize("NFKD", nombre[:-4]).encode("ascii", "ignore").decode()
    seguro = re.sub(r"[^a-zA-Z0-9_-]+", "-", seguro).strip("-")[:70] or "evaluacion"
    return seguro + ".txt"


def directorio(config) -> Path:
    ruta = config.datos / "sobres"
    ruta.mkdir(mode=0o700, exist_ok=True)
    os.chmod(ruta, 0o700)
    return ruta


def ruta_sobre(config, identificador: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", identificador):
        raise FalloSobre("metadatos_invalidos")
    return directorio(config) / (identificador + ".gcm")


def escribir_atomico(ruta: Path, contenido: bytes):
    """Publica bytes completos mediante rename; fsync precede la referencia SQLite."""
    temporal = ruta.with_name("." + secrets.token_hex(16) + ".tmp")
    try:
        with os.fdopen(os.open(temporal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as archivo:
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
        if os.name == "posix":
            descriptor = os.open(ruta.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        temporal.unlink(missing_ok=True)


def privada(config, db, crear=False):
    """Nunca regenera una clave ausente si existen documentos publicados."""
    carpeta = config.datos / "secrets"
    carpeta.mkdir(mode=0o700, exist_ok=True)
    ruta = carpeta / "sobre-rsa.pem"
    if not ruta.exists():
        if not crear or db.execute("SELECT 1 FROM documentos LIMIT 1").fetchone():
            raise FalloSobre("clave_no_disponible")
        escribir_atomico(ruta, nueva_privada())
    try:
        return cargar_privada(ruta.read_bytes())
    except (ValueError, OSError):
        raise FalloSobre("clave_no_disponible") from None


def guardar_copia(config, contenido, publica, contexto):
    if sum(p.stat().st_size for p in directorio(config).iterdir() if p.is_file()) + len(contenido) + 16 > MAX_ALMACEN:
        raise FalloSobre("almacen_lleno")
    cifrado, datos = cifrar(contenido, publica, contexto)
    datos["id"] = secrets.token_hex(16)
    escribir_atomico(ruta_sobre(config, datos["id"]), cifrado)
    return datos


def recuperar(config, db, documento, copia=None, comprobar_hash=True) -> bytes:
    """Autentica y compara la referencia inmutable antes de devolver bytes al llamador."""
    try:
        datos = json.loads(documento["activo"]) if copia is None else copia
        ruta = ruta_sobre(config, datos["id"])
        if ruta.stat().st_size > MAX_ARCHIVO + 16:
            raise FalloSobre("metadatos_invalidos")
        cifrado = ruta.read_bytes()
        contenido = descifrar(cifrado, datos, privada(config, db), aad(documento["evaluacion_id"], documento["version"]))
    except InvalidTag:
        raise FalloSobre("autenticacion_gcm_fallida") from None
    except (ValueError, KeyError, TypeError):
        raise FalloSobre("sobre_invalido") from None
    except OSError:
        raise FalloSobre("archivo_no_disponible") from None
    if comprobar_hash and (not hmac.compare_digest(huella(contenido), documento["sha256"]) or len(contenido) != documento["tamano"]):
        raise FalloSobre("discrepancia_sha256")
    return contenido


def tiempo_recurso(db):
    try:
        return leer_reloj(db).isoformat()
    except ValueError:
        return None


def metadatos(documento):
    if not documento:
        return None
    return {"nombre": documento["nombre"], "tamano": documento["tamano"],
            "publicado": documento["publicado"], "version": documento["version"],
            "publicacion": fecha_hora_visual(documento["publicado"])}


def publicar_en_transaccion(config, db, evaluacion, nombre, contenido, cuenta_id):
    """Invocada con bloqueo SQLite y autorización vigente de la capa HTTP o CLI local."""
    nombre = validar_texto(nombre, contenido)
    if not db.execute("SELECT 1 FROM evaluaciones WHERE id=?", (evaluacion,)).fetchone():
        raise ValueError("Selecciona una evaluación registrada.")
    if not db.execute("SELECT 1 FROM documentos WHERE evaluacion_id=?", (evaluacion,)).fetchone() and db.execute("SELECT count(*) FROM documentos").fetchone()[0] >= 32:
        raise ValueError("Se alcanzó el límite de documentos del laboratorio.")
    version = secrets.token_hex(16)
    clave = privada(config, db, crear=True)
    copia = guardar_copia(config, contenido, clave.public_key(), aad(evaluacion, version))
    publicado = datetime.now(BOGOTA).isoformat()
    db.execute("""INSERT INTO documentos VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(evaluacion_id)
               DO UPDATE SET version=excluded.version,nombre=excluded.nombre,tamano=excluded.tamano,
               sha256=excluded.sha256,publicado=excluded.publicado,creador=excluded.creador,
               original=excluded.original,activo=excluded.activo""",
               (evaluacion, version, nombre, len(contenido), huella(contenido), publicado, cuenta_id,
                json.dumps(copia), json.dumps(copia)))
    registrar(db, "publicar_documento", "permitido", "sobre_publicado", cuenta_id, evaluacion, tiempo_recurso(db))
    return copia


def limpiar_huerfanos(config):
    """Solo elimina cifrados sin referencia, bajo el mismo bloqueo que lectores/escritores."""
    with conexion(config, True) as db:
        usados = set()
        for fila in db.execute("SELECT original,activo FROM documentos"):
            for valor in fila:
                usados.add(json.loads(valor)["id"] + ".gcm")
        for ruta in directorio(config).glob("*.gcm"):
            if ruta.name not in usados:
                ruta.unlink()


def operacion_local(config, evaluacion, accion):
    """Alteraciones exclusivas de terminal. La referencia SHA nunca se reescribe."""
    with conexion(config, True) as db:
        if accion == "preparar":
            publicar_en_transaccion(config, db, evaluacion, "evaluacion-prueba.txt", TEXTO_PRUEBA, None)
        else:
            documento = db.execute("SELECT * FROM documentos WHERE evaluacion_id=?", (evaluacion,)).fetchone()
            if not documento:
                raise ValueError("Publica primero un documento.")
            original = json.loads(documento["original"])
            if accion == "restaurar":
                recuperar(config, db, documento, original)
                copia = original
            else:
                contenido = recuperar(config, db, documento, original)
                clave = privada(config, db)
                if accion == "alterar-hash":
                    # Mantiene texto UTF-8 válido incluso si el original empieza por BOM o acentos.
                    letras = list(contenido.decode("utf-8"))
                    indice = next((i for i, c in enumerate(letras) if c.isalpha()),
                                  next(i for i, c in enumerate(letras) if not c.isspace() and c != '\ufeff'))
                    letras[indice] = "X" if letras[indice] != "X" else "Y"
                    contenido = "".join(letras).encode("utf-8")
                copia = guardar_copia(config, contenido, clave.public_key(), aad(evaluacion, documento["version"]))
                if accion == "alterar-gcm":
                    ruta = ruta_sobre(config, copia["id"])
                    datos = ruta.read_bytes()
                    escribir_atomico(ruta, bytes([datos[0] ^ 1]) + datos[1:])
            db.execute("UPDATE documentos SET activo=? WHERE evaluacion_id=?", (json.dumps(copia), evaluacion))
            registrar(db, "laboratorio_sobre", "permitido", accion.replace("-", "_"), None, evaluacion, tiempo_recurso(db))
    limpiar_huerfanos(config)


def estado_sobre(config, evaluacion):
    """Expone huellas/algoritmos al operador local, nunca claves o contenido original."""
    with conexion(config) as db:
        fila = db.execute("SELECT * FROM documentos WHERE evaluacion_id=?", (evaluacion,)).fetchone()
        if not fila:
            raise ValueError("No hay documento publicado.")
        resultado = {**metadatos(fila), "sha256_original": fila["sha256"],
                     "algoritmos": "AES-256-GCM / RSA-3072-OAEP-SHA256", "nonce_bits": 96,
                     "almacen": "/data/sobres (privado)", "referencia_conservada": fila["original"] == fila["activo"]}
        try:
            contenido = recuperar(config, db, fila, comprobar_hash=False)
            resultado.update(autenticacion_gcm="correcta", sha256_recuperado=huella(contenido),
                             integridad=huella(contenido) == fila["sha256"])
        except FalloSobre as fallo:
            resultado.update(autenticacion_gcm="no_superada", motivo=fallo.motivo)
        return resultado


def bitacora_documentos(config):
    """Resumen docente acotado; selecciona campos, nunca cuerpos o secretos."""
    with conexion(config) as db:
        return [dict(fila) for fila in db.execute("""SELECT accion,resultado,motivo,evaluacion_id,
                   datetime(instante,'unixepoch','-5 hours') AS hora_real, instante_didactico
                   FROM eventos WHERE accion IN ('publicar_documento','descargar_documento','verificar_integridad','laboratorio_sobre')
                   ORDER BY id DESC LIMIT 12""")]
