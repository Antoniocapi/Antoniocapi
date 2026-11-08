"""Informe de contratos: vencimientos, cláusulas y estructura salarial."""

from .comun import NOMBRE_GRUPO, NOMBRE_DATO, ROL_TEXTO, falta
from .datos import (fecha_limite_renovacion, fmt_euros, fmt_fecha, mediana, meses_entre,
                    texto_potencial, valor_estimado)
from .inf_plantilla import recomendar
from .salida import Informe


def generar(p, carpeta):
    cfg = p.cfg
    inf = Informe("contratos", f"Contratos · {cfg.get('club', '')}", p.fecha)
    jugadores = [j for j in p.unicos() if not p.es_cedido_aqui(j)]

    # ------------------------------------------------ 1. Vencimientos
    inf.seccion(f"Contratos con {cfg.get('meses_alerta_contrato', 18)} meses o menos")
    inf.texto("Regla: renovar antes del 1 de enero de su último año (cuando ya puede firmar un precontrato) o venderlo antes.")
    filas = []
    for j in jugadores:
        meses = meses_entre(p.fecha, j["fin"])
        if meses is None or meses > cfg.get("meses_alerta_contrato", 18):
            continue
        limite = fecha_limite_renovacion(j["fin"])
        dias = (limite - p.fecha).days if limite else None
        accion, motivo = recomendar(p, j)
        nivel = "rojo" if dias is not None and dias <= 120 else "naranja"
        filas.append({
            "Jugador": j["jugador"], "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Edad": j["edad"],
            "Calidad": j["calidad"], "Potencial": texto_potencial(j), "Tiempo de juego": j["estado"],
            "Inf": p.inf_texto(j),
            "Fin contrato": fmt_fecha(j["fin"]), "Meses": meses, "Límite renovar/vender": fmt_fecha(limite),
            "Días hasta límite": dias, "Sueldo (€)": j["sueldo"], "Valor estimado (€)": valor_estimado(j),
            "Recomendación": accion, "Motivo": motivo, "_nivel": nivel,
        })
    filas.sort(key=lambda f: (f["Días hasta límite"] if f["Días hasta límite"] is not None else 9999, f["Jugador"]))
    inf.texto(f"🔴 = quedan 120 días o menos para el límite. Total: {len(filas)} jugadores.")
    inf.tabla("Vencimientos", ["Jugador", "Equipo", "Edad", "Calidad", "Potencial", "Inf", "Fin contrato", "Meses",
                               "Límite renovar/vender", "Días hasta límite", "Sueldo (€)", "Valor estimado (€)",
                               "Recomendación", "Motivo"], filas)
    mayores = [f["Jugador"] for f in filas if (f["Edad"] or 0) > cfg.get("edad_max_renovar_largo", 30)]
    if mayores:
        inf.aviso("Mayores de " + str(cfg.get("edad_max_renovar_largo", 30)) + " años: si renuevas, solo 1 año → " + ", ".join(mayores))

    # ------------------------------------------------ 2. Cláusulas
    inf.seccion("Cláusulas de rescisión bajas (potencial 4★ o más)")
    if "clausula" not in p.columnas:
        inf.aviso("La columna «Cláusula de rescisión» no sale en las capturas. Añádela a la vista "
                  "(o pásame la vista de Contratos) y este apartado se activará solo.")
    else:
        filas = []
        for j in jugadores:
            pot = p.pot(j)
            if pot is None or pot < 4:
                continue
            clausula = j["clausula"]
            if clausula is None:
                motivo, nivel = "Sin cláusula visible", "naranja"
            elif clausula < cfg.get("clausula_minima", 500000) or (j["valor_max"] and clausula < j["valor_max"]):
                motivo, nivel = "Cláusula baja: cualquiera puede pagarla", "rojo"
            else:
                continue
            filas.append({"Jugador": j["jugador"], "Edad": j["edad"], "Potencial": texto_potencial(j),
                          "Cláusula (€)": clausula, "Valor máx. (€)": j["valor_max"], "Alerta": motivo, "_nivel": nivel})
        inf.tabla("Cláusulas", ["Jugador", "Edad", "Potencial", "Cláusula (€)", "Valor máx. (€)", "Alerta"], filas,
                  "Ningún jugador de 4★ o más tiene la cláusula baja.")

    if "futura_venta" not in p.columnas:
        inf.aviso("El «Porcentaje de futura venta» no sale en las capturas: no puedo revisarlo.")

    # ------------------------------------------------ 3. Estructura salarial
    inf.seccion("Estructura salarial")
    faltan = falta(p.columnas, ["nota"])
    if faltan:
        inf.aviso("Sin «Nota media» en las capturas: el rendimiento se mide por estrellas de calidad, no por nota.")
    topes = cfg.get("topes_sueldo") or {}
    inf.texto("Topes: " + ", ".join(f"{ROL_TEXTO.get(k, k)} {fmt_euros(v)}" for k, v in topes.items()) + ".")

    primer = [j for j in jugadores if j["grupo"] == "primer-equipo" and j["sueldo"]]
    eur_estrella = mediana(j["sueldo"] / j["calidad"] for j in primer if j["calidad"])
    sueldo_p75 = sorted(j["sueldo"] for j in primer)[int(len(primer) * 0.75)] if primer else None
    filas = []
    for j in jugadores:
        if not j["sueldo"]:
            continue
        tope = p.tope(j)
        alertas = []
        if tope and j["sueldo"] > tope:
            alertas.append(f"supera el tope de {ROL_TEXTO[p.rol_salarial(j)]} en {fmt_euros(j['sueldo'] - tope)}")
        ratio = None
        if j["grupo"] == "primer-equipo" and j["calidad"] and eur_estrella:
            ratio = round(j["sueldo"] / j["calidad"] / eur_estrella, 2)
            if ratio >= 1.5:
                alertas.append(f"cobra {ratio:g} veces lo normal para sus {j['calidad']:g}★")
        if (j["edad"] or 0) >= 28 and sueldo_p75 and j["sueldo"] >= sueldo_p75 and (p.pot(j) or 0) <= (j["calidad"] or 0):
            alertas.append(f"{j['edad']} años, de los sueldos más altos y sin margen de mejora")
        if j["nota"] is not None and j["nota"] < cfg.get("recomendaciones", {}).get("nota_minima", 6.6) and tope and j["sueldo"] > tope * 0.75:
            alertas.append(f"nota media {j['nota']:g} para un sueldo alto")
        filas.append({
            "Jugador": j["jugador"], "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Edad": j["edad"],
            "Calidad": j["calidad"], "Potencial": texto_potencial(j), "Rol salarial": ROL_TEXTO[p.rol_salarial(j)],
            "Sueldo (€)": j["sueldo"], "Tope (€)": tope, "Índice €/estrella": ratio,
            "Alerta": "; ".join(alertas), "_nivel": "rojo" if len(alertas) >= 2 else ("naranja" if alertas else ""),
        })
    filas.sort(key=lambda f: -(f["Sueldo (€)"] or 0))
    inf.texto("Índice €/estrella: 1 = lo que cobra de media el primer equipo por cada estrella de calidad; 1,5 o más = caro.")
    inf.tabla("Salarios", ["Jugador", "Equipo", "Edad", "Calidad", "Potencial", "Rol salarial", "Sueldo (€)",
                           "Tope (€)", "Índice €/estrella", "Alerta"], filas)

    # Masa salarial
    inf.seccion("Masa salarial")
    masas = {}
    for j in jugadores:
        masas[j["grupo"]] = masas.get(j["grupo"], 0) + (j["sueldo"] or 0)
    filas_masa = [{"Equipo": NOMBRE_GRUPO.get(g, g), "Masa salarial (€)": v} for g, v in masas.items()]
    total = sum(masas.values())
    filas_masa.append({"Equipo": "TOTAL", "Masa salarial (€)": total})
    inf.tabla("Masa salarial", ["Equipo", "Masa salarial (€)"], filas_masa)
    sin_sueldo = [j["jugador"] for j in jugadores if j["sueldo"] is None]
    if sin_sueldo:
        inf.aviso("Sin sueldo en la captura (no sumados): " + ", ".join(sin_sueldo))
    presupuesto = cfg.get("presupuesto_salarial_anual")
    reserva = cfg.get("reserva_enero", 0)
    if presupuesto:
        margen = presupuesto - total - reserva
        inf.texto(f"Presupuesto {fmt_euros(presupuesto)} − masa {fmt_euros(total)} − reserva de enero {fmt_euros(reserva)} "
                  f"= **margen {fmt_euros(margen)}**" + (" ⚠️ NEGATIVO" if margen < 0 else ""))
    else:
        inf.aviso(f"No sé el presupuesto salarial del club (no sale en las capturas). Ponlo en config.yaml "
                  f"(presupuesto_salarial_anual) y calcularé si respetas la reserva de enero de {fmt_euros(reserva)}.")
    return inf.guardar(carpeta)
