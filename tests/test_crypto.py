"""Pruebas reales de primitivas: claves independientes, OAEP, AAD y autenticación."""

import pytest
from cryptography.exceptions import InvalidTag

from app.crypto import aad, cargar_privada, cifrar, descifrar, huella, nueva_privada, oaep


@pytest.fixture(scope="module")
def privada():
    return cargar_privada(nueva_privada())


def test_cifrado_hibrido_original_y_claves_distintas(privada):
    original = b"Examen ficticio con marca unica de prueba"
    contexto = aad("evaluacion-001", "v1")
    a, ma = cifrar(original, privada.public_key(), contexto)
    b, mb = cifrar(original, privada.public_key(), contexto)
    assert original not in a and a != b
    ka = privada.decrypt(bytes.fromhex(ma["clave_envuelta"]), oaep())
    kb = privada.decrypt(bytes.fromhex(mb["clave_envuelta"]), oaep())
    assert len(ka) == len(kb) == 32 and ka != kb
    assert len(bytes.fromhex(ma["nonce"])) == 12
    assert len(a) == len(original) + 16
    assert descifrar(a, ma, privada, contexto) == original
    assert huella(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.parametrize("posicion", [0, -1])
def test_cifrado_o_tag_danados(privada, posicion):
    datos, meta = cifrar(b"Texto original", privada.public_key(), aad("e", "v"))
    copia = bytearray(datos)
    copia[posicion] ^= 1
    with pytest.raises(InvalidTag):
        descifrar(bytes(copia), meta, privada, aad("e", "v"))


@pytest.mark.parametrize("contexto", [aad("otra", "v"), aad("e", "otra")])
def test_aad_impide_intercambio_de_evaluacion_o_version(privada, contexto):
    datos, meta = cifrar(b"Original", privada.public_key(), aad("e", "v"))
    with pytest.raises(InvalidTag):
        descifrar(datos, meta, privada, contexto)


def test_otra_privada_no_recupera_aes(privada):
    datos, meta = cifrar(b"Original", privada.public_key(), aad("e", "v"))
    with pytest.raises(ValueError):
        descifrar(datos, meta, cargar_privada(nueva_privada()), aad("e", "v"))
