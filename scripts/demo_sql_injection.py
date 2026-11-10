"""Comparación educativa aislada; nunca conecta con la base del portal."""

import sqlite3


ENTRADA = "' OR '1'='1' --"


def demostrar(entrada: str = ENTRADA) -> dict[str, list[str]]:
    """Compara concatenación vulnerable y parámetros sobre datos efímeros."""
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE cuentas_demo(usuario TEXT NOT NULL)")
        db.executemany(
            "INSERT INTO cuentas_demo(usuario) VALUES(?)",
            [("docente_demo",), ("estudiante_demo",)],
        )

        # Vulnerabilidad intencional confinada a SQLite en memoria con datos ficticios.
        consulta_insegura = "SELECT usuario FROM cuentas_demo WHERE usuario='" + entrada + "'"
        insegura = [fila[0] for fila in db.execute(consulta_insegura)]

        consulta_segura = "SELECT usuario FROM cuentas_demo WHERE usuario=?"
        segura = [fila[0] for fila in db.execute(consulta_segura, (entrada,))]
        return {"consulta_insegura": insegura, "consulta_parametrizada": segura}


if __name__ == "__main__":
    resultado = demostrar()
    print(f"Entrada ficticia: {ENTRADA}")
    print(f"Consulta concatenada (vulnerable): {resultado['consulta_insegura']}")
    print(f"Consulta parametrizada: {resultado['consulta_parametrizada']}")
