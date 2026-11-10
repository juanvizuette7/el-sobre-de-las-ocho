"""CA privada de desarrollo y certificados locales; nunca instala confianza en Windows."""

import argparse
import ipaddress
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def guardar(ruta, datos, privado=False):
    ruta.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with os.fdopen(os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if privado else 0o644), "wb") as archivo:
        archivo.write(datos)
        archivo.flush()
        os.fsync(archivo.fileno())


def clave_pem(clave):
    return clave.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                               serialization.NoEncryption())


def emitir(nombre, clave, emisor, firmante, ca=False):
    ahora = datetime.now(timezone.utc)
    identidad = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nombre)])
    constructor = (x509.CertificateBuilder().subject_name(identidad).issuer_name(emisor or identidad)
                   .public_key(clave.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(ahora - timedelta(minutes=5))
                   .not_valid_after(ahora + timedelta(days=3650 if ca else 180))
                   .add_extension(x509.BasicConstraints(ca=ca, path_length=0 if ca else None), critical=True)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(clave.public_key()), critical=False)
                   .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                       key_encipherment=not ca, data_encipherment=False, key_agreement=False,
                       key_cert_sign=ca, crl_sign=ca, encipher_only=False, decipher_only=False), critical=True))
    if not ca:
        constructor = (constructor.add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(firmante.public_key()), critical=False))
    return constructor.sign(firmante or clave, hashes.SHA256())


def comprobar(directorio):
    """Comprueba cadena, SAN, vigencia y pareja privada sin imprimir ninguna clave."""
    ca = x509.load_pem_x509_certificate((directorio / "ca/ca.crt").read_bytes())
    ahora = datetime.now(timezone.utc)
    if not ca.extensions.get_extension_for_class(x509.BasicConstraints).value.ca:
        raise ValueError("La CA no es válida")
    ca.verify_directly_issued_by(ca)
    for nombre in ("nginx", "lab"):
        cert = x509.load_pem_x509_certificate((directorio / nombre / "server.crt").read_bytes())
        clave = serialization.load_pem_private_key((directorio / nombre / "server.key").read_bytes(), None)
        cert.verify_directly_issued_by(ca)
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        if (ipaddress.ip_address("127.0.0.1") not in san.get_values_for_type(x509.IPAddress)
                or "localhost" not in san.get_values_for_type(x509.DNSName)
                or not cert.not_valid_before_utc <= ahora < cert.not_valid_after_utc
                or cert.public_key().public_numbers() != clave.public_key().public_numbers()):
            raise ValueError("Certificado o clave no válidos")
    if not ca.not_valid_before_utc <= ahora < ca.not_valid_after_utc:
        raise ValueError("CA fuera de vigencia")
    return {"ca": ca.subject.rfc4514_string(), "sha256_ca": ca.fingerprint(hashes.SHA256()).hex(),
            "san": ["127.0.0.1", "localhost"], "confianza_windows": "Instalación explícita del usuario requerida"}


def generar(directorio: Path):
    """Conserva un juego existente válido; una instalación parcial nunca se sobrescribe."""
    rutas = [directorio / "ca/ca.key", directorio / "ca/ca.crt"]
    rutas += [directorio / nombre / archivo for nombre in ("nginx", "lab") for archivo in ("server.key", "server.crt")]
    if any(p.exists() for p in rutas):
        if not all(p.is_file() for p in rutas):
            raise ValueError("Instalación de certificados incompleta; restaure una copia privada, no se sobrescribió nada")
        return comprobar(directorio)
    ca_clave = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca = emitir("El Sobre - CA local de laboratorio", ca_clave, None, None, ca=True)
    guardar(directorio / "ca/ca.key", clave_pem(ca_clave), privado=True)
    guardar(directorio / "ca/ca.crt", ca.public_bytes(serialization.Encoding.PEM))
    for nombre in ("nginx", "lab"):
        clave = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        cert = emitir("El Sobre - " + nombre, clave, ca.subject, ca_clave)
        guardar(directorio / nombre / "server.key", clave_pem(clave), privado=True)
        guardar(directorio / nombre / "server.crt", cert.public_bytes(serialization.Encoding.PEM))
    return comprobar(directorio)


def principal():
    parser = argparse.ArgumentParser(description="Certificados locales del sobre; no modifica confianza del sistema")
    parser.add_argument("accion", choices=["generar", "comprobar"])
    parser.add_argument("--directorio", type=Path, default=Path("/certificados"))
    args = parser.parse_args()
    try:
        datos = generar(args.directorio) if args.accion == "generar" else comprobar(args.directorio)
        if args.accion == "generar" and hasattr(os, "geteuid") and os.geteuid() == 0:
            # Cada servicio no privilegiado recibe solo su pareja TLS, nunca la privada de CA.
            for nombre, usuario in (("nginx", 101), ("lab", 10001)):
                os.chown(args.directorio / nombre, usuario, usuario)
                os.chmod(args.directorio / nombre, 0o700)
                for archivo in ("server.crt", "server.key"):
                    ruta = args.directorio / nombre / archivo
                    os.chown(ruta, usuario, usuario)
                    os.chmod(ruta, 0o600 if archivo.endswith("key") else 0o644)
        print(json.dumps(datos, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError):
        parser.exit(1, "Certificados ausentes, incompletos, incompatibles o no válidos. No se regeneraron claves existentes.\n")


if __name__ == "__main__":
    principal()
