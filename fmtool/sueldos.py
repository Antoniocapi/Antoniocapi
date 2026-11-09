"""Sueldo justo según rendimiento (en lugar de topes fijos).

Idea: con la MISMA masa salarial de cada equipo, ¿cuánto cobraría cada jugador si el
club pagara según lo que aporta? Se hace en tres pasos:

1. Puntuación de cada jugador (más alta = aporta más), combinando:
   - calidad en estrellas (lo que el jugador ES),
   - nota media "ajustada": con pocos minutos la nota es poco fiable, así que se mezcla con
     la media del equipo según los minutos jugados (contracción bayesiana: con 270'
     cuenta la mitad la nota del jugador y la mitad la del equipo),
   - participación (porcentaje de minutos jugados),
   - margen de mejora (potencial - calidad), solo para menores de 24 años.
   En filial y juvenil no hay notas ni minutos: calidad y potencial.
2. Se ordena a los jugadores por puntuación.
3. Sueldo justo: se toman la media y la dispersión (en escala logarítmica) de los sueldos reales
   del equipo y se coloca a cada jugador según su puntuación. Quien está 1 desviación por encima
   de la media en puntuación "merece" un sueldo 1 desviación por encima de la media del equipo.

Así el sueldo justo sube cuando el jugador mejora y baja cuando rinde menos, sin topes fijos.
"""

import math
from statistics import mean, pstdev

PESOS_PRIMER = {"calidad": 0.45, "nota": 0.35, "participacion": 0.10, "margen": 0.10}
PESOS_CANTERA = {"calidad": 0.70, "potencial": 0.30}
MINUTOS_CONFIANZA = 270  # minutos a partir de los cuales la nota del jugador pesa más que la del equipo


def _z(valores):
    """Tipifica una lista (media 0, desviación 1). Si no varía, todo 0."""
    v = [x for x in valores if x is not None]
    if len(v) < 2:
        return [0.0 if x is not None else None for x in valores]
    m, s = mean(v), pstdev(v) or 1.0
    return [None if x is None else (x - m) / s for x in valores]


def calcular(p, umbral_mas=0.30, umbral_menos=-0.25):
    """Devuelve {(grupo, jugador): {...}} con puntuación, sueldo justo y valoración."""
    resultado = {}
    for grupo in ("primer-equipo", "filial", "juvenil"):
        js = [j for j in p.jugadores if j["grupo"] == grupo and j["sueldo"] and j["calidad"] is not None]
        # Fuera los cedidos a nuestro club y, en el primer equipo, los canteranos que también están
        # en el filial o el juvenil (cobran un sueldo de cantera y desvirtuarían la comparación)
        propios = [j for j in js if not p.es_cedido_aqui(j)
                   and not (grupo == "primer-equipo" and p.grupos_de.get(j["jugador"], set()) - {grupo})]
        if len(propios) < 3:
            continue
        partidos = max(p.partidos_con_once, 1)
        if grupo == "primer-equipo":
            con_nota = [j for j in propios if j["nota"] is not None]
            nota_ref = mean(j["nota"] for j in con_nota) if con_nota else None

            def nota_aj(j):
                if nota_ref is None:
                    return None
                minutos = j["minutos"] or 0
                if j["nota"] is None or minutos == 0:
                    return nota_ref
                return (minutos * j["nota"] + MINUTOS_CONFIANZA * nota_ref) / (minutos + MINUTOS_CONFIANZA)

            comps = {
                "calidad": _z([j["calidad"] for j in propios]),
                "nota": _z([nota_aj(j) for j in propios]),
                "participacion": _z([(j["minutos"] or 0) / (90 * partidos) for j in propios]),
                "margen": _z([max(0.0, (p.pot(j) or 0) - j["calidad"]) if (j["edad"] or 99) < 24 else 0.0 for j in propios]),
            }
            pesos = PESOS_PRIMER
        else:
            comps = {"calidad": _z([j["calidad"] for j in propios]), "potencial": _z([p.pot(j) for j in propios])}
            pesos = PESOS_CANTERA
        puntos = []
        for i, j in enumerate(propios):
            usados = {k: comps[k][i] for k in pesos if comps[k][i] is not None}
            total = sum(pesos[k] for k in usados) or 1
            puntos.append(sum(pesos[k] * v for k, v in usados.items()) / total)
        # Sueldo justo: en escala logarítmica, la media y la dispersión de los sueldos reales del
        # equipo, colocadas según la puntuación (tipificada). Mejor puntuación = sueldo más alto.
        logs = [math.log(j["sueldo"]) for j in propios]
        m_log, s_log = mean(logs), pstdev(logs)
        zp = _z(puntos)
        orden = sorted(range(len(propios)), key=lambda i: -puntos[i])
        for puesto, i in enumerate(orden):
            j = propios[i]
            justo = round(math.exp(m_log + s_log * zp[i]) / 500) * 500
            dif = (j["sueldo"] - justo) / justo if justo else 0
            if dif > umbral_mas:
                val = "Cobra de más"
            elif dif < umbral_menos:
                val = "Cobra de menos"
            else:
                val = "Acorde"
            resultado[(grupo, j["jugador"])] = {
                "puntuacion": round(puntos[i], 2), "puesto": puesto + 1, "de": len(propios),
                "sueldo_justo": justo, "diferencia_pct": round(dif * 100), "valoracion": val,
                "nota_ajustada": round(nota_aj(j), 2) if grupo == "primer-equipo" and nota_aj(j) is not None else None,
            }
    return resultado


def motivo(j, r):
    """Una frase que explica la valoración salarial."""
    if r["valoracion"] == "Cobra de más":
        return (f"Es el {r['puesto']}º que más aporta de {r['de']}, pero cobra como uno de los primeros: "
                f"{r['diferencia_pct']:+d} % sobre su sueldo justo.")
    if r["valoracion"] == "Cobra de menos":
        return (f"Es el {r['puesto']}º que más aporta de {r['de']} y cobra menos de lo que le tocaría "
                f"({r['diferencia_pct']:+d} %): al renovar, puede pedir más (y lo merece).")
    return f"Cobra acorde a lo que aporta ({r['puesto']}º de {r['de']})."
