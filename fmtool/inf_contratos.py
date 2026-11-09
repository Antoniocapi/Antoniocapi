"""Informe de contratos: vencimientos, cláusulas y estructura salarial."""

from .comun import NOMBRE_GRUPO, NOMBRE_DATO, ROL_TEXTO, falta
from .datos import (fecha_limite_renovacion, fmt_euros, fmt_fecha, mediana, meses_entre,
                    texto_potencial, valor_estimado)
from .inf_plantilla import recomendar
from . import sueldos
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
        nivel = "rojo" if (dias is not None and dias <= 120) or p.le_siguen(j) else "naranja"
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

    # ------------------------------------------------ 1b. Jugadores que siguen otros clubes
    inf.seccion("Jugadores a los que siguen otros clubes")
    filas = []
    for j in jugadores:
        if not p.le_siguen(j):
            continue
        meses = meses_entre(p.fecha, j["fin"])
        accion, motivo = recomendar(p, j)
        pot = p.pot(j) or 0
        riesgo = []
        if meses is not None and meses <= cfg.get("meses_alerta_contrato", 18):
            riesgo.append(f"le quedan {meses:g} meses")
        if "clausula" not in p.columnas or j["clausula"] is None:
            riesgo.append("cláusula desconocida")
        elif j["clausula"] < cfg.get("clausula_minima", 500000):
            riesgo.append("cláusula baja")
        if pot >= 4:
            riesgo.append(f"potencial {texto_potencial(j)}★")
        filas.append({
            "Jugador": j["jugador"], "Equipo": NOMBRE_GRUPO.get(j["grupo"], j["grupo"]), "Edad": j["edad"],
            "Calidad": j["calidad"], "Potencial": texto_potencial(j), "Fin contrato": fmt_fecha(j["fin"]),
            "Cláusula (€)": j["clausula"], "Valor máx. (€)": j["valor_max"], "Riesgo": ", ".join(riesgo),
            "Recomendación": accion, "Motivo": motivo,
            "_nivel": "rojo" if (pot >= 4 or (meses is not None and meses <= 12)) else "naranja",
        })
    filas.sort(key=lambda f: (f["_nivel"] != "rojo", f["Jugador"]))
    inf.texto("🔴 = potencial de 4★ o más, o menos de 12 meses de contrato: hay riesgo de perderle barato.")
    inf.tabla("Les siguen", ["Jugador", "Equipo", "Edad", "Calidad", "Potencial", "Fin contrato", "Cláusula (€)",
                             "Valor máx. (€)", "Riesgo", "Recomendación", "Motivo"], filas, "Nadie marcado con seguimiento.")

    # ------------------------------------------------ 2. Cláusulas
    inf.seccion("Cláusulas de rescisión bajas (potencial 4★ o más)")
    if "clausula" not in p.columnas:
        inf.aviso("La columna «Cláusula de rescisión» no sale en las capturas. Añádela a la vista "
                  "(o pásame la vista de Contratos) y este apartado se activará solo.")
    else:
        filas, sin_clausula = [], []
        for j in jugadores:
            pot = p.pot(j)
            if pot is None or pot < 4:
                continue
            clausula = j["clausula"]
            if clausula is None:
                sin_clausula.append(j["jugador"])  # "-" en el FM = sin cláusula: no se le puede llevar pagándola
                continue
            if j["valor_max"] and clausula < j["valor_max"]:
                motivo, nivel = "Cláusula POR DEBAJO de su valor de mercado: se lo pueden llevar barato", "rojo"
            elif clausula < cfg.get("clausula_minima", 500000):
                motivo, nivel = f"Cláusula por debajo de {fmt_euros(cfg.get('clausula_minima', 500000))}", "naranja"
            else:
                continue
            if p.le_siguen(j):
                motivo += " · LE SIGUEN OTROS CLUBES"
                nivel = "rojo"
            filas.append({"Jugador": j["jugador"], "Edad": j["edad"], "Potencial": texto_potencial(j),
                          "Cláusula (€)": clausula, "Valor máx. (€)": j["valor_max"], "Alerta": motivo, "_nivel": nivel})
        filas.sort(key=lambda f: (f["_nivel"] != "rojo", (f["Cláusula (€)"] or 0)))
        inf.tabla("Cláusulas", ["Jugador", "Edad", "Potencial", "Cláusula (€)", "Valor máx. (€)", "Alerta"], filas,
                  "Ningún jugador de 4★ o más tiene la cláusula baja.")
        if sin_clausula:
            inf.texto("Sin cláusula (bien protegidos): " + ", ".join(sin_clausula) + ".")
        inf.texto("Solución: renovar subiendo la cláusula o sin cláusula. Prioridad: 🔴 primero.")

    if "futura_venta" not in p.columnas:
        inf.aviso("El «Porcentaje de futura venta» no sale en las capturas: no puedo revisarlo.")

    # ------------------------------------------------ 3. Sueldo frente a rendimiento
    inf.seccion("Sueldo frente a rendimiento")
    inf.texto("Sin topes fijos. Para cada equipo, con su misma masa salarial, el **sueldo justo** es lo que le "
              "correspondería a cada jugador según lo que aporta: calidad, nota media (ajustada por los minutos: con "
              "pocos minutos la nota se acerca a la del equipo), participación y, en menores de 24, margen de mejora. "
              "En el Salamanca B y el juvenil, calidad y potencial. Si un jugador mejora, su sueldo justo sube.")
    inf.texto("«Cobra de más» = más de un 30 % por encima de su sueldo justo; «cobra de menos» = más de un 25 % por "
              "debajo (al renovar pedirá más, y lo merece). Con 4 jornadas, las notas aún pesan poco.")
    salarios = sueldos.calcular(p)
    for grupo in ("primer-equipo", "filial", "juvenil"):
        filas = []
        for j in p.jugadores:
            r = salarios.get((grupo, j["jugador"])) if j["grupo"] == grupo else None
            if not r:
                continue
            filas.append({
                "Puesto": r["puesto"], "Jugador": j["jugador"], "Edad": j["edad"], "Calidad": j["calidad"],
                "Potencial": texto_potencial(j), "Nota": j["nota"], "Minutos": j["minutos"],
                "Sueldo (€)": j["sueldo"], "Sueldo justo (€)": r["sueldo_justo"], "Diferencia": f"{r['diferencia_pct']:+d} %",
                "Valoración": r["valoracion"], "Motivo": sueldos.motivo(j, r),
                "_nivel": "rojo" if r["valoracion"] == "Cobra de más" else ("verde" if r["valoracion"] == "Cobra de menos" else ""),
            })
        filas.sort(key=lambda f: f["Puesto"])
        inf.seccion(f"Sueldo justo · {NOMBRE_GRUPO[grupo]}")
        cols = ["Puesto", "Jugador", "Edad", "Calidad", "Potencial"] + (["Nota", "Minutos"] if grupo == "primer-equipo" else []) + \
               ["Sueldo (€)", "Sueldo justo (€)", "Diferencia", "Valoración", "Motivo"]
        inf.tabla(f"Sueldos {NOMBRE_GRUPO[grupo]}", cols, filas)
    cedidos = [j["jugador"] for j in p.unicos() if p.es_cedido_aqui(j)]
    if cedidos:
        inf.texto("Fuera del cálculo: " + ", ".join(cedidos) + " (cedidos a nuestro club) y los canteranos que figuran también "
                  "en el primer equipo (cobran sueldo de cantera).")

    # Masa salarial
    inf.seccion("Masa salarial")
    masas = {}
    for j in p.unicos():  # aquí sí cuentan los cedidos: también cobran
        masas[j["grupo"]] = masas.get(j["grupo"], 0) + (j["sueldo"] or 0)
    filas_masa = [{"Equipo": NOMBRE_GRUPO.get(g, g), "Masa salarial (€)": v} for g, v in masas.items()]
    total = sum(masas.values())
    filas_masa.append({"Equipo": "TOTAL", "Masa salarial (€)": total})
    inf.tabla("Masa salarial", ["Equipo", "Masa salarial (€)"], filas_masa)
    sin_sueldo = [j["jugador"] for j in p.unicos() if j["sueldo"] is None]
    if sin_sueldo:
        inf.aviso("Sin sueldo en la captura (no sumados): " + ", ".join(sin_sueldo))
    ps = cfg.get("presupuesto_sueldos") or {}
    reserva = cfg.get("reserva_enero", 0)
    if ps.get("disponible") is not None:
        margen = ps["disponible"] - reserva
        inf.texto(f"Según el FM ({ps.get('fecha', '')}): gasto en sueldos {fmt_euros(ps.get('gasto_actual'))} al año, "
                  f"disponible {fmt_euros(ps['disponible'])}. Restando la reserva de enero ({fmt_euros(reserva)}): "
                  f"**margen para sueldos nuevos {fmt_euros(margen)} al año**" + (" ⚠️ NEGATIVO" if margen < 0 else "") + ".")
        if ps.get("gasto_actual"):
            dif = ps["gasto_actual"] - total
            inf.texto(f"La suma de las capturas ({fmt_euros(total)}) difiere en {fmt_euros(dif)} del gasto que da el FM: "
                      "son sueldos que no veo (jugadores sin sueldo en la captura, cedidos fuera con sueldo compartido, etc.).")
    else:
        inf.aviso(f"No sé el presupuesto salarial (pásame una captura del Portal o rellénalo en config.yaml): "
                  f"no puedo comprobar la reserva de enero de {fmt_euros(reserva)}.")
    return inf.guardar(carpeta)
