"""Informe de analista: el análisis escrito de data/analisis/analisis.csv y lo que hace falta para profundizar."""

from .comun import RAIZ
from .datos import leer_csv
from .salida import Informe


def generar(p, carpeta):
    ruta = RAIZ / "data" / "analisis" / "analisis.csv"
    if not ruta.exists():
        return None
    _, filas = leer_csv(ruta)
    inf = Informe("analisis", f"Informe de analista · {p.cfg.get('club', '')}", p.fecha,
                  "Lectura completa de las jornadas jugadas")
    bloque = None
    for f in sorted(filas, key=lambda x: int(x["orden"])):
        if f["bloque"] != bloque:
            bloque = f["bloque"]
            inf.seccion(bloque)
        inf.texto(f"**{f['titulo']}.** {f['texto']}" + (f"\n\n→ *Qué hacer:* {f['accion']}" if f.get("accion") else ""))
    ruta_n = RAIZ / "data" / "analisis" / "necesito.csv"
    if ruta_n.exists():
        _, nec = leer_csv(ruta_n)
        inf.seccion("Para profundizar: capturas que necesito")
        inf.tabla("Necesito", ["Captura", "Dónde", "Para qué"],
                  [{"Captura": n["captura"], "Dónde": n["donde"], "Para qué": n["para_que"]} for n in nec])
    return inf.guardar(carpeta)
