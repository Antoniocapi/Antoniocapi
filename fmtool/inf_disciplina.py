"""Disciplina: amarillas por jugador y quién está a punto de cumplir ciclo."""

from .comun import NOMBRE_GRUPO
from .salida import Informe


def generar(p, carpeta):
    ciclo = p.cfg.get("disciplina", {}).get("ciclo_amarillas", 5)
    inf = Informe("disciplina", f"Disciplina · {p.cfg.get('club', '')}", p.fecha)
    if "amarillas" not in p.columnas:
        inf.aviso("Las capturas no tienen la columna de tarjetas amarillas. Pásame una captura de la vista "
                  "de Estadísticas de la plantilla con «Amarillas» (y «Rojas» si se puede) y este informe se completará.")
        return inf.guardar(carpeta)
    filas = []
    for j in p.unicos():
        if j["amarillas"] is None:
            continue
        am = int(j["amarillas"])
        resto = am % ciclo
        faltan = ciclo - resto
        nivel = "rojo" if faltan == 1 else ("naranja" if faltan == 2 else "")
        filas.append({
            "Jugador": j["jugador"], "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Amarillas": am,
            "Rojas": int(j["rojas"]) if j["rojas"] is not None else None,
            "Ciclos cumplidos": am // ciclo, "Amarillas en el ciclo actual": resto,
            "Le faltan para sanción": faltan,
            "Aviso": "¡A UNA de la sanción!" if faltan == 1 else ("A dos de la sanción" if faltan == 2 else ""),
            "_nivel": nivel,
        })
    filas.sort(key=lambda f: (f["Le faltan para sanción"], -f["Amarillas"]))
    inf.texto(f"Ciclo de {ciclo} amarillas = 1 partido de sanción (se cambia en config.yaml).")
    inf.seccion("Cerca de cumplir ciclo")
    inf.tabla("Cerca de ciclo", ["Jugador", "Equipo", "Amarillas", "Amarillas en el ciclo actual", "Le faltan para sanción", "Aviso"],
              [f for f in filas if f["Le faltan para sanción"] <= 2], "Nadie a 1 o 2 amarillas de la sanción.")
    inf.seccion("Todas las tarjetas")
    inf.tabla("Tarjetas", ["Jugador", "Equipo", "Amarillas", "Rojas", "Ciclos cumplidos", "Amarillas en el ciclo actual",
                           "Le faltan para sanción"], sorted(filas, key=lambda f: -f["Amarillas"]))
    return inf.guardar(carpeta)
