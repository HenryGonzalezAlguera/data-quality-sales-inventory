"""Informe ejecutivo determinista basado en los CSV enriquecidos del proyecto.

Este módulo no atribuye causas de anomalías ni interpreta impacto absoluto como
pérdida. Permite regenerar/validar docs/INFORME_EJECUTIVO.md sin tocar data/raw.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def analizar_hallazgos(ventas: pd.DataFrame, inventario: pd.DataFrame) -> dict:
    """Agrupa importes y diferencias; ninguna entrada es modificada."""
    ventas_requeridas = {
        "fecha", "venta_id", "producto_id", "nombre_producto",
        "sucursal", "categoria", "cantidad", "importe_total"
    }
    inventario_requerido = {
        "sucursal", "producto_id", "nombre_producto", "stock_sistema",
        "stock_fisico", "diferencia_stock", "estado_stock",
        "valor_diferencia", "impacto_absoluto"
    }
    if ventas.empty or inventario.empty:
        raise ValueError("El análisis requiere datos no vacíos.")
    if not ventas_requeridas.issubset(ventas.columns):
        raise ValueError("Ventas: columnas faltantes para el informe.")
    if not inventario_requerido.issubset(inventario.columns):
        raise ValueError("Inventario: columnas faltantes para el informe.")

    fechas = pd.to_datetime(ventas["fecha"], errors="coerce")
    if fechas.isna().any():
        raise ValueError("Ventas: fechas inválidas.")

    resumen_ventas = (
        ventas.groupby("sucursal", as_index=False)
        .agg(transacciones=("venta_id", "count"),
             unidades=("cantidad", "sum"),
             ingresos=("importe_total", "sum"))
        .sort_values(["ingresos", "sucursal"], ascending=[False, True])
    )
    resumen_inventario = inventario.assign(
        afectado=inventario["diferencia_stock"].ne(0)
    ).groupby("sucursal", as_index=False).agg(
        revisados=("producto_id", "count"),
        afectados=("afectado", "sum"),
        impacto_absoluto=("impacto_absoluto", "sum"),
        valor_neto=("valor_diferencia", "sum"),
    ).sort_values(["impacto_absoluto", "sucursal"], ascending=[False, True])

    categorias = (
        ventas.groupby("categoria")["importe_total"].sum()
        .sort_values(ascending=False)
    )
    productos = (
        ventas.groupby(["producto_id", "nombre_producto"], as_index=False)
        .agg(unidades=("cantidad", "sum"), ingresos=("importe_total", "sum"))
        .sort_values(["ingresos", "producto_id"], ascending=[False, True])
    )
    discrepancias = (
        inventario.loc[inventario["diferencia_stock"].ne(0)]
        .sort_values(["impacto_absoluto", "sucursal", "producto_id"],
                     ascending=[False, True, True])
    )
    if discrepancias.empty:
        principal = None
    else:
        principal = discrepancias.iloc[0].to_dict()

    return {
        "fecha_min": fechas.min().date().isoformat(),
        "fecha_max": fechas.max().date().isoformat(),
        "total_ventas": round(float(ventas["importe_total"].sum()), 2),
        "transacciones": int(len(ventas)),
        "unidades": int(ventas["cantidad"].sum()),
        "sucursales": resumen_ventas.to_dict("records"),
        "categorias": [(str(k), round(float(v), 2))
                       for k, v in categorias.items()],
        "productos_top": productos.head(5).to_dict("records"),
        "inventario": resumen_inventario.to_dict("records"),
        "registros_inventario": int(len(inventario)),
        "registros_afectados": int(inventario["diferencia_stock"].ne(0).sum()),
        "unidades_abs": int(inventario["diferencia_stock"].abs().sum()),
        "unidades_netas": int(inventario["diferencia_stock"].sum()),
        "impacto_absoluto": round(float(inventario["impacto_absoluto"].sum()), 2),
        "impacto_neto": round(float(inventario["valor_diferencia"].sum()), 2),
        "principal_discrepancia": principal,
    }


def _crc(valor: float) -> str:
    return f"₡{valor:,.2f}"


def _porcentaje(numerador: float, denominador: float) -> str:
    return f"{numerador / denominador * 100:.2f}%" if denominador else "0.00%"


def renderizar_informe(analisis: dict) -> str:
    """Devuelve Markdown reproducible con recomendaciones y supuestos explícitos."""
    total = analisis["total_ventas"]
    impacto = analisis["impacto_absoluto"]
    afect = analisis["registros_afectados"]
    rev = analisis["registros_inventario"]
    lineas = [
        "# Informe ejecutivo — Calidad de datos de ventas e inventario",
        "",
        "> **Caso sintético de portafolio.** Los valores representan datos inventados y "
        "no deben interpretarse como resultados de una empresa real.",
        "",
        "## Resumen ejecutivo",
        "",
        f"Se analizaron **{analisis['transacciones']:,} transacciones válidas** "
        f"entre **{analisis['fecha_min']} y {analisis['fecha_max']}**, "
        f"con importes por **{_crc(total)}** y **{analisis['unidades']:,} unidades vendidas**.",
        f"En inventario, **{afect} de {rev} registros** "
        f"({_porcentaje(afect, rev)}) mostraron diferencias entre el sistema "
        "y el conteo físico.",
        f"La suma de desviaciones absolutas valorizadas fue **{_crc(impacto)}**; "
        "no equivale a pérdida contable ni al faltante neto.",
        "",
        "## 1. Desempeño de ventas por sucursal",
        "",
        "| Sucursal | Transacciones | Unidades | Importe analizado | Participación |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for r in analisis["sucursales"]:
        lineas.append(
            f"| {r['sucursal']} | {int(r['transacciones']):,} | "
            f"{int(r['unidades']):,} | {_crc(r['ingresos'])} | "
            f"{_porcentaje(r['ingresos'], total)} |"
        )
    lineas += ["", "Las diferencias de importe entre sucursales no demuestran por sí "
              "solas diferencias de rentabilidad: no se analizan costos operativos "
              "ni cobros reales.", "", "## 2. Categorías y productos destacados",
              "", "| Categoría | Importe analizado | Participación |",
              "| --- | ---: | ---: |"]
    for categoria, valor in analisis["categorias"]:
        lineas.append(f"| {categoria} | {_crc(valor)} | {_porcentaje(valor, total)} |")
    lineas += ["", "**Cinco productos con mayor importe:**", "",
              "| Producto | Unidades vendidas | Importe |",
              "| --- | ---: | ---: |"]
    for r in analisis["productos_top"]:
        lineas.append(
            f"| {r['producto_id']} — {r['nombre_producto']} | "
            f"{int(r['unidades']):,} | {_crc(r['ingresos'])} |"
        )
    lineas += ["", "## 3. Conciliación de inventario por sucursal", "",
              "| Sucursal | Revisados | Con diferencia | % con diferencia | Impacto absoluto | % del impacto total |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in analisis["inventario"]:
        lineas.append(
            f"| {r['sucursal']} | {int(r['revisados'])} | "
            f"{int(r['afectados'])} | "
            f"{_porcentaje(r['afectados'], r['revisados'])} | "
            f"{_crc(r['impacto_absoluto'])} | "
            f"{_porcentaje(r['impacto_absoluto'], impacto)} |"
        )
    lineas += [
        "",
        f"**Magnitudes distintas:** desviación absoluta de "
        f"**{analisis['unidades_abs']} unidades**, frente a una "
        f"**diferencia neta de {analisis['unidades_netas']:+d} unidades**; "
        f"valor absoluto **{_crc(impacto)}** frente a "
        f"valor neto **{_crc(analisis['impacto_neto'])}**.",
        "La compensación de sobrantes y faltantes no elimina la necesidad de "
        "revisar cada discrepancia.",
        "",
        "### Mayor discrepancia individual",
        "",
    ]
    principal = analisis["principal_discrepancia"]
    if principal is None:
        lineas.append("No hay discrepancias en los registros válidos.")
    else:
        lineas.append(
            f"**{principal['sucursal']} · {principal['producto_id']} — "
            f"{principal['nombre_producto']}**: "
            f"stock del sistema **{int(principal['stock_sistema'])}**, "
            f"stock físico **{int(principal['stock_fisico'])}**, "
            f"diferencia **{int(principal['diferencia_stock']):+d} unidades "
            f"({principal['estado_stock']})** e impacto absoluto "
            f"**{_crc(principal['impacto_absoluto'])}** "
            f"({_porcentaje(principal['impacto_absoluto'], impacto)} "
            "del impacto total)."
        )
    lineas += [
        "",
        "## 4. Plan de acción sugerido",
        "",
        "| Prioridad | Acción propuesta | Responsable sugerido | Indicador de seguimiento |",
        "| --- | --- | --- | --- |",
        "| Alta | Revisar primero la discrepancia individual de mayor impacto: "
        "conteo independiente y movimientos de entrada/salida. | "
        "Encargado de inventario | Diferencia en unidades y valor conciliado |",
        "| Alta | Implementar conteos cíclicos en la sucursal con mayor "
        "impacto absoluto; documentar causas y correcciones. | "
        "Operaciones y almacén | % de registros con diferencia e impacto absoluto |",
        "| Media | Estandarizar captura de fechas, cantidades, IDs y "
        "precios; rechazar datos inválidos antes del análisis. | "
        "Responsable de datos | Errores por regla y registros descartados |",
        "| Media | Monitorear semanalmente sucursales y productos "
        "de mayor importe, sin asumir márgenes o rentabilidad. | "
        "Analista comercial | Importe por sucursal/categoría y transacciones válidas |",
        "",
        "## 5. Metodología y límites",
        "",
        "- **Origen:** CSV de ventas/catálogo y Excel de inventario sintéticos; "
        "datos transformados por `src/procesamiento.py`.",
        "- **Reglas:** normalización de etiquetas, deduplicación, validación "
        "de fechas, cantidades y referencias; conciliación por stock físico menos stock del sistema.",
        "- **Fórmulas:** importe de venta = cantidad × precio unitario; "
        "diferencia = stock físico − stock del sistema; "
        "impacto absoluto = |diferencia × precio estándar|.",
        "- **No inferencias:** los datos no evidencian fraude, pérdida real, "
        "causas de diferencias, impuestos, costos ni cobros efectivamente recibidos.",
        "- **Reproducibilidad:** `python -m src.informe_ejecutivo` "
        "regenera este documento desde los archivos procesados. "
        "`python -m pytest -q tests` verifica los hallazgos.",
        "",
        "---",
        "",
        "Informe generado automáticamente desde "
        "`data/processed/ventas_analisis.csv` e "
        "`data/processed/inventario_analisis.csv`. "
        "No incluye datos personales ni fuentes empresariales reales.",
        "",
    ]
    return "\n".join(lineas)


def generar(raiz: Path, verificar: bool = False) -> Path:
    raiz = Path(raiz)
    ventas = pd.read_csv(raiz / "data/processed/ventas_analisis.csv",
                        encoding="utf-8-sig")
    inventario = pd.read_csv(
        raiz / "data/processed/inventario_analisis.csv", encoding="utf-8-sig"
    )
    texto = renderizar_informe(analizar_hallazgos(ventas, inventario))
    destino = raiz / "docs/INFORME_EJECUTIVO.md"
    if verificar:
        if not destino.is_file() or destino.read_text(encoding="utf-8") != texto:
            raise ValueError("Informe ejecutivo desactualizado. Ejecuta "
                             "python -m src.informe_ejecutivo")
    else:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    ruta = generar(args.raiz, verificar=args.verificar)
    print(f"INFORME EJECUTIVO {'VERIFICADO' if args.verificar else 'GENERADO'}: {ruta}")


if __name__ == "__main__":
    main()
