"""Validaciones reproducibles para los entregables sintéticos del portafolio.

No altera archivos de origen ni resultados; falla con código distinto de 0 si
los datos procesados incumplen las reglas o los KPI publicados cambian.
Uso: python -m src.validar_entregables [--raiz .] [--sin-linea-base]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook


ARCHIVOS = {
    "catalogo": Path("data/processed/catalogo_productos_limpio.csv"),
    "ventas": Path("data/processed/ventas_analisis.csv"),
    "inventario": Path("data/processed/inventario_analisis.csv"),
}

LINEA_BASE = {
    "productos": 20,
    "transacciones": 491,
    "unidades_vendidas": 3578,
    "ingresos": 5_073_392.98,
    "registros_inventario": 58,
    "registros_con_diferencia": 51,
    "diferencia_absoluta_unidades": 230,
    "impacto_monetario_absoluto": 322_700.00,
}

HOJAS_PROCESADAS = {"Catalogo", "Ventas", "Inventario"}
HOJAS_REPORTE = {
    "Indicadores", "Sucursales", "Productos", "Inventario sucursal",
    "Validaciones", "Ventas detalle", "Inventario detalle",
}


def exigir(condicion: bool, mensaje: str) -> None:
    """Produce errores descriptivos y no modifica los datos."""
    if not condicion:
        raise ValueError(mensaje)


def _numeros_validos(serie: pd.Series, nombre: str, permitir_cero: bool) -> None:
    valores = pd.to_numeric(serie, errors="coerce")
    exigir(valores.notna().all(), f"{nombre}: valores nulos o no numéricos")
    exigir(np.isfinite(valores.to_numpy(dtype=float)).all(), f"{nombre}: infinitos")
    exigir(bool((valores >= 0).all()) if permitir_cero else bool((valores > 0).all()),
           f"{nombre}: valores fuera de rango")


def auditar_dataframes(
    catalogo: pd.DataFrame, ventas: pd.DataFrame, inventario: pd.DataFrame
) -> dict[str, int | float]:
    """Comprueba integridad y calcula KPI; sin dependencia de valores precalculados."""
    cat_cols = {"producto_id", "nombre_producto", "categoria", "precio_estandar"}
    ven_cols = {"venta_id", "fecha", "sucursal", "producto_id", "cantidad",
                "precio_unitario", "importe_total", "categoria", "nombre_producto"}
    inv_cols = {"sucursal", "producto_id", "stock_sistema", "stock_fisico",
                "diferencia_stock", "estado_stock", "precio_estandar",
                "valor_diferencia", "impacto_absoluto"}

    for nombre, df, esperadas in [
        ("catálogo", catalogo, cat_cols),
        ("ventas", ventas, ven_cols),
        ("inventario", inventario, inv_cols),
    ]:
        exigir(esperadas.issubset(df.columns), f"{nombre}: columnas faltantes")
        exigir(not df.empty, f"{nombre}: sin registros")
        exigir(not df.isna().any().any(), f"{nombre}: contiene nulos")
        exigir(not df.duplicated().any(), f"{nombre}: filas duplicadas")

    exigir(catalogo["producto_id"].is_unique, "catálogo: IDs duplicados")
    exigir(ventas["venta_id"].is_unique, "ventas: IDs duplicados")
    exigir(
        not inventario.duplicated(subset=["sucursal", "producto_id"]).any(),
        "inventario: combinación sucursal-producto duplicada",
    )
    validos = set(catalogo["producto_id"])
    exigir(set(ventas["producto_id"]).issubset(validos),
           "ventas: producto que no existe en catálogo")
    exigir(set(inventario["producto_id"]).issubset(validos),
           "inventario: producto que no existe en catálogo")
    exigir(pd.to_datetime(ventas["fecha"], errors="coerce").notna().all(),
           "ventas: fecha inválida")

    _numeros_validos(catalogo["precio_estandar"], "catálogo/precio", False)
    _numeros_validos(ventas["cantidad"], "ventas/cantidad", False)
    _numeros_validos(ventas["precio_unitario"], "ventas/precio", False)
    _numeros_validos(ventas["importe_total"], "ventas/importe", False)
    _numeros_validos(inventario["stock_sistema"], "inventario/sistema", True)
    _numeros_validos(inventario["stock_fisico"], "inventario/físico", True)
    _numeros_validos(inventario["precio_estandar"], "inventario/precio", False)
    _numeros_validos(inventario["impacto_absoluto"], "inventario/impacto", True)

    esperado_ventas = (
        ventas["cantidad"].astype(float) * ventas["precio_unitario"].astype(float)
    ).round(2)
    exigir(np.allclose(ventas["importe_total"].astype(float), esperado_ventas, atol=0.011),
           "ventas: importe_total no coincide con cantidad × precio")

    diferencia = (
        inventario["stock_fisico"].astype(float)
        - inventario["stock_sistema"].astype(float)
    )
    exigir(np.allclose(inventario["diferencia_stock"].astype(float), diferencia),
           "inventario: diferencia_stock incorrecta")
    estado = np.select(
        [diferencia < 0, diferencia > 0], ["Faltante", "Sobrante"], default="Coincide"
    )
    exigir(bool(np.array_equal(inventario["estado_stock"].to_numpy(), estado)),
           "inventario: clasificación de diferencia incorrecta")
    valor = (
        diferencia * inventario["precio_estandar"].astype(float)
    ).round(2)
    exigir(np.allclose(inventario["valor_diferencia"].astype(float), valor, atol=0.011),
           "inventario: valor monetario incorrecto")
    exigir(np.allclose(inventario["impacto_absoluto"].astype(float),
                       inventario["valor_diferencia"].abs().astype(float), atol=0.011),
           "inventario: impacto absoluto incorrecto")

    return {
        "productos": len(catalogo),
        "transacciones": len(ventas),
        "unidades_vendidas": int(ventas["cantidad"].sum()),
        "ingresos": round(float(ventas["importe_total"].sum()), 2),
        "registros_inventario": len(inventario),
        "registros_con_diferencia": int((diferencia != 0).sum()),
        "diferencia_absoluta_unidades": int(diferencia.abs().sum()),
        "impacto_monetario_absoluto": round(
            float(inventario["impacto_absoluto"].sum()), 2
        ),
    }


def verificar_entregables(raiz: Path, *, linea_base: bool = True) -> dict:
    """Revisa CSV, libros Excel, figura y opcionalmente el baseline sintético."""
    raiz = Path(raiz)
    tablas = {
        nombre: pd.read_csv(raiz / ruta, encoding="utf-8-sig")
        for nombre, ruta in ARCHIVOS.items()
    }
    metricas = auditar_dataframes(
        tablas["catalogo"], tablas["ventas"], tablas["inventario"]
    )

    if linea_base:
        for nombre, esperado in LINEA_BASE.items():
            exigir(abs(metricas[nombre] - esperado) < 0.01,
                   f"KPI {nombre}: {metricas[nombre]} (esperado {esperado})")

    libros = [
        (raiz / "data/processed/datos_procesados.xlsx", HOJAS_PROCESADAS),
        (raiz / "reports/reporte_analisis.xlsx", HOJAS_REPORTE),
    ]
    for ruta, hojas in libros:
        exigir(ruta.is_file() and ruta.stat().st_size > 0,
               f"Excel no disponible: {ruta}")
        libro = load_workbook(ruta, read_only=True, data_only=True)
        try:
            exigir(hojas.issubset(set(libro.sheetnames)),
                   f"Excel incompleto: {ruta.name}")
        finally:
            libro.close()

    figura = raiz / "reports/figures/dashboard_ventas_inventario.png"
    exigir(figura.is_file() and figura.stat().st_size > 0,
           "Falta el dashboard PNG")

    return metricas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--sin-linea-base", action="store_true",
                        help="Verifica reglas sin exigir los KPI exactos del dataset sintético")
    args = parser.parse_args()
    resultados = verificar_entregables(args.raiz, linea_base=not args.sin_linea_base)
    print("VALIDACIÓN APROBADA — datos procesados, Excel y dashboard")
    for nombre, valor in resultados.items():
        print(f"  {nombre}: {valor}")


if __name__ == "__main__":
    main()
