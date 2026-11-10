"""Configuración local y parámetros de seguridad de identidad."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Configuracion:
    datos: Path
    origen: str = "http://127.0.0.1:8080"
    duracion_sesion: int = 1800
    duracion_previa: int = 600
    duracion_mfa: int = 300
    ventana_intentos: int = 300
    limite_intentos: int = 5

    def __post_init__(self):
        """Rechaza orígenes públicos o ambiguos para este laboratorio local."""
        url = urlsplit(self.origen)
        if (url.scheme not in {"http", "https"} or url.hostname not in {"127.0.0.1", "localhost"}
                or url.path or url.query or url.fragment or url.username):
            raise ValueError("PORTAL_ORIGIN debe ser un origen local HTTP/HTTPS sin ruta.")

    @property
    def cookie_secure(self) -> bool:
        return self.origen.startswith("https://")

    @property
    def base_datos(self) -> Path:
        return self.datos / "portal.sqlite3"


def configuracion_entorno() -> Configuracion:
    """No requiere credenciales en variables de entorno ni valores secretos por defecto."""
    return Configuracion(
        datos=Path(os.environ.get("PORTAL_DATA_DIR", "/data")),
        origen=os.environ.get("PORTAL_ORIGIN", "http://127.0.0.1:8080"),
    )
