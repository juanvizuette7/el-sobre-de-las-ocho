"""Sobre híbrido: AES-256-GCM, RSA-OAEP/SHA-256 y huella del original."""

import hashlib
import json
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def nueva_privada() -> bytes:
    """Genera RSA-3072; el almacenamiento privado protege su representación PKCS8."""
    clave = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    return clave.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                               serialization.NoEncryption())


def cargar_privada(pem: bytes):
    clave = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(clave, rsa.RSAPrivateKey) or clave.key_size < 3072:
        raise ValueError("Clave no válida")
    return clave


def oaep():
    return padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


def aad(evaluacion: str, version: str) -> bytes:
    """Vincula formato, evaluación y versión; no admite intercambiar sobres."""
    return json.dumps(["sobre-v1", evaluacion, version], separators=(",", ":")).encode("utf-8")


def cifrar(contenido: bytes, publica, contexto: bytes) -> tuple[bytes, dict]:
    """Cada operación crea otra clave AES y nonce; incluye tag GCM de 128 bits."""
    clave = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    cifrado = AESGCM(clave).encrypt(nonce, contenido, contexto)
    envuelta = publica.encrypt(clave, oaep())
    return cifrado, {"nonce": nonce.hex(), "clave_envuelta": envuelta.hex()}


def descifrar(cifrado: bytes, metadatos: dict, privada, contexto: bytes) -> bytes:
    """No devuelve contenido hasta autenticar la totalidad del sobre."""
    clave = privada.decrypt(bytes.fromhex(metadatos["clave_envuelta"]), oaep())
    if len(clave) != 32 or len(bytes.fromhex(metadatos["nonce"])) != 12:
        raise ValueError("Parámetros no válidos")
    return AESGCM(clave).decrypt(bytes.fromhex(metadatos["nonce"]), cifrado, contexto)


def huella(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()
