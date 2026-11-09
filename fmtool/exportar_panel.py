"""Exporta los datos del panel de analista (claude.ai) a CSV en la carpeta panel/."""

import csv
from pathlib import Path

from .comun import NOMBRE_GRUPO, RAIZ
from .datos import fecha, fecha_limite_renovacion, leer_csv, meses_entre, numero, texto_potencial, valor_estimado
from .inf_cantera import proponer_nivel
from .inf_equipo import METRICAS, _valoracion
from .inf_partidos import (buscar_posicion, cargar_clasificacion, leer_partidos, puntos_esperados,
                           rendimiento_jugadores)
from .inf_plantilla import recomendar


def _escribir(ruta, columnas, filas):
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        for fila in filas:
            w.writerow({c: _limpio(fila.get(c)) for c in columnas})


def _limpio(v):
    """Vacío para None y 3.0 -> 3, para que el CSV se lea limpio."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def exportar(p, cfg, carpeta=RAIZ / "panel"):
    carpeta = Path(carpeta)
    carpeta.mkdir(exist_ok=True)
    liga = RAIZ / "data" / "liga"
    _, tabla = cargar_clasificacion(liga)

    # Partidos
    partidos, _, _ = leer_partidos(RAIZ / "data" / "partidos" / "partidos.csv")
    partidos.sort(key=lambda x: (x["jornada"] or 999))
    filas = []
    for x in partidos:
        xpts = puntos_esperados(x["xg_favor"], x["xg_contra"])
        pts = 3 if x["gf"] > x["gc"] else (1 if x["gf"] == x["gc"] else 0)
        filas.append({
            "jornada": int(x["jornada"]) if x["jornada"] else "", "fecha": x["fecha"].isoformat() if x["fecha"] else "",
            "rival": x["rival"], "pos_rival": x["pos_rival"] if x["pos_rival"] is not None else buscar_posicion(tabla, x["rival"]),
            "campo": {True: "Local", False: "Visitante"}.get(x["local"], ""), "resultado": f"{x['gf']}-{x['gc']}",
            "goles_favor": x["gf"], "goles_contra": x["gc"], "puntos": pts,
            "xg_favor": x["xg_favor"], "xg_contra": x["xg_contra"], "xpts": round(xpts, 2) if xpts is not None else None,
            "posesion": x["posesion"], "prpad": x["prpad"], "faltas": x["faltas"], "amarillas": x["amarillas"],
            "disparos_favor": x["dis_favor"], "disparos_contra": x["dis_contra"],
            "corners_favor": x["cor_favor"], "corners_contra": x["cor_contra"], "mentalidad": x["mentalidad"],
        })
    _escribir(carpeta / "partidos.csv", list(filas[0]) if filas else ["jornada"], filas)

    # Jugadores (un registro por jugador)
    rend = {r["Jugador"]: r for r in rendimiento_jugadores(RAIZ / "data" / "partidos")}
    filas = []
    for j in p.unicos():
        accion, motivo = recomendar(p, j)
        r = rend.get(j["jugador"], {})
        filas.append({
            "jugador": j["jugador"], "equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "edad": j["edad"],
            "posicion": j["mejor_pos"] or j["posicion"], "calidad": j["calidad"], "potencial": texto_potencial(j),
            "potencial_num": p.pot(j), "nota": j["nota"], "titularidades": r.get("Titularidades", 0),
            "goles": r.get("Goles", 0), "asistencias": r.get("Asistencias", 0), "sueldo": j["sueldo"],
            "tope": p.tope(j), "fin_contrato": j["fin"].isoformat() if j["fin"] else "", "clausula": j["clausula"],
            "valor_max": j["valor_max"], "valor_estimado": valor_estimado(j), "accion": accion, "motivo": motivo,
            "le_siguen": "Sí" if p.le_siguen(j) else "No", "cedido": "Sí" if p.es_cedido_aqui(j) else "No",
            "lesionado": "Sí" if "Les" in p.codigos_inf(j) else "No",
            "meses_contrato": meses_entre(p.fecha, j["fin"]),
            "limite_renovar": fecha_limite_renovacion(j["fin"]).isoformat() if j["fin"] else "",
            "exceso_tope": (j["sueldo"] - p.tope(j)) if j["sueldo"] and p.tope(j) and j["sueldo"] > p.tope(j) else 0,
        })
    _escribir(carpeta / "jugadores.csv", list(filas[0]), filas)

    # Métricas del Centro de datos frente a la liga
    filas = []
    archivos = sorted((RAIZ / "data" / "analitica").glob("equipo_*.csv"))
    if archivos:
        _, met = leer_csv(archivos[-1])
        for m in met:
            v, med = numero(m.get("Salamanca")), numero(m.get("Media 2F5"))
            if med is None:
                continue
            texto, _ = _valoracion(m["Métrica"], v, med)
            filas.append({"bloque": m["Bloque"], "metrica": m["Métrica"], "que_es": METRICAS.get(m["Métrica"], ("", 0))[0],
                          "nosotros": v, "media_liga": med, "diferencia_pct": round((v - med) / med * 100, 1) if med else None,
                          "valoracion": texto})
    _escribir(carpeta / "metricas.csv", ["bloque", "metrica", "que_es", "nosotros", "media_liga", "diferencia_pct", "valoracion"], filas)

    # Clasificación
    ruta = sorted(liga.glob("clasificacion_*.csv"))
    filas = []
    if ruta:
        _, cl = leer_csv(ruta[-1])
        for c in cl:
            jug, g, pe = int(c["Jug"]), int(c["G"]), int(c["P"])
            filas.append({"pos": int(c["Pos"]), "equipo": c["Equipo"], "jugados": jug, "ganados": g, "empatados": jug - g - pe,
                          "perdidos": pe, "dif_goles": int(c["Dif."]), "puntos": int(c["Pts"])})
    _escribir(carpeta / "clasificacion.csv", ["pos", "equipo", "jugados", "ganados", "empatados", "perdidos", "dif_goles", "puntos"], filas)
    # Cantera: 19 años o menos, potencial alto, en filial o juvenil
    c = cfg.get("cantera", {})
    filas, vistos = [], set()
    for j in p.jugadores:
        pot = p.pot(j)
        if (j["grupo"] not in c.get("grupos", ["filial", "juvenil"]) or j["jugador"] in vistos or j["edad"] is None
                or j["edad"] > c.get("edad_maxima", 19) or pot is None or pot < c.get("potencial_minimo", 4)):
            continue
        vistos.add(j["jugador"])
        nivel, motivo = proponer_nivel(p, j)
        filas.append({"jugador": j["jugador"], "equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "edad": j["edad"],
                      "posicion": j["mejor_pos"] or j["posicion"], "calidad": j["calidad"], "potencial": texto_potencial(j),
                      "potencial_num": pot, "clausula": j["clausula"], "valor_max": j["valor_max"],
                      "le_siguen": "Sí" if p.le_siguen(j) else "No", "propuesta": nivel, "motivo": motivo})
    filas.sort(key=lambda f: (-f["potencial_num"], f["edad"]))
    _escribir(carpeta / "cantera.csv", list(filas[0]) if filas else ["jugador"], filas)

    # Calendario: próximos partidos con la posición del rival
    ruta = sorted(liga.glob("calendario_*.csv"))
    filas = []
    if ruta:
        _, cal = leer_csv(ruta[-1])
        arriba, abajo = cfg.get("partidos", {}).get("rivales_arriba_hasta", 6), cfg.get("partidos", {}).get("rivales_abajo_desde", 13)
        for f in cal:
            if (f.get("Resultado") or "").strip() not in ("", "-"):
                continue
            pos = buscar_posicion(tabla, f.get("Club", ""))
            filas.append({"fecha": fecha(f["Fecha"]).isoformat(), "rival": f["Club"],
                          "campo": "Local" if f.get("Estadio", "").strip().upper() == "C" else "Visitante", "pos_rival": pos,
                          "tramo": "" if pos is None else "Arriba" if pos <= arriba else "Abajo" if pos >= abajo else "Mitad"})
    _escribir(carpeta / "calendario.csv", ["fecha", "rival", "campo", "pos_rival", "tramo"], filas)

    # Análisis escrito (tareas, once propuesto, cambios de táctica): se copian de data/analisis
    for nombre in ("tareas", "once", "tactica"):
        ruta = RAIZ / "data" / "analisis" / f"{nombre}.csv"
        if ruta.exists():
            cols, filas = leer_csv(ruta)
            _escribir(carpeta / f"{nombre}.csv", cols, filas)
    return sorted(carpeta.glob("*.csv"))
