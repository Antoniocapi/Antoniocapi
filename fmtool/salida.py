"""Generación de informes en Markdown (.md) y Excel (.xlsx)."""

import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLORES = {  # relleno de filas en Excel según el nivel de alerta
    "rojo": "F8CBAD",
    "naranja": "FFE699",
    "verde": "C6EFCE",
    "gris": "E7E6E6",
}
ICONOS = {"rojo": "🔴", "naranja": "🟠", "verde": "🟢", "gris": "⚪"}


class Informe:
    """Se va llenando con secciones, textos y tablas; luego se guarda en .md y .xlsx.

    Las tablas son listas de diccionarios. Columnas especiales:
      - una columna cuyo nombre acaba en '(€)' se formatea como dinero;
      - la clave '_nivel' ('rojo', 'naranja', 'verde', 'gris') colorea la fila.
    """

    def __init__(self, nombre, titulo, fecha_juego, subtitulo=""):
        self.nombre = nombre
        self.titulo = titulo
        self.fecha = fecha_juego
        self.subtitulo = subtitulo
        self.bloques = []

    def seccion(self, titulo):
        self.bloques.append(("seccion", titulo))

    def texto(self, texto):
        self.bloques.append(("texto", texto))

    def aviso(self, texto):
        self.bloques.append(("aviso", texto))

    def lista(self, elementos):
        self.bloques.append(("lista", list(elementos)))

    def tabla(self, hoja, columnas, filas, vacio="(ninguno)"):
        self.bloques.append(("tabla", (hoja, columnas, filas, vacio)))

    # ------------------------------------------------------------ guardar
    def guardar(self, carpeta):
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        base = carpeta / f"{self.fecha.isoformat()}_{self.nombre}"
        md, xlsx = base.with_suffix(".md"), base.with_suffix(".xlsx")
        md.write_text(self._markdown(), encoding="utf-8")
        self._excel(xlsx)
        return md, xlsx

    @staticmethod
    def _celda_md(col, v):
        if v is None:
            return ""
        if col.endswith("(€)") and isinstance(v, (int, float)):
            return f"{v:,.0f}".replace(",", ".")
        if isinstance(v, float):
            return f"{v:g}"
        return str(v).replace("|", "/").replace("\n", " ")

    def _markdown(self):
        out = [f"# {self.titulo}", ""]
        out.append(f"*Fecha de juego: {self.fecha.strftime('%d/%m/%Y')}*" + (f" · {self.subtitulo}" if self.subtitulo else ""))
        out.append("")
        for tipo, contenido in self.bloques:
            if tipo == "seccion":
                out += [f"## {contenido}", ""]
            elif tipo == "texto":
                out += [contenido, ""]
            elif tipo == "aviso":
                out += [f"> ⚠️ {contenido}", ""]
            elif tipo == "lista":
                out += [f"- {e}" for e in contenido] + [""]
            elif tipo == "tabla":
                hoja, columnas, filas, vacio = contenido
                if not filas:
                    out += [f"*{vacio}*", ""]
                    continue
                cols = [""] + columnas if any(f.get("_nivel") for f in filas) else columnas
                out.append("| " + " | ".join(cols) + " |")
                out.append("|" + "|".join("---" for _ in cols) + "|")
                for f in filas:
                    celdas = [self._celda_md(c, f.get(c)) for c in columnas]
                    if cols[0] == "":
                        celdas = [ICONOS.get(f.get("_nivel"), "")] + celdas
                    out.append("| " + " | ".join(celdas) + " |")
                out.append("")
        return "\n".join(out)

    def _excel(self, ruta):
        wb = Workbook()
        resumen = wb.active
        resumen.title = "Resumen"
        resumen["A1"] = self.titulo
        resumen["A1"].font = Font(bold=True, size=14)
        resumen["A2"] = f"Fecha de juego: {self.fecha.strftime('%d/%m/%Y')}"
        fila = 4
        nombres_usados = {"Resumen"}
        for tipo, contenido in self.bloques:
            if tipo == "seccion":
                resumen.cell(fila, 1, contenido).font = Font(bold=True, size=12)
                fila += 1
            elif tipo in ("texto", "aviso"):
                texto = ("⚠ " if tipo == "aviso" else "") + re.sub(r"\*\*?|`", "", contenido)
                resumen.cell(fila, 1, texto).alignment = Alignment(wrap_text=True, vertical="top")
                fila += 1
            elif tipo == "lista":
                for e in contenido:
                    resumen.cell(fila, 1, "• " + re.sub(r"\*\*?|`", "", e))
                    fila += 1
            elif tipo == "tabla":
                hoja, columnas, filas, vacio = contenido
                nombre = self._nombre_hoja(hoja, nombres_usados)
                resumen.cell(fila, 1, f"→ Tabla en la hoja «{nombre}» ({len(filas)} filas)").font = Font(italic=True)
                fila += 1
                self._hoja_tabla(wb.create_sheet(nombre), columnas, filas, vacio)
        resumen.column_dimensions["A"].width = 120
        wb.save(ruta)

    @staticmethod
    def _nombre_hoja(nombre, usados):
        base = re.sub(r"[\[\]\*\?/\\:]", "", nombre)[:28] or "Tabla"
        n, i = base, 2
        while n in usados:
            n, i = f"{base[:25]} {i}", i + 1
        usados.add(n)
        return n

    @staticmethod
    def _hoja_tabla(ws, columnas, filas, vacio):
        cabecera = PatternFill("solid", fgColor="1F3864")
        for c, nombre in enumerate(columnas, 1):
            celda = ws.cell(1, c, nombre)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = cabecera
            celda.alignment = Alignment(wrap_text=True, vertical="center")
        if not filas:
            ws.cell(2, 1, vacio)
        for r, f in enumerate(filas, 2):
            relleno = PatternFill("solid", fgColor=COLORES[f["_nivel"]]) if f.get("_nivel") in COLORES else None
            for c, nombre in enumerate(columnas, 1):
                v = f.get(nombre)
                celda = ws.cell(r, c, v)
                if nombre.endswith("(€)") and isinstance(v, (int, float)):
                    celda.number_format = '#,##0 "€"'
                if relleno:
                    celda.fill = relleno
        for c, nombre in enumerate(columnas, 1):
            largo = max([len(str(nombre))] + [len(str(f.get(nombre) or "")) for f in filas])
            ws.column_dimensions[get_column_letter(c)].width = min(max(10, largo + 2), 70)
        ws.freeze_panes = "B2"
        if filas:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(columnas))}{len(filas) + 1}"
