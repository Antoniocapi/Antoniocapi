"""Analítica de equipo y de jugador (Centro de datos del FM) frente a la media de la liga."""

from pathlib import Path

from .datos import fecha, leer_csv, numero
from .salida import Informe

# Qué significa cada métrica y si es mejor alta (+1), baja (-1) o depende del estilo (0)
METRICAS = {
    "% Pase": ("Precisión de pase", +1),
    "% ent": ("Entradas ganadas (%)", +1),
    "Gol/Par": ("Goles marcados por partido", +1),
    "xG- Sp/90": ("xG sin penaltis por 90'", +1),
    "Enc/Par": ("Goles encajados por partido", -1),
    "xGC/Par": ("xG concedido por partido", -1),
    "Dis/Par": ("Disparos por partido", +1),
    "% disparos": ("Disparos a puerta (%)", +1),
    "Fal R/Par": ("Faltas recibidas por partido", 0),
    "Reg/Par": ("Regates por partido", +1),
    "% Cen": ("Precisión de centros", +1),
    "1/3 final pas con/par": ("Pases en el último tercio (según el FM)", 0),
    "Fal/Par": ("Faltas cometidas por partido", -1),
    "Imb": ("Imb (sin confirmar qué mide)", 0),
    "PRPAD": ("Pases rivales por acción defensiva (más bajo = más presión)", 0),
    "Pos gan/par": ("Posesiones ganadas por partido", +1),
    "Centros rivales ABP/par (aprox.)": ("Centros del rival a balón parado por partido", -1),
    "xA rival ABP/par (aprox.)": ("xA del rival a balón parado por partido", -1),
    "Acciones def./par": ("Acciones defensivas por partido", 0),
    "Acc. def. zona 1 - propia área (%)": ("% de acciones defensivas junto a nuestra área", 0),
    "Acc. def. zona 2 (%)": ("% de acciones defensivas, zona 2", 0),
    "Acc. def. zona 3 (%)": ("% de acciones defensivas, zona 3", 0),
    "Acc. def. zona 4 (%)": ("% de acciones defensivas, zona 4", 0),
    "Acc. def. zona 5 (%)": ("% de acciones defensivas, zona 5", 0),
    "Acc. def. zona 6 - área rival (%)": ("% de acciones defensivas junto al área rival", 0),
    "Cabezazos intentados/90 (aprox.)": ("Balones aéreos disputados por 90'", 0),
    "% cabezazos ganados (aprox.)": ("% de balones aéreos ganados", +1),
    # jugador
    "Desp/90": ("Despejes por 90'", +1),
    "Cab 90": ("Cabezazos ganados por 90'", +1),
    "Entr/90": ("Entradas por 90'", +1),
    "Rob/90": ("Robos por 90'", +1),
    "Fal C": ("Faltas cometidas", -1),
    "Rech/90": ("Rechaces/bloqueos por 90'", +1),
}


def _ultimo(carpeta, prefijo):
    archivos = sorted(Path(carpeta).glob(f"{prefijo}_*.csv"))
    return archivos


def _valoracion(metrica, nuestro, media, margen=0.05):
    """Compara con la media: 'mejor', 'peor' o 'en la media' (±10 %)."""
    if nuestro is None or media is None:
        return "", ""
    sentido = METRICAS.get(metrica, ("", 0))[1]
    dif = (nuestro - media) / abs(media) if media else 0
    if sentido == 0:
        return "estilo", ""
    if abs(dif) <= margen:
        return "en la media", ""
    mejor = (dif > 0) == (sentido > 0)
    return ("mejor", "verde") if mejor else ("peor", "rojo")


def _tabla(filas_csv, col_valor, col_media):
    filas = []
    for f in filas_csv:
        m = f.get("Métrica", "")
        v, med = numero(f.get(col_valor)), numero(f.get(col_media))
        texto, nivel = _valoracion(m, v, med)
        filas.append({"Bloque": f.get("Bloque", ""), "Métrica": m, "Qué es": METRICAS.get(m, ("?", 0))[0],
                      "Nosotros": v, "Media": med,
                      "Diferencia": None if v is None or med is None else round(v - med, 2),
                      "Valoración": texto, "_nivel": nivel})
    return filas


def generar(carpeta_analitica, cfg, carpeta, partidos=None):
    equipos = _ultimo(carpeta_analitica, "equipo")
    if not equipos:
        return None
    ruta = equipos[-1]
    _, filas_csv = leer_csv(ruta)
    inf = Informe("equipo", f"Analítica de equipo · {cfg.get('club', '')}", fecha(ruta.stem.split("_")[-1]),
                  "Centro de datos del FM: media por partido de la temporada frente a la media de la liga")
    datos = {f["Métrica"]: numero(f.get("Salamanca")) for f in filas_csv}
    medias = {f["Métrica"]: numero(f.get("Media 2F5")) for f in filas_csv}

    # Lectura "modelo Castellón": juego (xG) frente a resultados (goles)
    inf.seccion("Juego frente a resultados (xG)")
    xg, xgc = datos.get("xG- Sp/90"), datos.get("xGC/Par")
    gf, gc = datos.get("Gol/Par"), datos.get("Enc/Par")
    if None not in (xg, xgc, gf, gc):
        dif_xg, dif_goles = round(xg - xgc, 2), round(gf - gc, 2)
        suerte = round(dif_goles - dif_xg, 2)
        inf.lista([
            f"Diferencia de xG por partido: **{dif_xg:+g}** (creamos {xg:g}, concedemos {xgc:g}).",
            f"Diferencia de goles por partido: **{dif_goles:+g}** (marcamos {gf:g}, encajamos {gc:g}).",
            ("Los resultados son **mejores** que el juego" if suerte > 0 else "Los resultados son **peores** que el juego"
             if suerte < 0 else "Los resultados reflejan el juego") + f" ({suerte:+g} goles por partido): "
            + ("esperar una regresión a la baja si no mejora el xG." if suerte > 0 else
               "deberían llegar mejores resultados si se mantiene el xG." if suerte < 0 else "sin sorpresas."),
        ])
        inf.texto("Ojo: el xG a favor del FM es sin penaltis y por 90'; con pocos partidos jugados, las medias aún bailan mucho.")
    else:
        inf.aviso("Faltan xG, xGC, goles o encajados en la captura: no puedo comparar juego y resultados.")

    inf.seccion("Métricas frente a la media de la liga")
    inf.texto("Valoración: «mejor/peor» si nos separamos más de un 5 % de la media; «estilo» = depende del plan de juego "
              "(un bloque medio de contraataque presiona menos, así que un PRPAD alto es esperable).")
    inf.texto("«(aprox.)» = valor leído a ojo en un gráfico de dispersión del FM (margen de ±0,3 en centros, ±0,01 en xA, "
              "±0,3 en cabezazos y ±2 puntos en %).")
    inf.tabla("Equipo", ["Bloque", "Métrica", "Qué es", "Nosotros", "Media", "Diferencia", "Valoración"],
              _tabla(filas_csv, "Salamanca", "Media 2F5"))

    # Evolución si hay varias capturas
    if len(equipos) > 1:
        _, previas = leer_csv(equipos[-2])
        antes = {f["Métrica"]: numero(f.get("Salamanca")) for f in previas}
        inf.seccion(f"Cambio desde {fecha(equipos[-2].stem.split('_')[-1]).strftime('%d/%m/%Y')}")
        inf.tabla("Evolución", ["Métrica", "Antes", "Ahora", "Cambio"], [
            {"Métrica": m, "Antes": antes.get(m), "Ahora": v,
             "Cambio": None if v is None or antes.get(m) is None else round(v - antes[m], 2)}
            for m, v in datos.items()])

    # Analítica de jugadores
    jugadores = _ultimo(carpeta_analitica, "jugador")
    if jugadores:
        _, filas_j = leer_csv(jugadores[-1])
        inf.seccion("Analítica de jugadores (frente a la media de su rol en la liga)")
        for nombre in sorted({f.get("Jugador", "") for f in filas_j}):
            inf.texto(f"**{nombre}**")
            inf.tabla(nombre, ["Métrica", "Qué es", "Nosotros", "Media", "Diferencia", "Valoración"],
                      _tabla([f for f in filas_j if f.get("Jugador") == nombre], "Valor", "Media"))
    return inf.guardar(carpeta)
