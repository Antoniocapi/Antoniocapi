"""Lectura de los CSV y conversión de sus valores (dinero, estrellas, fechas, posiciones)."""

import csv
import re
import unicodedata
from datetime import date

# Para cada dato que usa la herramienta, los títulos de columna que puede tener en el FM.
# Solo se usan si la columna EXISTE en el CSV: si no está, el dato se trata como "no disponible".
ALIAS = {
    "jugador": ["Jugador", "Nombre"],
    "edad": ["Edad"],
    "posicion": ["Posición", "Posiciones"],
    "mejor_pos": ["Mejor pos.", "Mejor posición"],
    "mejor_rol": ["Mejor rol"],
    "calidad": ["Calidad", "Habilidad actual"],
    "potencial": ["Potencial", "Habilidad potencial"],
    "valor": ["Valor de traspaso", "Valor", "Valor de mercado"],
    "sueldo": ["Sueldo", "Salario"],
    "fin_contrato": ["Final", "Fin de contrato", "Expira", "Contrato hasta"],
    "estado": ["Tiempo de juego", "Estado en plantilla"],
    "pais": ["País", "Nacionalidad"],
    "club": ["Club", "Equipo"],
    "clausula": ["Cláusula de rescisión", "Cláusula de rescisión mínima", "Cláusula"],
    "futura_venta": ["Porcentaje de futura venta", "% futura venta", "Futura venta"],
    "nota": ["Nota media", "Nota", "Media de puntuación"],
    "partidos": ["Partidos", "Apariciones", "PJ"],
    "minutos": ["Minutos", "Min.", "Minutos jugados"],
    "amarillas": ["Amarillas", "Tarjetas amarillas", "TA"],
    "rojas": ["Rojas", "Tarjetas rojas", "TR"],
    "xg": ["xG", "Goles esperados"],
    "entrenamiento": ["Valoración de entrenamiento", "Entrenamiento", "Media de entrenamiento"],
    "recomendacion": ["Recomendación", "Recomendación del ojeador", "Rec."],
    "situacion": ["Situación", "Estado de traspaso", "Disponibilidad"],
    "inf": ["Inf"],
    "promesas": ["Promesas"],
    "elegido": ["Elegido"],
}

VACIOS = {"", "-", "n/d", "sin datos", "no disponible", "?"}


def _clave(texto):
    """Normaliza un título: minúsculas y sin tildes, para comparar."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def es_vacio(v):
    return v is None or _clave(v) in VACIOS


# ----------------------------------------------------------------- lectura CSV

def leer_csv(ruta):
    """Lee un CSV (separador ; , o tabulador, detectado solo). Devuelve (columnas, filas)."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        texto = f.read()
    primera = texto.splitlines()[0] if texto else ""
    sep = max([";", ",", "\t"], key=primera.count)
    lector = csv.DictReader(texto.splitlines(), delimiter=sep)
    filas = [dict(f) for f in lector if any((v or "").strip() for v in f.values())]
    return lector.fieldnames or [], filas


def mapa_columnas(columnas, alias_extra=None):
    """Dice qué columna del CSV corresponde a cada dato (jugador, edad...)."""
    alias = {k: list(v) for k, v in ALIAS.items()}
    for k, v in (alias_extra or {}).items():
        alias.setdefault(k, []).extend(v)
    por_clave = {_clave(c): c for c in columnas}
    mapa = {}
    for dato, nombres in alias.items():
        for n in nombres:
            if _clave(n) in por_clave:
                mapa[dato] = por_clave[_clave(n)]
                break
    return mapa


# ----------------------------------------------------------------- conversiones

def dinero(texto):
    """'52m € p/a' -> 52000 ; '52000' -> 52000 ; '1,5M €' -> 1500000.
    En el FM en español, 'm' = miles y 'M' = millones."""
    if es_vacio(texto):
        return None
    t = str(texto).replace("€", "").replace("p/a", "").replace("p...", "").strip()
    mult = 1
    if t.endswith("m"):
        mult, t = 1000, t[:-1]
    elif t.endswith("M"):
        mult, t = 1_000_000, t[:-1]
    t = t.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):  # 52.000 -> 52000
        t = t.replace(".", "")
    t = t.replace(",", ".")
    try:
        return round(float(t) * mult)
    except ValueError:
        return None


def numero(texto):
    """'3,5' o '3.5' -> 3.5 ; '45%' -> 45.0 ; vacío -> None."""
    if es_vacio(texto):
        return None
    t = str(texto).replace("%", "").replace("★", "").strip().replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def rango(texto, conversor):
    """'14000-65000' -> (14000, 65000) ; '450000' -> (450000, 450000)."""
    if es_vacio(texto):
        return None, None
    partes = [p for p in re.split(r"\s+-\s+|(?<=\d)-(?=\d)", str(texto)) if p.strip()]
    valores = [conversor(p) for p in partes]
    valores = [v for v in valores if v is not None]
    if not valores:
        return None, None
    return min(valores), max(valores)


def fecha(texto):
    """'30/6/2030' o '2030-06-30' -> date."""
    if es_vacio(texto):
        return None
    t = str(texto).strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        return date(int(m[3]), int(m[2]), int(m[1]))
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))
    return None


def posiciones(texto):
    """'ME/MP (DI), DL (C)' -> {('ME','D'), ('ME','I'), ('MP','D'), ('MP','I'), ('DL','C')}.
    Si el texto está cortado ('...'), se usa lo que se ve."""
    resultado = set()
    if es_vacio(texto):
        return resultado
    t = str(texto).replace("…", "...")
    for trozo in t.split(","):
        trozo = trozo.replace("...", "").strip()
        if not trozo:
            continue
        m = re.match(r"^([A-Z/]+)\s*(?:\(([DIC]*)\)?)?", trozo)
        if not m:
            continue
        bases = [b for b in m[1].split("/") if b]
        lados = m[2] or ("C" if "(" not in trozo else "")
        for b in bases:
            for lado in (lados or "C"):
                resultado.add((b, lado))
    return resultado


# ----------------------------------------------------------------- jugador normalizado

def normalizar(fila, mapa):
    """Convierte una fila del CSV en un diccionario con datos ya convertidos."""
    def col(dato):
        c = mapa.get(dato)
        return fila.get(c) if c else None

    j = {"raw": fila}
    j["jugador"] = (col("jugador") or "").strip()
    edad = numero(col("edad"))
    j["edad"] = int(edad) if edad is not None else None
    j["posicion"] = (col("posicion") or "").strip()
    j["mejor_pos"] = "" if es_vacio(col("mejor_pos")) else col("mejor_pos").strip()
    j["calidad"] = rango(col("calidad"), numero)[0]
    j["pot_min"], j["pot_max"] = rango(col("potencial"), numero)
    j["valor_min"], j["valor_max"] = rango(col("valor"), dinero)
    j["sueldo"] = dinero(col("sueldo"))
    j["fin"] = fecha(col("fin_contrato"))
    j["estado"] = "" if es_vacio(col("estado")) else col("estado").strip()
    j["pais"] = (col("pais") or "").strip()
    for dato in ("club", "situacion", "recomendacion", "inf"):
        v = col(dato)
        j[dato] = "" if es_vacio(v) else v.strip()
    j["clausula"] = dinero(col("clausula"))
    for dato in ("futura_venta", "nota", "partidos", "minutos", "amarillas", "rojas", "xg", "entrenamiento"):
        j[dato] = numero(col(dato))
    # Qué datos existen de verdad en este CSV
    j["columnas"] = set(mapa)
    return j


def potencial(j, criterio):
    """Potencial según el criterio de la configuración (minimo / media / maximo)."""
    if j.get("pot_min") is None:
        return None
    if criterio == "minimo":
        return j["pot_min"]
    if criterio == "maximo":
        return j["pot_max"]
    return (j["pot_min"] + j["pot_max"]) / 2


def texto_potencial(j):
    if j.get("pot_min") is None:
        return ""
    if j["pot_min"] == j["pot_max"]:
        return f"{j['pot_min']:g}"
    return f"{j['pot_min']:g}-{j['pot_max']:g}"


def valor_estimado(j):
    """Punto medio del rango de valor de traspaso."""
    if j.get("valor_min") is None:
        return None
    return (j["valor_min"] + j["valor_max"]) / 2


def meses_entre(desde, hasta):
    if not desde or not hasta:
        return None
    return round((hasta - desde).days / 30.44, 1)


def fecha_limite_renovacion(fin):
    """Fecha límite para renovar o vender: 6 meses antes del final
    (para contratos al 30/6, es el 1 de enero de ese año)."""
    if not fin:
        return None
    mes, anio = fin.month - 6, fin.year
    if mes <= 0:
        mes, anio = mes + 12, anio - 1
    dia = min(fin.day, 28)
    limite = date(anio, mes, dia)
    # 30/6 -> 31/12: lo pasamos al 1/1 para que sea más claro
    if fin.month == 6 and fin.day == 30:
        limite = date(fin.year, 1, 1)
    return limite


def fmt_fecha(d):
    return d.strftime("%d/%m/%Y") if d else ""


def fmt_euros(v):
    if v is None:
        return ""
    return f"{v:,.0f} €".replace(",", ".")


def mediana(valores):
    v = sorted(x for x in valores if x is not None)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
