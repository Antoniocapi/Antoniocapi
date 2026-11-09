"""Ranking de fichajes con la puntuación "modelo Castellón" (0-100) a partir de las listas de ojeo."""

import re

from . import bd
from .comun import NOMBRE_DATO, RAIZ
from .datos import fmt_euros, fmt_fecha, meses_entre, posiciones, potencial, texto_potencial
from .salida import Informe

PRIORIDAD = {"alta": 1.0, "media": 0.7, "baja": 0.4}
LETRAS = {"A+": 1.0, "A": 0.9, "A-": 0.85, "B+": 0.75, "B": 0.7, "B-": 0.6, "C+": 0.55, "C": 0.5,
          "C-": 0.4, "D": 0.3, "E": 0.1}


def _limitar(x):
    return max(0.0, min(1.0, x))


def nota_recomendacion(texto):
    """Convierte la recomendación del ojeador en 0-1. None si el formato no se reconoce."""
    if not texto:
        return None
    t = texto.strip().upper()
    if t in LETRAS:
        return LETRAS[t]
    m = re.search(r"\d+([.,]\d+)?", t)
    if m:
        v = float(m[0].replace(",", "."))
        return _limitar(v / 10 if v <= 10 else v / 100)
    return None


def puntuar(j, cfg, ctx):
    """Calcula cada criterio (0-1, o None si falta el dato) y los motivos de descarte."""
    f = cfg.get("fichajes", {})
    topes = cfg.get("topes_sueldo", {})
    c, descartes = {}, []

    # Edad
    e = j["edad"]
    if e is None:
        c["edad"] = None
    else:
        ideal, acept = f.get("edad_ideal", [19, 23]), f.get("edad_aceptable", [19, 25])
        if ideal[0] <= e <= ideal[1]:
            c["edad"] = 1.0
        elif acept[0] <= e <= acept[1]:
            c["edad"] = 0.6
        elif e < acept[0]:
            c["edad"] = 0.5
        else:
            c["edad"] = _limitar(0.6 - 0.2 * (e - acept[1]))
        if e > f.get("edad_maxima", 27):
            descartes.append(f"{e} años (máximo {f.get('edad_maxima', 27)})")

    # Estrellas
    pot = potencial(j, cfg.get("criterio_potencial", "media"))
    if j["calidad"] is None or pot is None:
        descartes.append("sin estrellas de calidad/potencial (falta conocimiento de ojeo)")
        c["potencial"] = c["calidad"] = None
    else:
        c["potencial"] = _limitar((pot - 2.5) / 2)
        c["calidad"] = _limitar((j["calidad"] - (ctx["nivel"] - 1)) / 1.5)
        if pot < ctx["nivel"]:
            descartes.append(f"potencial {texto_potencial(j)}★ por debajo del nivel del primer equipo ({ctx['nivel']:g}★)")

    # Recomendación del ojeador
    c["recomendacion"] = nota_recomendacion(j["recomendacion"])

    # Coste: libre / cesión / traspaso y sueldo frente a los topes
    situacion = (j["situacion"] or "").lower()
    libre = ("libre" in situacion or "sin contrato" in situacion
             or ("club" in j["columnas"] and j["club"].lower() in ("", "sin club", "libre")))
    cesion = "cedible" in situacion or "cesión" in situacion or "cesion" in situacion
    coste = None
    if libre:
        coste, tipo = 1.0, "Libre"
    elif cesion:
        coste, tipo = 0.85, "Cesión"
    elif j["valor_min"] is not None:
        presupuesto = ctx["presupuesto_traspasos"]
        coste, tipo = _limitar(1 - j["valor_min"] / presupuesto), "Traspaso"
        if j["valor_min"] > presupuesto:
            descartes.append(f"traspaso mínimo {fmt_euros(j['valor_min'])} > presupuesto {fmt_euros(presupuesto)}")
    else:
        tipo = "?"
    if j["sueldo"] is not None:
        if ctx["margen_sueldos"] is not None and j["sueldo"] > ctx["margen_sueldos"]:
            descartes.append(f"sueldo {fmt_euros(j['sueldo'])} > margen salarial tras la reserva de enero ({fmt_euros(ctx['margen_sueldos'])})")
        factor = 1.0 if j["sueldo"] <= topes.get("rotacion", 40000) else 0.7
        coste = factor if coste is None else coste * factor
    c["coste"] = coste

    # Contrato que acaba pronto
    meses = meses_entre(j["fecha_juego"], j["fin"])
    c["contrato"] = 1.0 if libre else None if meses is None else (1.0 if meses <= 6 else 0.7 if meses <= 12 else 0.4 if meses <= 18 else 0.1)

    # Encaje en las posiciones que necesito
    necesarias = cfg.get("posiciones_necesarias") or []
    grupo_pos = j["mejor_pos"] or j["posicion"] or "Sin posición"
    if not necesarias:
        c["encaje"] = None
    else:
        mejor, grupo = 0.0, None
        natural, todas = posiciones(j["mejor_pos"]), posiciones(j["posicion"]) | posiciones(j["mejor_pos"])
        for n in necesarias:
            objetivo = posiciones(n.get("posicion"))
            peso = PRIORIDAD.get(str(n.get("prioridad", "media")).lower(), 0.7)
            v = peso if natural & objetivo else (peso * 0.8 if todas & objetivo else 0)
            if v > mejor:
                mejor, grupo = v, n.get("posicion")
        c["encaje"] = mejor
        if grupo:
            grupo_pos = grupo
        elif f.get("descartar_sin_encaje"):
            descartes.append("no encaja en ninguna posición necesaria")

    pesos = f.get("pesos", {})
    usados = {k: v for k, v in c.items() if v is not None and pesos.get(k)}
    total_pesos = sum(pesos[k] for k in usados)
    nota = round(100 * sum(pesos[k] * v for k, v in usados.items()) / total_pesos, 1) if total_pesos else 0
    return nota, c, descartes, tipo, meses, grupo_pos


def generar(conn, cfg, plantilla, carpeta):
    alias = cfg.get("alias_columnas") or {}
    lista = bd.estado_actual(conn, "ojeo", alias)
    if not lista:
        return None
    fecha = max(j["fecha_juego"] for j in lista)
    inf = Informe("fichajes", f"Ranking de fichajes · modelo Castellón · {cfg.get('club', '')}", fecha)

    # Un registro por jugador, juntando los focos en que aparece
    jugadores = {}
    for j in lista:
        if j["jugador"] in jugadores:
            jugadores[j["jugador"]]["focos"].add(j["grupo"])
        else:
            j["focos"] = {j["grupo"]}
            jugadores[j["jugador"]] = j
    propios = {j["jugador"] for j in plantilla.jugadores}
    ps, pf = cfg.get("presupuesto_sueldos") or {}, cfg.get("presupuesto_fichajes") or {}
    ctx = {
        "nivel": plantilla.mediana_calidad.get("primer-equipo") or 3,
        "presupuesto_traspasos": cfg.get("fichajes", {}).get("presupuesto_traspasos") or pf.get("disponible") or 0,
        "margen_sueldos": (ps["disponible"] - cfg.get("reserva_enero", 0)) if ps.get("disponible") is not None else None,
    }

    columnas = set().union(*(j["columnas"] for j in jugadores.values()))
    faltan = [d for d in ("recomendacion", "situacion", "club", "sueldo", "fin_contrato") if d not in columnas]
    faltan_txt = [NOMBRE_DATO.get(d, {"sueldo": "Sueldo", "fin_contrato": "Fin de contrato"}.get(d, d)) for d in faltan]
    if faltan_txt:
        inf.aviso("Datos que no salen en las listas de ojeo (esos criterios no cuentan en la nota): " + ", ".join(faltan_txt))
    if not cfg.get("posiciones_necesarias"):
        inf.aviso("No has definido «posiciones_necesarias» en config.yaml: el criterio de encaje no cuenta.")
    pesos = cfg.get("fichajes", {}).get("pesos", {})
    inf.texto("Pesos: " + ", ".join(f"{k} {v}" for k, v in pesos.items())
              + f". Nivel de referencia (calidad mediana del primer equipo): {ctx['nivel']:g}★. "
              + f"Traspaso máximo: {fmt_euros(ctx['presupuesto_traspasos'])}. "
              + ("" if ctx["margen_sueldos"] is None else f"Margen salarial tras la reserva de enero: {fmt_euros(ctx['margen_sueldos'])} al año."))

    validos, descartados = [], []
    for j in jugadores.values():
        if j["jugador"] in propios:
            continue
        nota, c, descartes, tipo, meses, grupo_pos = puntuar(j, cfg, ctx)
        fila = {
            "Nota": nota, "Jugador": j["jugador"], "Edad": j["edad"], "Pos.": j["mejor_pos"] or j["posicion"],
            "Club": j["club"], "Calidad": j["calidad"], "Potencial": texto_potencial(j),
            "Recomendación": j["recomendacion"], "Tipo": tipo, "Valor mín. (€)": j["valor_min"],
            "Sueldo (€)": j["sueldo"], "Fin contrato": fmt_fecha(j["fin"]), "Meses": meses,
            "Focos": ", ".join(sorted(j["focos"])), "_grupo": grupo_pos,
            "Desglose": " · ".join(f"{k} {v:.2f}" for k, v in c.items() if v is not None),
        }
        if descartes:
            fila["Motivo del descarte"] = "; ".join(descartes)
            descartados.append(fila)
        else:
            fila["_nivel"] = "verde" if nota >= 70 else ("naranja" if nota >= 55 else "")
            validos.append(fila)

    cols = ["Nota", "Jugador", "Edad", "Pos.", "Club", "Calidad", "Potencial", "Recomendación", "Tipo",
            "Valor mín. (€)", "Sueldo (€)", "Fin contrato", "Focos", "Desglose"]
    orden = [n.get("posicion") for n in cfg.get("posiciones_necesarias") or []]
    grupos = sorted({f["_grupo"] for f in validos}, key=lambda g: (orden.index(g) if g in orden else 99, g))
    inf.seccion("Ranking por posición")
    inf.texto("🟢 70 o más · 🟠 55-70.")
    for g in grupos:
        filas = sorted((f for f in validos if f["_grupo"] == g), key=lambda f: -f["Nota"])
        inf.seccion(f"{g} ({len(filas)})")
        inf.tabla(g, cols, filas)
    inf.seccion(f"Descartados ({len(descartados)})")
    inf.tabla("Descartados", ["Jugador", "Edad", "Pos.", "Calidad", "Potencial", "Nota", "Motivo del descarte"],
              sorted(descartados, key=lambda f: -f["Nota"]))
    # CSV para el panel (pestaña Mercado)
    import csv as _csv
    filas_panel = [dict(f, Estado="Candidato") for f in validos] + [dict(f, Estado="Descartado") for f in descartados]
    filas_panel.sort(key=lambda f: (f["Estado"] != "Candidato", -f["Nota"]))
    with open(RAIZ / "panel" / "fichajes.csv", "w", encoding="utf-8", newline="") as fh:
        w = _csv.writer(fh)
        w.writerow(["jugador", "estado", "nota", "edad", "posicion", "calidad", "potencial", "tipo", "valor_min", "sueldo", "fin", "precontrato", "motivo"])
        for f in filas_panel:
            pre = "Sí" if f["Fin contrato"].endswith("2029") else ""
            w.writerow([f["Jugador"], f["Estado"], f["Nota"], f["Edad"], f["Pos."], f["Calidad"], f["Potencial"], f["Tipo"],
                        f["Valor mín. (€)"] if f["Valor mín. (€)"] is not None else "", f["Sueldo (€)"] if f["Sueldo (€)"] is not None else "",
                        f["Fin contrato"], pre, f.get("Motivo del descarte", "")])
    return inf.guardar(carpeta)
