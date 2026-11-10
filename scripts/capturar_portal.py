"""Captura segura del portal real en 8443, sin credenciales ni contenido privado."""

import argparse
import json
import subprocess
import time
import urllib.request
import ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".qa" / "red"
PCAP = OUT / "portal-8443.pcapng"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--esperar-disponibilidad", action="store_true", help="espera una consulta manual autenticada")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    filtro = "host 127.0.0.1 and tcp port 8443"
    dumpcap = Path(r"C:\Program Files\Wireshark\dumpcap.exe")
    if not dumpcap.is_file():
        raise FileNotFoundError(f"No se encontró dumpcap: {dumpcap}")
    captura = subprocess.Popen([str(dumpcap), "-i", r"\Device\NPF_Loopback", "-f", filtro, "-w", str(PCAP)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    if captura.poll() is not None:
        error = captura.stderr.read()
        raise RuntimeError(f"dumpcap no pudo iniciar la captura: {error.strip()}")
    contexto = ssl.create_default_context(cafile=str(ROOT / "certs" / "ca" / "ca.crt"))
    respuestas = []
    for ruta in ("/health", "/acceso"):
        try:
            with urllib.request.urlopen(f"https://127.0.0.1:8443{ruta}", context=contexto, timeout=5) as respuesta:
                respuestas.append({"ruta": ruta, "estado": respuesta.status})
        except Exception as exc:
            respuestas.append({"ruta": ruta, "error": type(exc).__name__})
    if args.esperar_disponibilidad:
        input("Captura activa. Inicie sesión en el portal y pulse «Comprobar acceso»; después presione Enter aquí.\n")
    else:
        time.sleep(2)
    captura.terminate()
    captura.wait(timeout=10)
    if len(respuestas) != 2 or any(respuesta.get("estado") != 200 for respuesta in respuestas):
        raise RuntimeError(f"No se pudieron verificar las rutas públicas del portal: {respuestas}")
    tshark = dumpcap.with_name("tshark.exe")
    verificacion = subprocess.run([str(tshark), "-r", str(PCAP), "-Y", "tcp.port == 8443 && tls", "-T", "fields", "-e", "tls.record.version", "-e", "tls.record.opaque_type"], capture_output=True, text=True, check=True)
    registros_tls = [linea for linea in verificacion.stdout.splitlines() if linea.strip()]
    if not registros_tls:
        raise RuntimeError("La captura no contiene registros TLS del puerto 8443.")
    resultado = {"filtro": filtro, "puerto": 8443, "respuestas_publicas": respuestas, "consulta_disponibilidad_manual": args.esperar_disponibilidad, "registros_tls": len(registros_tls), "pcap": str(PCAP)}
    (OUT / "portal-8443-resultados.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
