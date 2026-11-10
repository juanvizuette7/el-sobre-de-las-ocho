"""Administración local de metadatos y reloj de ensayo, sin endpoints privilegiados."""

import argparse
import json
import sqlite3
from datetime import date, datetime, time

from app.audit import registrar
from app.clock import BOGOTA, ahora_real, cambiar_reloj, interpretar_instante, leer_reloj
from app.config import configuracion_entorno
from app.db import conexion, inicializar_base
from app.storage import FalloSobre

ID_EVALUACION = "evaluacion-001"


def preparar_ensayo(config, fecha: date):
    """Prepara un único caso a las 08:00 y lo deja cerrado a las 07:59:59."""
    apertura = datetime.combine(fecha, time(8), BOGOTA)
    inicio = datetime.combine(fecha, time(7, 59, 59), BOGOTA)
    with conexion(config, escritura=True) as db:
        estudiante = db.execute(
            "SELECT id FROM cuentas WHERE nombre='estudiante' AND rol='ESTUDIANTE' AND activa=1",
        ).fetchone()
        if not estudiante:
            raise ValueError("Inicialice primero la cuenta estudiante mediante app.manage; no se crearon cuentas.")
        db.execute(
            """INSERT INTO evaluaciones VALUES(?,?,?) ON CONFLICT(id)
               DO UPDATE SET titulo=excluded.titulo, apertura=excluded.apertura""",
            (ID_EVALUACION, "Evaluación de laboratorio", apertura.isoformat()),
        )
        # Solo este caso de ensayo: no borra evaluaciones, identidad, sesiones o bitácora.
        db.execute("DELETE FROM asignaciones WHERE evaluacion_id=?", (ID_EVALUACION,))
        db.execute("INSERT INTO asignaciones VALUES(?,?)", (ID_EVALUACION, estudiante[0]))
        instante = cambiar_reloj(db, inicio)
        registrar(db, "administracion_local", "permitido", "ensayo_preparado",
                  evaluacion_id=ID_EVALUACION, instante_didactico=instante.isoformat())


def estado_reloj(config) -> dict:
    """Identifica el tiempo real y el de decisión sin incluir información de sesión."""
    with conexion(config) as db:
        instante = leer_reloj(db)
        fijo = db.execute("SELECT instante_fijo FROM reloj_evaluaciones WHERE id=1").fetchone()[0]
    return {"modo": "fijo" if fijo is not None else "normal", "zona_horaria": "America/Bogota",
            "tiempo_didactico": instante.isoformat(), "tiempo_real": ahora_real().isoformat()}


def cambiar_asignacion(config, estudiante: str, asignar: bool):
    """Modifica solo la asignación del caso local; no crea cuentas o recursos web."""
    with conexion(config, escritura=True) as db:
        cuenta = db.execute("SELECT id FROM cuentas WHERE nombre=? AND rol='ESTUDIANTE' AND activa=1",
                            (estudiante.strip().lower(),)).fetchone()
        evaluacion = db.execute("SELECT id FROM evaluaciones WHERE id=?", (ID_EVALUACION,)).fetchone()
        if not cuenta or not evaluacion:
            raise ValueError("Se requiere evaluación preparada y estudiante activo.")
        if asignar:
            db.execute("INSERT OR IGNORE INTO asignaciones VALUES(?,?)", (ID_EVALUACION, cuenta[0]))
        else:
            db.execute("DELETE FROM asignaciones WHERE evaluacion_id=? AND cuenta_id=?", (ID_EVALUACION, cuenta[0]))
        registrar(db, "administracion_local", "permitido", "asignacion_otorgada" if asignar else "asignacion_retirada",
                  evaluacion_id=ID_EVALUACION, instante_didactico=leer_reloj(db).isoformat())


def consultar_auditoria(config, limite: int = 20) -> list[dict]:
    """Exporta solo decisiones de disponibilidad, con tiempos y campos explícitos."""
    if not 1 <= limite <= 100:
        raise ValueError("El límite debe estar entre 1 y 100.")
    with conexion(config) as db:
        filas = db.execute(
            """SELECT instante,cuenta_id,accion,evaluacion_id,resultado,motivo,instante_didactico
               FROM eventos WHERE accion='consultar_disponibilidad' ORDER BY id DESC LIMIT ?""",
            (limite,),
        ).fetchall()
    return [{"tiempo_real": datetime.fromtimestamp(f["instante"], BOGOTA).isoformat(),
             "usuario_id": f["cuenta_id"], "accion": f["accion"],
             "evaluacion_id": f["evaluacion_id"], "decision": f["resultado"],
             "motivo": f["motivo"], "tiempo_didactico": f["instante_didactico"]} for f in filas]


def principal():
    """El acceso al contenedor es la frontera administrativa de estos comandos."""
    parser = argparse.ArgumentParser(description="Reloj y evaluación de ensayo local")
    acciones = parser.add_subparsers(dest="accion", required=True)
    preparar = acciones.add_parser("preparar", help="Restablece el caso cerrado y su asignación")
    preparar.add_argument("--fecha", required=True, help="Fecha de ensayo AAAA-MM-DD")
    asignacion = acciones.add_parser("asignacion", help="Asigna o retira el caso local a un estudiante existente")
    asignacion.add_argument("cambio", choices=["asignar", "retirar"])
    asignacion.add_argument("--estudiante", default="estudiante")
    auditoria = acciones.add_parser("auditoria", help="Consulta decisiones de disponibilidad sin datos sensibles")
    auditoria.add_argument("--limite", type=int, default=20)
    reloj = acciones.add_parser("reloj", help="Consulta o cambia únicamente el reloj de disponibilidad")
    sobre = acciones.add_parser("sobre", help="Operaciones criptográficas exclusivamente locales")
    sobre.add_argument("operacion", choices=["preparar", "estado", "alterar-gcm", "alterar-hash", "restaurar", "auditoria"])
    sobre.add_argument("--evaluacion", default=ID_EVALUACION)
    modos = reloj.add_subparsers(dest="modo", required=True)
    modos.add_parser("estado")
    fijar = modos.add_parser("fijar")
    fijar.add_argument("instante", help="AAAA-MM-DDTHH:MM:SS, hora Bogotá si no incluye offset")
    modos.add_parser("normal")
    argumentos = parser.parse_args()
    config = configuracion_entorno()
    inicializar_base(config)
    try:
        if argumentos.accion == "sobre":
            from app.storage import operacion_local, estado_sobre
            if argumentos.operacion == "auditoria":
                with conexion(config) as db:
                    filas = db.execute("""SELECT instante,cuenta_id,accion,resultado,motivo,evaluacion_id,instante_didactico
                                          FROM eventos WHERE accion IN ('publicar_documento','descargar_documento','verificar_integridad','laboratorio_sobre')
                                          ORDER BY id DESC LIMIT 30""").fetchall()
                print(json.dumps([dict(fila) for fila in filas], ensure_ascii=False, indent=2))
            else:
                if argumentos.operacion != "estado":
                    operacion_local(config, argumentos.evaluacion, argumentos.operacion)
                print(json.dumps(estado_sobre(config, argumentos.evaluacion), ensure_ascii=False, indent=2))
            return
        if argumentos.accion == "auditoria":
            print(json.dumps(consultar_auditoria(config, argumentos.limite), ensure_ascii=False, indent=2))
            return
        if argumentos.accion == "preparar":
            preparar_ensayo(config, date.fromisoformat(argumentos.fecha))
        elif argumentos.accion == "asignacion":
            cambiar_asignacion(config, argumentos.estudiante, argumentos.cambio == "asignar")
        elif argumentos.modo != "estado":
            instante = interpretar_instante(argumentos.instante) if argumentos.modo == "fijar" else None
            with conexion(config, escritura=True) as db:
                decision = cambiar_reloj(db, instante)
                registrar(db, "administracion_local", "permitido",
                          "reloj_fijado" if instante else "reloj_normal",
                          instante_didactico=decision.isoformat())
        print(json.dumps(estado_reloj(config), ensure_ascii=False, indent=2))
    except (ValueError, sqlite3.Error, OSError, FalloSobre):
        parser.exit(1, "No se pudo configurar el ensayo. Verifique fecha/hora, almacenamiento y cuenta estudiante activa.\n")


if __name__ == "__main__":
    principal()
