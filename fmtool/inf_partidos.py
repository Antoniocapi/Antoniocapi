"""Seguimiento de partidos a partir de data/partidos/partidos.csv (lo rellenas tú)."""

import math
import re
from pathlib import Path

from .datos import fecha, leer_csv, mapa_columnas, numero, _clave
from .salida import Informe

# Columnas de la plantilla de partidos (y nombres alternativos aceptados)
COLUMNAS = {
    "fecha": ["Fecha"],
    "jornada": ["Jornada"],
    "competicion": ["Competición"],
    "rival": ["Rival"],
    "pos_rival": ["Posición rival"],
    "campo": ["Local/Visitante", "Campo"],
    "resultado": ["Resultado"],
    "xg_favor": ["xG a favor"],
    "xg_contra": ["xG en contra"],
    "oc_favor": ["Ocasiones claras a favor", "Ocasiones claras"],
    "oc_contra": ["Ocasiones claras en contra"],
    "posesion": ["Posesión"],
    "prpad": ["PRPAD"],
    "faltas": ["Faltas"],
    "amarillas": ["Amarillas"],
    "mentalidad": ["Mentalidad"],
}


def leer_partidos(ruta):
    columnas, filas = leer_csv(ruta)
    por_clave = {_clave(c): c for c in columnas}
    mapa = {k: next((por_clave[_clave(n)] for n in ns if _clave(n) in por_clave), None) for k, ns in COLUMNAS.items()}
    partidos, errores = [], []
    for i, f in enumerate(filas, 2):
        def v(k):
            return f.get(mapa[k]) if mapa[k] else None
        m = re.match(r"\s*(\d+)\s*[-–:]\s*(\d+)", v("resultado") or "")
        if not m:
            errores.append(f"Fila {i}: resultado «{v('resultado')}» no válido (usa 2-1, tus goles primero).")
            continue
        campo = _clave(v("campo") or "")
        p = {
            "fecha": fecha(v("fecha")), "jornada": numero(v("jornada")), "competicion": (v("competicion") or "").strip(),
            "rival": (v("rival") or "").strip(), "pos_rival": numero(v("pos_rival")),
            # Local / Casa = True, Visitante / Fuera = False, vacío = no se sabe
            "local": None if not campo else campo.startswith(("l", "c")),
            "gf": int(m[1]), "gc": int(m[2]),
            "mentalidad": (v("mentalidad") or "").strip() or "(sin indicar)",
        }
        for k in ("xg_favor", "xg_contra", "oc_favor", "oc_contra", "posesion", "prpad", "faltas", "amarillas"):
            p[k] = numero(v(k))
        partidos.append(p)
    faltan = [COLUMNAS[k][0] for k, c in mapa.items() if c is None]
    return partidos, errores, faltan


def _equipo(nombre):
    """Clave para comparar nombres de equipo ('R.C. Alcobe...' ~ 'R.C. Alcobendas')."""
    return re.sub(r"[^a-z0-9 ]", "", _clave(nombre).replace("...", "")).strip()


def _ultimo(carpeta, prefijo):
    """El CSV más reciente de data/liga con ese prefijo (p. ej. clasificacion_AAAA-MM-DD.csv)."""
    archivos = sorted(Path(carpeta).glob(f"{prefijo}_*.csv"))
    return archivos[-1] if archivos else None


def cargar_clasificacion(carpeta):
    """Devuelve (fecha, {clave_equipo: posición}) de la última clasificación guardada."""
    ruta = _ultimo(carpeta, "clasificacion")
    if not ruta:
        return None, {}
    _, filas = leer_csv(ruta)
    tabla = {_equipo(f.get("Equipo", "")): numero(f.get("Pos")) for f in filas}
    return fecha(ruta.stem.split("_")[-1]), tabla


def buscar_posicion(tabla, rival):
    clave = _equipo(rival)
    if clave in tabla:
        return tabla[clave]
    for k, v in tabla.items():  # nombre cortado o abreviado
        if k.startswith(clave) or clave.startswith(k):
            return v
    return None


def _poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def puntos_esperados(xgf, xgc):
    """Puntos esperados (xPts) con un modelo de Poisson sencillo."""
    if xgf is None or xgc is None:
        return None
    pg = pe = 0.0
    for a in range(11):
        for b in range(11):
            pr = _poisson(a, xgf) * _poisson(b, xgc)
            if a > b:
                pg += pr
            elif a == b:
                pe += pr
    return 3 * pg + pe


def _media(valores):
    v = [x for x in valores if x is not None]
    return round(sum(v) / len(v), 2) if v else None


def resumen(partidos, nombre):
    """Una fila de tabla con los números de un grupo de partidos."""
    if not partidos:
        return None
    g = sum(p["gf"] > p["gc"] for p in partidos)
    e = sum(p["gf"] == p["gc"] for p in partidos)
    xgf = [p["xg_favor"] for p in partidos]
    xgc = [p["xg_contra"] for p in partidos]
    xpts = [puntos_esperados(p["xg_favor"], p["xg_contra"]) for p in partidos]
    def suma(lista):
        v = [x for x in lista if x is not None]
        return round(sum(v), 2) if v else None

    def resta(a, b):
        return None if a is None or b is None else round(a - b, 2)

    def texto_par(a, b):
        return "" if a is None and b is None else f"{a or 0:g}-{b or 0:g}"

    puntos = 3 * g + e
    dif = resta(suma(xgf), suma(xgc))
    return {
        "Grupo": nombre, "PJ": len(partidos), "G-E-P": f"{g}-{e}-{len(partidos) - g - e}", "Puntos": puntos,
        "xPts": suma(xpts),
        "GF": sum(p["gf"] for p in partidos), "GC": sum(p["gc"] for p in partidos),
        "xG favor": suma(xgf), "xG contra": suma(xgc), "Dif. xG": dif,
        "Dif. xG/partido": None if dif is None else round(dif / len(partidos), 2),
        "Ocasiones claras (F-C)": texto_par(suma([p["oc_favor"] for p in partidos]), suma([p["oc_contra"] for p in partidos])),
        "Posesión media": _media(p["posesion"] for p in partidos),
        "PRPAD medio": _media(p["prpad"] for p in partidos),
        "Faltas/partido": _media(p["faltas"] for p in partidos),
        "Amarillas/partido": _media(p["amarillas"] for p in partidos),
    }


COLS = ["Grupo", "PJ", "G-E-P", "Puntos", "xPts", "GF", "GC", "xG favor", "xG contra", "Dif. xG", "Dif. xG/partido",
        "Ocasiones claras (F-C)", "Posesión media", "PRPAD medio", "Faltas/partido", "Amarillas/partido"]


def generar(ruta_csv, cfg, carpeta, carpeta_liga=None):
    c = cfg.get("partidos", {})
    partidos, errores, faltan = leer_partidos(ruta_csv)
    # Si no has puesto la posición del rival, la tomo de la última clasificación guardada
    fecha_tabla, tabla = cargar_clasificacion(carpeta_liga) if carpeta_liga else (None, {})
    rellenadas = 0
    for p in partidos:
        if p["pos_rival"] is None and tabla:
            p["pos_rival"] = buscar_posicion(tabla, p["rival"])
            rellenadas += p["pos_rival"] is not None
    if not partidos:
        return None, errores
    partidos.sort(key=lambda p: (p["jornada"] if p["jornada"] is not None else 999, p["fecha"] or fecha("1/1/2100")))
    ultima = max((p["fecha"] for p in partidos if p["fecha"]), default=None)
    inf = Informe("partidos", f"Seguimiento de partidos · {cfg.get('club', '')}", ultima)
    for e in errores:
        inf.aviso(e)
    if faltan:
        inf.aviso("Columnas que faltan en partidos.csv: " + ", ".join(faltan))
    if rellenadas:
        inf.texto(f"Posición del rival: en {rellenadas} partidos la tomo de la clasificación del "
                  f"{fecha_tabla.strftime('%d/%m/%Y')} (su puesto actual, no el del día del partido).")
    sin_xg = [p for p in partidos if p["xg_favor"] is None or p["xg_contra"] is None]
    if sin_xg:
        inf.aviso(f"{len(sin_xg)} partidos sin xG en partidos.csv: el análisis por xG estará incompleto hasta que los rellenes "
                  "(" + ", ".join(f"{p['fecha'].strftime('%d/%m') if p['fecha'] else '?'} {p['rival']}" for p in sin_xg) + ").")

    def alertas(fila):
        a = []
        if fila["Faltas/partido"] is not None and fila["Faltas/partido"] > c.get("faltas_por_partido_alerta", 14):
            a.append("faltas altas")
        if fila["Amarillas/partido"] is not None and fila["Amarillas/partido"] > c.get("amarillas_por_partido_alerta", 2.5):
            a.append("tarjetas altas")
        fila["Alerta"] = ", ".join(a)
        fila["_nivel"] = "rojo" if a else ""
        return fila

    # Total y bloques de N jornadas
    bloque = c.get("bloque_jornadas", 10)
    liga = [p for p in partidos if p["jornada"] is not None]
    filas = [alertas(resumen(partidos, "Temporada (todo)"))]
    bloques = {}
    for p in liga:
        bloques.setdefault(int((p["jornada"] - 1) // bloque), []).append(p)
    for b in sorted(bloques):
        filas.append(alertas(resumen(bloques[b], f"Jornadas {b * bloque + 1}-{(b + 1) * bloque}")))
    sin_jornada = [p for p in partidos if p["jornada"] is None]
    if sin_jornada:
        filas.append(alertas(resumen(sin_jornada, "Sin jornada (copa/amistosos)")))
    inf.seccion(f"Por bloques de {bloque} jornadas")
    inf.texto("Evalúa por xG, no por resultados: si Puntos > xPts, hay suerte que puede acabarse; si es al revés, el juego merece más.")
    inf.tabla("Bloques", COLS + ["Alerta"], filas)

    # Tendencia entre los dos últimos bloques
    claves = sorted(bloques)
    if len(claves) >= 2:
        a, b = resumen(bloques[claves[-2]], ""), resumen(bloques[claves[-1]], "")
        cambios = []
        for k, txt in (("Dif. xG/partido", "diferencia de xG por partido"), ("PRPAD medio", "PRPAD (más bajo = más presión)"),
                       ("Posesión media", "posesión"), ("Faltas/partido", "faltas")):
            if a[k] is not None and b[k] is not None:
                cambios.append(f"{txt}: {a[k]:g} → {b[k]:g} ({b[k] - a[k]:+.2f})")
        inf.seccion("Tendencia (último bloque frente al anterior)")
        inf.lista(cambios)

    # Casa / fuera
    inf.seccion("En casa y fuera")
    inf.tabla("Casa-fuera", COLS, [r for r in (resumen([p for p in partidos if p["local"]], "Local"),
                                               resumen([p for p in partidos if p["local"] is False], "Visitante")) if r])
    sin_campo = [p for p in partidos if p["local"] is None]
    if sin_campo:
        inf.aviso(f"{len(sin_campo)} partidos sin indicar Local/Visitante: no cuentan en esta tabla.")

    # Rivales de arriba / abajo
    inf.seccion("Según el rival")
    arriba, abajo = c.get("rivales_arriba_hasta", 6), c.get("rivales_abajo_desde", 13)
    con_pos = [p for p in partidos if p["pos_rival"] is not None]
    if not con_pos:
        inf.aviso("Rellena la columna «Posición rival» para comparar contra los de arriba y los de abajo.")
    else:
        inf.tabla("Rivales", COLS, [r for r in (
            resumen([p for p in con_pos if p["pos_rival"] <= arriba], f"Rivales de arriba (1-{arriba})"),
            resumen([p for p in con_pos if arriba < p["pos_rival"] < abajo], "Rivales de mitad de tabla"),
            resumen([p for p in con_pos if p["pos_rival"] >= abajo], f"Rivales de abajo ({abajo}+)"),
        ) if r])

    # Mentalidad
    inf.seccion("Según la mentalidad usada")
    mentalidades = sorted({p["mentalidad"] for p in partidos})
    inf.tabla("Mentalidad", COLS, [resumen([p for p in partidos if p["mentalidad"] == m], m) for m in mentalidades])

    # Próximos partidos (calendario guardado en data/liga)
    ruta_cal = _ultimo(carpeta_liga, "calendario") if carpeta_liga else None
    if ruta_cal:
        _, cal = leer_csv(ruta_cal)
        jugados = {p["fecha"] for p in partidos}
        proximos = []
        for f in cal:
            d = fecha(f.get("Fecha"))
            if d is None or d in jugados or (f.get("Resultado") or "").strip() not in ("", "-"):
                continue
            pos = buscar_posicion(tabla, f.get("Club", ""))
            tramo = ("" if pos is None else "de arriba" if pos <= arriba else "de abajo" if pos >= abajo else "mitad")
            proximos.append({"Fecha": d.strftime("%d/%m/%Y"), "Rival": f.get("Club"),
                             "Campo": "Local" if (f.get("Estadio") or "").strip().upper() == "C" else "Visitante",
                             "Pos. rival": pos, "Tramo": tramo, "Competición": f.get("Competición"),
                             "_nivel": "naranja" if tramo == "de arriba" else ""})
        inf.seccion("Próximos partidos")
        inf.tabla("Próximos", ["Fecha", "Rival", "Campo", "Pos. rival", "Tramo", "Competición"], proximos[:8])

    # Lista de partidos
    inf.seccion("Partidos")
    inf.tabla("Partidos", ["Fecha", "J", "Rival", "Pos. rival", "Campo", "Resultado", "xG", "xPts", "Mentalidad"], [{
        "Fecha": p["fecha"].strftime("%d/%m/%Y") if p["fecha"] else "", "J": p["jornada"], "Rival": p["rival"],
        "Pos. rival": p["pos_rival"], "Campo": {True: "Local", False: "Visitante"}.get(p["local"], "?"), "Resultado": f"{p['gf']}-{p['gc']}",
        "xG": f"{p['xg_favor']:g}-{p['xg_contra']:g}" if p["xg_favor"] is not None and p["xg_contra"] is not None else "",
        "xPts": round(puntos_esperados(p["xg_favor"], p["xg_contra"]), 2) if p["xg_favor"] is not None and p["xg_contra"] is not None else None,
        "Mentalidad": p["mentalidad"],
    } for p in partidos])
    return inf.guardar(carpeta), errores
