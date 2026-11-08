"""Piezas comunes a todos los informes: configuración, base de datos y contexto de la plantilla."""

from pathlib import Path

import yaml

from . import bd
from .datos import mediana, potencial

RAIZ = Path(__file__).resolve().parent.parent
ORDEN_GRUPOS = {"primer-equipo": 0, "filial": 1, "juvenil": 2}
NOMBRE_GRUPO = {"primer-equipo": "Primer equipo", "filial": "Filial", "juvenil": "Juvenil"}


def cargar_config(ruta=None):
    with open(ruta or RAIZ / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def abrir_bd(cfg, mostrar=print):
    """Abre la base de datos e importa los CSV nuevos antes de cada informe."""
    conn = bd.conectar(RAIZ / "fm.db")
    for m in bd.importar(conn, RAIZ / "data"):
        mostrar(m)
    return conn


class Plantilla:
    """Estado actual de la plantilla, con todo lo que necesitan los informes."""

    def __init__(self, conn, cfg):
        self.cfg = cfg
        alias = cfg.get("alias_columnas") or {}
        self.jugadores = sorted(bd.estado_actual(conn, "plantilla", alias),
                                key=lambda j: (ORDEN_GRUPOS.get(j["grupo"], 9), j["jugador"]))
        self.fecha = max((j["fecha_juego"] for j in self.jugadores), default=None)
        # Historial completo, para ver evolución
        self._historial = {}
        for j in bd.historial(conn, alias):
            self._historial.setdefault(j["jugador"], []).append(j)
        # Grupos en los que aparece cada jugador (p. ej. alguien inscrito en primer equipo y filial)
        self.grupos_de = {}
        for j in self.jugadores:
            self.grupos_de.setdefault(j["jugador"], set()).add(j["grupo"])
        # Calidad mediana de cada equipo (sirve de referencia de nivel)
        self.mediana_calidad = {
            g: mediana(j["calidad"] for j in self.jugadores if j["grupo"] == g)
            for g in ORDEN_GRUPOS
        }
        # Columnas disponibles en total
        self.columnas = set().union(*(j["columnas"] for j in self.jugadores)) if self.jugadores else set()

    def pot(self, j):
        return potencial(j, self.cfg.get("criterio_potencial", "media"))

    def unicos(self, grupos=None):
        """Un registro por jugador (si sale en dos equipos, el primero: primer equipo > filial > juvenil)."""
        vistos, res = set(), []
        for j in self.jugadores:
            if grupos and j["grupo"] not in grupos:
                continue
            if j["jugador"] in vistos:
                continue
            vistos.add(j["jugador"])
            res.append(j)
        return res

    def historial(self, nombre):
        return self._historial.get(nombre, [])

    def evolucion(self, j):
        """Cambio de calidad y potencial desde la primera captura (None si solo hay una)."""
        h = [x for x in self.historial(j["jugador"]) if x["fecha_juego"] < j["fecha_juego"]]
        if not h:
            return None
        primero = h[0]
        anterior = h[-1]

        def dif(a, b):
            return None if a is None or b is None else round(a - b, 2)

        return {
            "desde": primero["fecha_juego"],
            "calidad": dif(j["calidad"], primero["calidad"]),
            "potencial": dif(self.pot(j), self.pot(primero)),
            "potencial_ultima": dif(self.pot(j), self.pot(anterior)),
            "calidad_ultima": dif(j["calidad"], anterior["calidad"]),
            "valor": dif(j["valor_max"], primero["valor_max"]),
        }

    def es_cedido_aqui(self, j):
        return j["jugador"] in (self.cfg.get("cedidos_a_nuestro_club") or [])

    def rol_salarial(self, j):
        """titular | rotacion | filial_proyecto, según equipo y 'Tiempo de juego'."""
        if j["grupo"] != "primer-equipo":
            return "filial_proyecto"
        if j["estado"] in (self.cfg.get("estados_titular") or []):
            return "titular"
        if j["estado"] in (self.cfg.get("estados_proyecto") or []):
            return "filial_proyecto"
        return "rotacion"

    def tope(self, j):
        return (self.cfg.get("topes_sueldo") or {}).get(self.rol_salarial(j))


ROL_TEXTO = {"titular": "titular", "rotacion": "rotación", "filial_proyecto": "filial/proyecto"}


def falta(columnas, datos):
    """Devuelve los datos de la lista que NO están en las capturas."""
    return [d for d in datos if d not in columnas]


NOMBRE_DATO = {
    "clausula": "Cláusula de rescisión",
    "futura_venta": "Porcentaje de futura venta",
    "nota": "Nota media",
    "partidos": "Partidos jugados",
    "minutos": "Minutos jugados",
    "amarillas": "Tarjetas amarillas",
    "rojas": "Tarjetas rojas",
    "entrenamiento": "Valoración de entrenamiento",
    "recomendacion": "Recomendación del ojeador",
    "situacion": "Situación (libre / cedible / transferible)",
    "club": "Club",
    "xg": "xG",
}
