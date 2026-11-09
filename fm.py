"""Herramienta de gestión de la partida de FM27 · Salamanca CF UDS.

Uso:  python fm.py <comando>
  importar     Guarda en la base de datos los CSV nuevos de data/plantilla y data/ojeo
  revisar      Dice qué datos hay en las capturas y cuáles faltan para cada informe
  contratos    Vencimientos, cláusulas y estructura salarial
  plantilla    Recomendaciones: RENOVAR / VENDER YA / CEDER / SALE LIBRE + cobertura de posiciones
  fichajes     Ranking "modelo Castellón" a partir de las listas de ojeo
  cantera      Jóvenes de 19 años o menos con potencial alto y dónde deben jugar
  partidos     Informe de partidos (data/partidos/partidos.csv)
  disciplina   Amarillas por jugador y quién está cerca del ciclo
  equipo       Analítica del Centro de datos frente a la media de la liga
  panel        Exporta los datos del panel de analista a la carpeta panel/
  evolucion    Evolución de la plantilla (o de un jugador: python fm.py evolucion "Pau Calvo")
  todo         Genera todos los informes
"""

import argparse
import sys

from fmtool import bd
from fmtool.comun import RAIZ, Plantilla, abrir_bd, cargar_config
from fmtool import (inf_cantera, inf_contratos, inf_disciplina, inf_equipo, inf_evolucion, inf_fichajes,
                    inf_partidos, inf_plantilla)
from fmtool.comun import NOMBRE_DATO

INFORMES = RAIZ / "informes"
CSV_PARTIDOS = RAIZ / "data" / "partidos" / "partidos.csv"


def avisar_guardado(rutas):
    for r in rutas:
        print(f"  → {r.relative_to(RAIZ)}")


def plantilla_o_salir(conn, cfg):
    p = Plantilla(conn, cfg)
    if not p.jugadores:
        sys.exit("No hay datos de plantilla. Pon los CSV en data/plantilla/ (formato grupo_vista_AAAA-MM-DD.csv).")
    return p


def cmd_revisar(conn, cfg):
    print("\nArchivos importados:")
    for r in bd.resumen_importaciones(conn):
        print(f"  [{r['tipo']}] {r['grupo']:<15} {r['vista'] or '-':<22} {r['fecha_juego']}  {r['filas']} filas")
    p = Plantilla(conn, cfg)
    necesita = {
        "contratos": ["fin_contrato", "sueldo", "clausula", "futura_venta", "nota"],
        "plantilla": ["calidad", "potencial", "fin_contrato", "nota", "minutos", "partidos"],
        "cantera": ["calidad", "potencial", "entrenamiento"],
        "disciplina": ["amarillas", "rojas"],
    }
    print("\nDatos que faltan en la plantilla, por informe:")
    for informe, datos in necesita.items():
        faltan = [NOMBRE_DATO.get(d, d) for d in datos if d not in p.columnas]
        print(f"  {informe:<11} " + ("todo disponible" if not faltan else "faltan: " + ", ".join(faltan)))
    ojeo = bd.estado_actual(conn, "ojeo")
    print(f"\nOjeo: {len(ojeo)} jugadores." if ojeo else "\nOjeo: sin listas todavía (data/ojeo/).")
    print("Partidos: " + ("hay archivo partidos.csv" if CSV_PARTIDOS.exists() else "falta data/partidos/partidos.csv"))


def main():
    parser = argparse.ArgumentParser(description="Gestión de la partida de FM27", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=__doc__)
    parser.add_argument("comando", choices=["importar", "revisar", "contratos", "plantilla", "fichajes", "cantera",
                                            "partidos", "disciplina", "equipo", "evolucion", "panel", "todo"])
    parser.add_argument("jugador", nargs="?", help="(solo evolucion) nombre del jugador")
    args = parser.parse_args()

    cfg = cargar_config()
    conn = abrir_bd(cfg)
    c = args.comando
    todo = c == "todo"

    if c == "importar":
        print("Base de datos al día.")
    if c == "revisar":
        cmd_revisar(conn, cfg)
    if c in ("contratos", "plantilla", "cantera", "disciplina", "evolucion") or todo:
        p = plantilla_o_salir(conn, cfg)
        if c == "contratos" or todo:
            print("Informe de contratos:"); avisar_guardado(inf_contratos.generar(p, INFORMES))
        if c == "plantilla" or todo:
            print("Recomendaciones de plantilla:"); avisar_guardado(inf_plantilla.generar(p, INFORMES))
        if c == "cantera" or todo:
            print("Cantera:"); avisar_guardado(inf_cantera.generar(p, INFORMES))
        if c == "disciplina" or todo:
            print("Disciplina:"); avisar_guardado(inf_disciplina.generar(p, INFORMES))
        if c == "evolucion" or todo:
            rutas, parecidos = inf_evolucion.generar(p, INFORMES, None if todo else args.jugador)
            if rutas:
                print("Evolución:"); avisar_guardado(rutas)
            else:
                print(f"No encuentro a «{args.jugador}»." + (f" ¿Quizás: {', '.join(parecidos)}?" if parecidos else ""))
    if c == "fichajes" or todo:
        p = Plantilla(conn, cfg)
        rutas = inf_fichajes.generar(conn, cfg, p, INFORMES)
        if rutas:
            print("Ranking de fichajes:"); avisar_guardado(rutas)
        else:
            print("Fichajes: no hay listas de ojeo en data/ojeo/ todavía.")
    if c == "panel" or todo:
        from fmtool import exportar_panel
        print("Datos del panel:")
        avisar_guardado(exportar_panel.exportar(Plantilla(conn, cfg), cfg))
    if c == "equipo" or todo:
        cmd_equipo(cfg)
    if c == "partidos" or todo:
        if not CSV_PARTIDOS.exists():
            print(f"Partidos: falta {CSV_PARTIDOS.relative_to(RAIZ)}.")
        else:
            rutas, errores = inf_partidos.generar(CSV_PARTIDOS, cfg, INFORMES, RAIZ / "data" / "liga")
            for e in errores:
                print("AVISO:", e)
            if rutas:
                print("Partidos:"); avisar_guardado(rutas)
            else:
                print("Partidos: el CSV no tiene partidos todavía.")


def cmd_equipo(cfg):
    rutas = inf_equipo.generar(RAIZ / "data" / "analitica", cfg, INFORMES)
    if rutas:
        print("Analítica de equipo:"); avisar_guardado(rutas)
    else:
        print("Equipo: no hay capturas de analítica en data/analitica/ todavía.")


if __name__ == "__main__":
    main()
