"""Dashboard ejecutivo reproducible en SVG a partir de ventas e inventario.

Genera una imagen vectorial accesible y apta para README, sin servicios externos
ni datos personales. No modifica DataFrames ni sustituye los archivos históricos.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd


def resumir_dashboard(ventas: pd.DataFrame, inventario: pd.DataFrame) -> dict:
    """Recalcula las métricas desde las tablas enriquecidas, sin constantes de negocio."""
    ventas_necesarias = {"venta_id", "importe_total", "sucursal", "categoria"}
    inventario_necesarias = {"sucursal", "diferencia_stock", "impacto_absoluto"}
    if ventas.empty or inventario.empty:
        raise ValueError("El dashboard requiere ventas e inventario no vacíos.")
    if not ventas_necesarias.issubset(ventas.columns):
        raise ValueError("Faltan columnas necesarias en ventas.")
    if not inventario_necesarias.issubset(inventario.columns):
        raise ValueError("Faltan columnas necesarias en inventario.")

    por_sucursal = ventas.groupby("sucursal")["importe_total"].sum().sort_values(
        ascending=False
    )
    por_categoria = ventas.groupby("categoria")["importe_total"].sum().sort_values(
        ascending=False
    )
    impacto_sucursal = inventario.groupby("sucursal")["impacto_absoluto"].sum().sort_values(
        ascending=False
    )
    total_ventas = round(float(ventas["importe_total"].sum()), 2)
    diferencias = int(inventario["diferencia_stock"].ne(0).sum())
    return {
        "transacciones": len(ventas),
        "total_ventas": total_ventas,
        "inventarios": len(inventario),
        "con_diferencia": diferencias,
        "porcentaje_diferencia": round(diferencias / len(inventario) * 100, 1),
        "impacto_absoluto": round(float(inventario["impacto_absoluto"].sum()), 2),
        "ventas_sucursal": [(str(k), round(float(v), 2)) for k, v in por_sucursal.items()],
        "ventas_categoria": [(str(k), round(float(v), 2)) for k, v in por_categoria.items()],
        "impacto_sucursal": [(str(k), round(float(v), 2)) for k, v in impacto_sucursal.items()],
        "estados": {
            "Faltante": int(inventario["diferencia_stock"].lt(0).sum()),
            "Coincide": int(inventario["diferencia_stock"].eq(0).sum()),
            "Sobrante": int(inventario["diferencia_stock"].gt(0).sum()),
        },
    }


def _moneda(valor: float) -> str:
    """Cantidades compactas en CRC, sin alterar los importes originales."""
    if abs(valor) >= 1_000_000:
        return f"₡{valor / 1_000_000:.2f} M"
    if abs(valor) >= 1_000:
        return f"₡{valor / 1_000:.1f} k"
    return f"₡{valor:,.0f}"


def generar_dashboard_svg(resumen: dict) -> str:
    """Genera un SVG estático. El contenido textual se escapa como XML."""
    fondo, panel = "#0B1322", "#162337"
    texto, secundario = "#F4F7FC", "#A8B7CB"
    acento, azul, naranja = "#42D4A4", "#6BAEFA", "#F6B26B"
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1030" viewBox="0 0 1600 1030" role="img" aria-labelledby="titulo descripcion">',
        '<title id="titulo">Dashboard ejecutivo: calidad de datos de ventas e inventario</title>',
        '<desc id="descripcion">Cuatro indicadores, ingresos por sucursal y categoría, impacto de inventario por sucursal y distribución de faltantes, coincidencias y sobrantes. Datos sintéticos.</desc>',
        f'<rect width="1600" height="1030" fill="{fondo}"/>',
        '<rect x="48" y="42" width="8" height="48" rx="4" fill="#42D4A4"/>',
    ]

    def caja(x: float, y: float, w: float, h: float, fill: str = panel, radio: int = 19) -> None:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radio}" fill="{fill}"/>')

    def escribir(x: float, y: float, valor: object, size: int = 22,
                 color: str = texto, weight: int = 400, ancla: str = "start") -> None:
        v = escape(str(valor), quote=True)
        svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, DejaVu Sans, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{ancla}">{v}</text>')

    escribir(78, 63, "DATA QUALITY / SALES & INVENTORY", 18, acento, 700)
    escribir(48, 121, "Visión ejecutiva de calidad de datos", 40, texto, 750)
    escribir(48, 157, "Ventas analizadas y conciliación de inventario  ·  escenario sintético", 19, secundario)
    caja(1334, 61, 218, 46, "#23374B", 23)
    escribir(1443, 92, "DATOS SINTÉTICOS", 17, acento, 700, "middle")

    tarjetas = [
        ("VENTAS ANALIZADAS", _moneda(resumen["total_ventas"]),
         "Importe de transacciones válidas", acento),
        ("TRANSACCIONES", f'{resumen["transacciones"]:,}',
         "Operaciones limpias", azul),
        ("CON DIFERENCIA", f'{resumen["con_diferencia"]}/{resumen["inventarios"]}',
         f'{resumen["porcentaje_diferencia"]:.1f}% de inventarios revisados', naranja),
        ("IMPACTO ABSOLUTO", _moneda(resumen["impacto_absoluto"]),
         "Valor de desviaciones, no pérdida neta", "#EBA6F9"),
    ]
    for idx, (etiqueta, cifra, subtitulo, color) in enumerate(tarjetas):
        x = 48 + idx * 382
        caja(x, 197, 358, 145)
        svg.append(f'<rect x="{x}" y="197" width="358" height="5" rx="2" fill="{color}"/>')
        escribir(x + 23, 238, etiqueta, 16, secundario, 700)
        escribir(x + 23, 293, cifra, 40, texto, 700)
        escribir(x + 23, 323, subtitulo, 14, secundario)

    def panel_barras(x: int, y: int, titulo: str, nota: str,
                     valores: list[tuple[str, float]], color: str,
                     altura: int, moneda: bool = True) -> None:
        caja(x, y, 739, altura)
        escribir(x + 26, y + 43, titulo, 25, texto, 700)
        escribir(x + 26, y + 72, nota, 16, secundario)
        maximo = max([valor for _, valor in valores], default=1) or 1
        espacio = 53 if len(valores) > 3 else 66
        for i, (etiqueta, valor) in enumerate(valores):
            fila_y = y + 107 + i * espacio
            escribir(x + 27, fila_y, etiqueta, 17, texto, 600)
            escribir(x + 708, fila_y, _moneda(valor) if moneda else str(round(valor)),
                     17, texto, 700, "end")
            caja(x + 27, fila_y + 13, 676, 12, "#293A50", 6)
            largo = max(2, round(676 * valor / maximo)) if valor > 0 else 0
            if largo:
                caja(x + 27, fila_y + 13, largo, 12, color, 6)

    panel_barras(
        48, 371, "Ventas por sucursal",
        "Participación de ingresos en las tres ubicaciones",
        resumen["ventas_sucursal"], acento, 286,
    )
    panel_barras(
        813, 371, "Impacto absoluto por sucursal",
        "Diferencias valorizadas de stock; no equivale a pérdidas",
        resumen["impacto_sucursal"], naranja, 286,
    )
    panel_barras(
        48, 679, "Ventas por categoría",
        "Clasificación por importe total de ventas",
        resumen["ventas_categoria"], azul, 291,
    )
    caja(813, 679, 739, 291)
    escribir(840, 722, "Conciliación del inventario", 25, texto, 700)
    escribir(840, 751, "Cantidad de registros según el conteo físico", 16, secundario)
    estados = resumen["estados"]
    for i, (nombre, color) in enumerate(
        [("Faltante", "#F3868B"), ("Coincide", acento), ("Sobrante", naranja)]
    ):
        y = 810 + i * 54
        cantidad = estados[nombre]
        escribir(840, y, nombre, 19, texto, 600)
        escribir(1517, y, cantidad, 20, texto, 700, "end")
        caja(1020, y - 14, 437, 13, "#293A50", 6)
        if cantidad:
            caja(1020, y - 14, round(437 * cantidad / max(1, resumen["inventarios"])),
                 13, color, 6)
    escribir(48, 1009, "Fuente: datos sintéticos del repositorio · cálculos desde CSV procesados · valores en CRC", 15, secundario)
    escribir(1552, 1009, "Python · pandas · calidad de datos", 15, secundario, 400, "end")
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def guardar_dashboard(
    ventas: pd.DataFrame, inventario: pd.DataFrame, destino: Path,
) -> dict:
    """Escribe un SVG reproducible en una ruta indicada por el llamador."""
    resumen = resumir_dashboard(ventas, inventario)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(generar_dashboard_svg(resumen), encoding="utf-8")
    return resumen
