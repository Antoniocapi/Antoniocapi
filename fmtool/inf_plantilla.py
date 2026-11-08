"""Informe de recomendaciones de plantilla: RENOVAR, VENDER YA, CEDER, SALE LIBRE, MANTENER."""

from .comun import NOMBRE_GRUPO, falta, NOMBRE_DATO
from .datos import (fecha_limite_renovacion, fmt_euros, fmt_fecha, meses_entre, posiciones,
                    texto_potencial, valor_estimado)
from .salida import Informe

ORDEN_ACCION = ["VENDER YA", "RENOVAR", "CEDER", "SALE LIBRE", "MANTENER", "CEDIDO AQUÍ", "SIN DATOS"]
NIVEL_ACCION = {"VENDER YA": "rojo", "RENOVAR": "verde", "CEDER": "naranja", "SALE LIBRE": "gris"}


SUFIJO_INTERES = {
    "RENOVAR": " Le siguen otros clubes: renovar YA y con cláusula alta.",
    "VENDER YA": " Le siguen otros clubes: aprovecha el interés para venderle.",
    "SALE LIBRE": " Le siguen otros clubes: intenta sacar algo por él antes de que se vaya gratis.",
    "CEDER": " Le siguen otros clubes: blinda su contrato antes de cederlo.",
    "MANTENER": " Le siguen otros clubes: vigila su cláusula.",
}


def recomendar(p, j):
    """Devuelve (acción, motivo en una frase) para un jugador. p = Plantilla."""
    accion, motivo = _recomendar(p, j)
    if p.le_siguen(j) and not p.es_cedido_aqui(j):
        motivo += SUFIJO_INTERES.get(accion, "")
    return accion, motivo


def _recomendar(p, j):
    r = p.cfg.get("recomendaciones", {})
    if p.es_cedido_aqui(j):
        return "CEDIDO AQUÍ", "Cedido por otro club: ni se renueva ni se vende."
    if j["calidad"] is None or j["pot_min"] is None:
        return "SIN DATOS", "La captura no muestra sus estrellas ni su contrato: no puedo recomendar nada."

    edad, cal, pot = j["edad"] or 0, j["calidad"], p.pot(j)
    margen = pot - cal
    meses = meses_entre(p.fecha, j["fin"])
    valor = valor_estimado(j) or 0
    fin = fmt_fecha(j["fin"])
    limite = fmt_fecha(fecha_limite_renovacion(j["fin"]))
    evo = p.evolucion(j)
    estrellas = f"{cal:g}★/{texto_potencial(j)}★"
    cedido_fuera = j["estado"] == "Cedido en otro club"
    hay_nota = j["nota"] is not None and (j["partidos"] or 0) >= r.get("partidos_minimos_nota", 5)

    # ---------------- VENDER YA
    if evo and evo["potencial_ultima"] is not None and evo["potencial_ultima"] < 0:
        return "VENDER YA", f"Su potencial ha bajado {abs(evo['potencial_ultima']):g}★ desde la captura anterior."
    if edad >= r.get("edad_veterano", 30) and (margen <= 0 or (evo and (evo["calidad"] or 0) < 0)):
        return "VENDER YA", f"{edad} años y sin margen de mejora ({estrellas}): vender mientras vale ~{fmt_euros(valor)}."
    if hay_nota and j["nota"] < r.get("nota_minima", 6.6):
        return "VENDER YA", f"Nota media {j['nota']:g} en {int(j['partidos'])} partidos: no rinde."
    renovable = edad <= r.get("edad_joven", 23) and pot >= r.get("potencial_renovar_joven", 3.5)
    if meses is not None and meses <= 12 and valor >= r.get("valor_minimo_venta", 50000) and not renovable:
        return "VENDER YA", f"Último año de contrato (acaba {fin}) y vale ~{fmt_euros(valor)}: vender antes del {limite} o se irá gratis."
    if edad >= r.get("edad_pico", 27) and margen <= 0 and valor >= r.get("valor_minimo_venta", 50000):
        return "VENDER YA", f"En su pico ({edad} años, {estrellas}) y vale ~{fmt_euros(valor)}: es el mejor momento para vender."

    # ---------------- SALE LIBRE (techo bajo)
    if pot <= r.get("techo_bajo", 2.5) and (edad >= 20 or (meses is not None and meses <= 12)):
        if meses is not None and meses <= 12:
            return "SALE LIBRE", f"Techo bajo ({estrellas}) a los {edad} años: no renovar, sale libre el {fin}."
        return "SALE LIBRE", f"Techo bajo ({estrellas}) a los {edad} años: buscarle salida, contrato hasta {fin}."

    # ---------------- CEDER (joven con potencial y pocos minutos)
    otros_grupos = p.grupos_de.get(j["jugador"], set()) - {j["grupo"]}
    juega_en_b = "B" in p.codigos_inf(j)  # Inf "B" = tiene minutos en el filial
    pocos_minutos, fuente = False, ""
    if j["minutos"] is not None:
        pocos_minutos = j["minutos"] < r.get("minutos_minimos_temporada", 900)
        fuente = f"{int(j['minutos'])} minutos"
    elif p.partidos_con_once >= r.get("partidos_minimos_minutos", 4):
        # Con alineaciones guardadas: pocos minutos = titular en menos de un tercio de los partidos
        tit = p.titularidades.get(j["jugador"], 0)
        pocos_minutos = tit / p.partidos_con_once < r.get("proporcion_titular_minima", 0.34)
        fuente = f"titular en {tit} de {p.partidos_con_once} partidos"
    elif j["grupo"] == "primer-equipo" and j["estado"] in (r.get("estados_pocos_minutos") or []):
        pocos_minutos = True
        fuente = f"estado «{j['estado']}», sin datos de minutos"
    if (not cedido_fuera and j["grupo"] == "primer-equipo" and not otros_grupos and not juega_en_b and pocos_minutos
            and edad <= r.get("edad_max_cesion", 21) and pot >= r.get("potencial_cesion", 3.5)):
        extra = f" Renuévalo antes de cederlo (acaba {fin})." if meses is not None and meses <= r.get("meses_para_renovar", 18) else ""
        return "CEDER", f"{edad} años, {estrellas} y pocos minutos ({fuente}): necesita jugar fuera.{extra}"

    # ---------------- RENOVAR
    if meses is not None and meses <= r.get("meses_para_renovar", 18):
        anios = " (solo 1 año)" if edad > p.cfg.get("edad_max_renovar_largo", 30) else ""
        if renovable:
            return "RENOVAR", f"Joven ({edad}) con potencial {texto_potencial(j)}★ y contrato hasta {fin}: renovar antes del {limite}{anios}."
        titular = j["estado"] in (p.cfg.get("estados_titular") or [])
        nivel = p.mediana_calidad.get(j["grupo"]) or 0
        rinde = (j["nota"] >= r.get("nota_minima", 6.6)) if hay_nota else cal >= nivel
        if titular and rinde:
            base = f"nota {j['nota']:g}" if hay_nota else f"{cal:g}★, sin nota media"
            return "RENOVAR", f"Titular ({j['estado']}, {base}) y acaba {fin}: renovar antes del {limite}{anios}."
        if meses <= 12:
            return "SALE LIBRE", f"No cumple los criterios de renovación ({edad} años, {estrellas}) y acaba {fin}: dejarle salir o venderle si llega oferta."

    # ---------------- MANTENER
    if juega_en_b:
        return "MANTENER", f"{estrellas}, ya suma minutos con el B: no hace falta cederlo. Contrato hasta {fin}."
    if cedido_fuera:
        return "MANTENER", f"Cedido en otro club; {estrellas}, contrato hasta {fin}."
    return "MANTENER", f"{estrellas}, contrato hasta {fin}: sin acción necesaria ahora."


def cobertura(p):
    """Jugadores del primer equipo que pueden jugar en cada posición de la táctica."""
    filas = []
    primer = p.unicos(["primer-equipo"])
    for pos_txt in p.cfg.get("posiciones_tactica") or []:
        objetivo = posiciones(pos_txt)
        naturales = [j for j in primer if posiciones(j["mejor_pos"]) & objetivo]
        otros = [j for j in primer if j not in naturales and posiciones(j["posicion"]) & objetivo]
        # Los cedidos a nuestro club no cuentan como cobertura de futuro
        propios = [j for j in naturales if not p.es_cedido_aqui(j)]
        cals = sorted((j["calidad"] or 0 for j in propios), reverse=True)
        nivel = "rojo" if len(propios) < 2 or (not cals or cals[0] < (p.mediana_calidad["primer-equipo"] or 0)) else ""
        filas.append({
            "Posición": pos_txt,
            "Nº naturales (propios)": len(propios),
            "Jugadores (mejor posición)": ", ".join(
                f"{j['jugador']} {j['calidad']:g}★/{texto_potencial(j)}★" + (" (CEDIDO)" if p.es_cedido_aqui(j) else "")
                for j in sorted(naturales, key=lambda x: -(x["calidad"] or 0))),
            "También pueden jugar": ", ".join(j["jugador"] for j in otros),
            "_nivel": nivel,
        })
    return filas


def generar(p, carpeta):
    inf = Informe("plantilla", f"Recomendaciones de plantilla · {p.cfg.get('club', '')}", p.fecha)
    faltan = falta(p.columnas | ({"nota", "partidos"} if p.fuente_nota else set()), ["nota", "minutos", "partidos"])
    if p.fuente_nota:
        inf.texto(f"Nota media y partidos: de las {p.fuente_nota}. Solo cuentan para VENDER/RENOVAR a partir de "
                  f"{p.cfg.get('recomendaciones', {}).get('partidos_minimos_nota', 5)} titularidades.")
    if faltan:
        inf.aviso("Datos que no salen en las capturas: " + ", ".join(NOMBRE_DATO[d] for d in faltan)
                  + ". El rendimiento se mide por estrellas de calidad y los minutos, por el «Tiempo de juego».")
    if p.cfg.get("criterio_potencial", "media") != "minimo":
        inf.texto(f"Potencial con rango (estrellas blancas): uso el criterio «{p.cfg.get('criterio_potencial', 'media')}» de config.yaml.")

    filas = []
    for j in p.unicos():
        accion, motivo = recomendar(p, j)
        filas.append({
            "Acción": accion, "Jugador": j["jugador"], "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]),
            "Edad": j["edad"], "Pos.": j["mejor_pos"] or j["posicion"], "Calidad": j["calidad"],
            "Potencial": texto_potencial(j), "Tiempo de juego": j["estado"], "Inf": p.inf_texto(j), "Fin contrato": fmt_fecha(j["fin"]),
            "Sueldo (€)": j["sueldo"], "Valor máx. (€)": j["valor_max"], "Motivo": motivo,
            "_nivel": NIVEL_ACCION.get(accion, ""),
        })
    filas.sort(key=lambda f: (ORDEN_ACCION.index(f["Acción"]), f["Equipo"], f["Jugador"]))

    inf.seccion("Resumen")
    inf.lista(f"**{a}**: {sum(f['Acción'] == a for f in filas)}" for a in ORDEN_ACCION
              if any(f["Acción"] == a for f in filas))
    columnas = ["Acción", "Jugador", "Equipo", "Edad", "Pos.", "Calidad", "Potencial", "Tiempo de juego", "Inf",
                "Fin contrato", "Sueldo (€)", "Motivo"]
    for accion in ORDEN_ACCION:
        grupo = [f for f in filas if f["Acción"] == accion]
        if grupo:
            inf.seccion(accion)
            inf.tabla(accion.title(), columnas[1:], grupo)

    inf.seccion("Cobertura de posiciones (primer equipo)")
    inf.texto("En rojo: menos de 2 jugadores naturales propios (los cedidos no cuentan), o el mejor propio está por debajo de la calidad mediana del primer equipo "
              f"({p.mediana_calidad['primer-equipo']:g}★). Sirve para decidir qué reforzar en enero.")
    inf.tabla("Cobertura", ["Posición", "Nº naturales (propios)", "Jugadores (mejor posición)", "También pueden jugar"], cobertura(p))
    return inf.guardar(carpeta)
