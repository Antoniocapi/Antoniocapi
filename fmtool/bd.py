"""Base de datos SQLite: guarda cada CSV importado con su fecha de juego."""

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from .datos import fecha, leer_csv, mapa_columnas, normalizar

# Nombre de archivo esperado:  <grupo>_<vista>_<AAAA-MM-DD>.csv
#   plantilla: primer-equipo_informacion-general_2028-09-18.csv
#   ojeo:      laterales-izquierdos_2029-01-02.csv  (la vista es opcional)
PATRON = re.compile(r"^(?P<grupo>[^_]+)(?:_(?P<vista>.+?))?_(?P<fecha>\d{4}-\d{2}-\d{2})\.csv$", re.I)

TIPOS = ("plantilla", "ojeo")


def conectar(ruta):
    conn = sqlite3.connect(ruta)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS importaciones (
            id INTEGER PRIMARY KEY,
            archivo TEXT UNIQUE,
            huella TEXT,
            tipo TEXT,           -- plantilla | ojeo
            grupo TEXT,          -- primer-equipo | filial | juvenil | nombre del foco de ojeo
            vista TEXT,
            fecha_juego TEXT,    -- AAAA-MM-DD
            columnas TEXT,       -- JSON con los títulos de columna
            importado_en TEXT
        );
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY,
            importacion_id INTEGER REFERENCES importaciones(id) ON DELETE CASCADE,
            jugador TEXT,
            datos TEXT           -- JSON con la fila tal cual está en el CSV
        );
        CREATE INDEX IF NOT EXISTS idx_reg_jugador ON registros(jugador);
        """
    )
    return conn


def importar(conn, carpeta_data):
    """Importa los CSV nuevos o modificados de data/plantilla y data/ojeo.
    Devuelve una lista de mensajes para mostrar."""
    mensajes = []
    for tipo in TIPOS:
        for ruta in sorted(Path(carpeta_data, tipo).glob("*.csv")):
            m = PATRON.match(ruta.name)
            if not m:
                mensajes.append(f"AVISO: '{ruta.name}' no sigue el formato grupo_vista_AAAA-MM-DD.csv; lo salto.")
                continue
            huella = hashlib.sha1(ruta.read_bytes()).hexdigest()
            previa = conn.execute("SELECT id, huella FROM importaciones WHERE archivo=?", (str(ruta),)).fetchone()
            if previa and previa["huella"] == huella:
                continue  # ya importado y sin cambios
            if previa:
                conn.execute("DELETE FROM registros WHERE importacion_id=?", (previa["id"],))
                conn.execute("DELETE FROM importaciones WHERE id=?", (previa["id"],))
            columnas, filas = leer_csv(ruta)
            cur = conn.execute(
                "INSERT INTO importaciones (archivo, huella, tipo, grupo, vista, fecha_juego, columnas, importado_en)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (str(ruta), huella, tipo, m["grupo"].lower(), (m["vista"] or "").lower(), m["fecha"],
                 json.dumps(columnas, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")),
            )
            mapa = mapa_columnas(columnas)
            col_jugador = mapa.get("jugador")
            if not col_jugador:
                mensajes.append(f"AVISO: '{ruta.name}' no tiene columna 'Jugador'.")
            for fila in filas:
                nombre = (fila.get(col_jugador) or "").strip() if col_jugador else ""
                conn.execute("INSERT INTO registros (importacion_id, jugador, datos) VALUES (?,?,?)",
                             (cur.lastrowid, nombre, json.dumps(fila, ensure_ascii=False)))
            mensajes.append(f"Importado {ruta.name}: {len(filas)} filas ({tipo}, {m['grupo']}, {m['fecha']}).")
    conn.commit()
    return mensajes


def _cargar(conn, sql, params, alias_extra):
    """Ejecuta la consulta y convierte cada fila en un jugador normalizado."""
    jugadores = []
    cache_mapas = {}
    for r in conn.execute(sql, params):
        if r["importacion_id"] not in cache_mapas:
            cache_mapas[r["importacion_id"]] = mapa_columnas(json.loads(r["columnas"]), alias_extra)
        j = normalizar(json.loads(r["datos"]), cache_mapas[r["importacion_id"]])
        j.update(grupo=r["grupo"], vista=r["vista"], fecha_juego=fecha(r["fecha_juego"]), archivo=r["archivo"])
        jugadores.append(j)
    return jugadores


_SQL = ("SELECT r.datos, r.importacion_id, i.grupo, i.vista, i.fecha_juego, i.columnas, i.archivo "
        "FROM registros r JOIN importaciones i ON i.id = r.importacion_id ")


def _fusionar(filas):
    """Une las filas del mismo jugador (vistas distintas del mismo día): gana el dato no vacío."""
    por_jugador = {}
    for j in filas:
        clave = (j["grupo"], j["jugador"])
        if clave not in por_jugador:
            por_jugador[clave] = j
            continue
        base = por_jugador[clave]
        for k, v in j.items():
            if k == "columnas":
                base["columnas"] = base["columnas"] | v
            elif k == "raw":
                base["raw"] = {**v, **{a: b for a, b in base["raw"].items() if b}}
            elif base.get(k) in (None, "") and v not in (None, ""):
                base[k] = v
    return list(por_jugador.values())


def estado_actual(conn, tipo, alias_extra=None):
    """Último estado conocido de cada grupo.

    - Los jugadores son los de la fecha más reciente del grupo (así desaparecen los que se fueron).
    - Cada dato sale de la vista más reciente que lo tenga: si el 17/12 solo hay estadísticas,
      las estrellas y el contrato siguen viniendo de la vista general anterior.
    """
    ultimas = conn.execute(
        "SELECT grupo, MAX(fecha_juego) AS f FROM importaciones WHERE tipo=? GROUP BY grupo", (tipo,)
    ).fetchall()
    filas = []
    for u in ultimas:
        recientes = _cargar(conn, _SQL + "WHERE i.tipo=? AND i.grupo=? AND i.fecha_juego=? ORDER BY r.id",
                            (tipo, u["grupo"], u["f"]), alias_extra)
        plantilla = {j["jugador"] for j in recientes}
        # Para cada vista, su importación más reciente (de la más nueva a la más vieja: la nueva manda)
        vistas = conn.execute(
            "SELECT vista, MAX(fecha_juego) AS f FROM importaciones WHERE tipo=? AND grupo=? GROUP BY vista ORDER BY f DESC",
            (tipo, u["grupo"])).fetchall()
        for v in vistas:
            for j in _cargar(conn, _SQL + "WHERE i.tipo=? AND i.grupo=? AND i.vista=? AND i.fecha_juego=? ORDER BY r.id",
                             (tipo, u["grupo"], v["vista"], v["f"]), alias_extra):
                if j["jugador"] in plantilla:
                    filas.append(j)
    fusion = _fusionar(filas)
    # Huecos (p. ej. un canterano que sube y cuyo contrato solo sale en la vista del B):
    # se rellenan con su dato más reciente en cualquier equipo
    todos = _cargar(conn, _SQL + "WHERE i.tipo=? ORDER BY i.fecha_juego DESC, r.id", (tipo,), alias_extra)
    for j in fusion:
        for o in todos:
            if o["jugador"] != j["jugador"]:
                continue
            for k, v in o.items():
                if k in ("grupo", "vista", "fecha_juego", "archivo", "raw", "columnas"):
                    continue
                if j.get(k) in (None, "") and v not in (None, ""):
                    j[k] = v
    # La fecha de cada jugador es la más reciente de su grupo
    fecha_grupo = {u["grupo"]: u["f"] for u in ultimas}
    from .datos import fecha as _f
    for j in fusion:
        j["fecha_juego"] = _f(fecha_grupo[j["grupo"]])
    return fusion


def historial(conn, alias_extra=None, jugador=None):
    """Todas las capturas de plantilla (o las de un jugador), ordenadas por fecha."""
    sql = _SQL + "WHERE i.tipo='plantilla' "
    params = ()
    if jugador:
        sql += "AND r.jugador = ? "
        params = (jugador,)
    filas = _cargar(conn, sql + "ORDER BY i.fecha_juego, r.id", params, alias_extra)
    # una fila por jugador, grupo y fecha
    por_fecha = {}
    for j in filas:
        por_fecha.setdefault(j["fecha_juego"], []).append(j)
    resultado = []
    for f in sorted(por_fecha):
        resultado += _fusionar(por_fecha[f])
    return resultado


def resumen_importaciones(conn):
    return conn.execute(
        "SELECT i.tipo, i.grupo, i.vista, i.fecha_juego, i.columnas, i.archivo, COUNT(r.id) AS filas "
        "FROM importaciones i LEFT JOIN registros r ON r.importacion_id = i.id "
        "GROUP BY i.id ORDER BY i.tipo, i.grupo, i.fecha_juego"
    ).fetchall()
