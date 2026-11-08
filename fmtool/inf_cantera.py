"""Seguimiento de la cantera: jóvenes con potencial alto, su evolución y dónde deben jugar."""

from .comun import NOMBRE_GRUPO
from .datos import fmt_fecha, texto_potencial
from .salida import Informe


def proponer_nivel(p, j):
    """Propone dónde debe jugar comparando su calidad con la de cada equipo."""
    c = p.cfg.get("cantera", {})
    cal = j["calidad"] or 0
    med_primer = p.mediana_calidad.get("primer-equipo") or 99
    med_filial = p.mediana_calidad.get("filial") or 99
    if j["estado"] == "Cedido en otro club":
        return "Sigue cedido", "Está cedido: revisar sus minutos en el club de destino."
    if cal >= med_primer:
        return "Primer equipo", f"Su calidad ({cal:g}★) ya iguala la mediana del primer equipo ({med_primer:g}★)."
    if cal >= med_filial or (j["edad"] or 0) > c.get("edad_maxima_juvenil", 18):
        motivo = (f"Calidad {cal:g}★, al nivel del filial ({med_filial:g}★)." if cal >= med_filial
                  else f"Con {j['edad']} años ya no puede jugar en el juvenil.")
        return "Filial", motivo
    return "Juvenil", f"Calidad {cal:g}★, por debajo del filial ({med_filial:g}★): necesita minutos en el juvenil."


def generar(p, carpeta):
    c = p.cfg.get("cantera", {})
    inf = Informe("cantera", f"Cantera · {p.cfg.get('club', '')}", p.fecha)
    inf.texto(f"Jugadores de {c.get('edad_maxima', 19)} años o menos, de {', '.join(c.get('grupos', []))}, "
              f"con potencial de {c.get('potencial_minimo', 4):g}★ o más (criterio «{p.cfg.get('criterio_potencial', 'media')}»).")
    if "entrenamiento" not in p.columnas:
        inf.aviso("La «Valoración de entrenamiento» no sale en las capturas. Pásame una captura de "
                  "Entrenamiento > Valoraciones (o añade la columna) y aparecerá aquí.")

    filas = []
    for j in p.jugadores:
        if j["grupo"] not in c.get("grupos", ["filial", "juvenil"]):
            continue
        pot = p.pot(j)
        if j["edad"] is None or j["edad"] > c.get("edad_maxima", 19) or pot is None or pot < c.get("potencial_minimo", 4):
            continue
        if any(f["Jugador"] == j["jugador"] for f in filas):
            continue
        nivel, motivo = proponer_nivel(p, j)
        evo = p.evolucion(j)
        otros = sorted(p.grupos_de.get(j["jugador"], set()) - {j["grupo"]})
        if otros:
            motivo += " También inscrito en: " + ", ".join(NOMBRE_GRUPO.get(o, o) for o in otros) + "."
        filas.append({
            "Jugador": j["jugador"], "Equipo actual": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Edad": j["edad"],
            "Pos.": j["mejor_pos"] or j["posicion"], "Calidad": j["calidad"], "Potencial": texto_potencial(j),
            "Evolución calidad": ("primera captura" if not evo or evo["calidad"] is None
                                  else f"{evo['calidad']:+g} desde {fmt_fecha(evo['desde'])}"),
            "Evolución potencial": ("" if not evo or evo["potencial"] is None else f"{evo['potencial']:+g}"),
            "Entrenamiento": j["entrenamiento"] if j["entrenamiento"] is not None else "sin datos",
            "Fin contrato": fmt_fecha(j["fin"]), "Propuesta": nivel, "Motivo": motivo,
            "_nivel": "verde" if nivel == "Primer equipo" else "", "_pot": pot,
        })
    filas.sort(key=lambda f: (-f["_pot"], f["Edad"]))
    inf.seccion(f"Joyas de la cantera ({len(filas)})")
    inf.tabla("Cantera", ["Jugador", "Equipo actual", "Edad", "Pos.", "Calidad", "Potencial", "Evolución calidad",
                          "Evolución potencial", "Entrenamiento", "Fin contrato", "Propuesta", "Motivo"], filas)
    m = {g: (f"{v:g}★" if v is not None else "sin datos") for g, v in p.mediana_calidad.items()}
    inf.texto(f"Referencia de nivel (calidad mediana): primer equipo {m['primer-equipo']} · "
              f"filial {m['filial']} · juvenil {m['juvenil']}.")
    return inf.guardar(carpeta)
