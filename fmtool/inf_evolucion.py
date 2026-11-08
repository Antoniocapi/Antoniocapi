"""Evolución de los jugadores entre capturas (estrellas, valor, sueldo, nota)."""

from .comun import NOMBRE_GRUPO
from .datos import fmt_fecha, texto_potencial
from .salida import Informe

COLS = ["Fecha", "Equipo", "Edad", "Calidad", "Potencial", "Valor mín. (€)", "Valor máx. (€)", "Sueldo (€)",
        "Nota", "Tiempo de juego", "Fin contrato"]


def _fila(j):
    return {
        "Fecha": fmt_fecha(j["fecha_juego"]), "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Edad": j["edad"],
        "Calidad": j["calidad"], "Potencial": texto_potencial(j), "Valor mín. (€)": j["valor_min"],
        "Valor máx. (€)": j["valor_max"], "Sueldo (€)": j["sueldo"], "Nota": j["nota"],
        "Tiempo de juego": j["estado"], "Fin contrato": fmt_fecha(j["fin"]),
    }


def generar(p, carpeta, nombre=None):
    if nombre:
        historial = p.historial(nombre)
        if not historial:
            parecidos = [j["jugador"] for j in p.jugadores if nombre.lower() in j["jugador"].lower()]
            return None, parecidos
        inf = Informe(f"evolucion_{nombre.replace(' ', '-')}", f"Evolución · {nombre}", p.fecha)
        inf.tabla(nombre, COLS, [_fila(j) for j in historial])
        return inf.guardar(carpeta), []

    inf = Informe("evolucion", f"Evolución de la plantilla · {p.cfg.get('club', '')}", p.fecha)
    fechas = sorted({j["fecha_juego"] for nombre in p._historial for j in p._historial[nombre]})
    inf.texto("Capturas guardadas: " + ", ".join(fmt_fecha(f) for f in fechas))
    filas = []
    for j in p.unicos():
        evo = p.evolucion(j)
        if not evo:
            continue
        filas.append({
            "Jugador": j["jugador"], "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Edad": j["edad"],
            "Desde": fmt_fecha(evo["desde"]), "Calidad ahora": j["calidad"], "Δ calidad": evo["calidad"],
            "Potencial ahora": texto_potencial(j), "Δ potencial": evo["potencial"], "Δ valor máx. (€)": evo["valor"],
            "_nivel": "verde" if (evo["calidad"] or 0) > 0 else ("rojo" if (evo["potencial"] or 0) < 0 else ""),
        })
    if not filas:
        inf.aviso("Solo hay una captura por jugador: la evolución aparecerá cuando me pases capturas de otra fecha.")
    filas.sort(key=lambda f: -((f["Δ calidad"] or 0) + (f["Δ potencial"] or 0)))
    inf.tabla("Evolución", ["Jugador", "Equipo", "Edad", "Desde", "Calidad ahora", "Δ calidad", "Potencial ahora",
                            "Δ potencial", "Δ valor máx. (€)"], filas)
    return inf.guardar(carpeta), []
