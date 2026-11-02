"""Pruebas del pipeline importable frente a los entregables históricos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.procesamiento import (
    conciliar_inventario,
    corregir_catalogo_y_vendedores,
    depurar_ventas,
    normalizar_fuentes,
)
from src.validar_entregables import LINEA_BASE, auditar_dataframes

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw():
    catalogo = pd.read_csv(RAIZ / "data/raw/catalogo_productos.csv",
                           encoding="utf-8-sig")
    ventas = pd.read_csv(RAIZ / "data/raw/ventas.csv", encoding="utf-8-sig")
    inventario = pd.read_excel(RAIZ / "data/raw/inventario.xlsx",
                               sheet_name="Inventario")
    return catalogo, ventas, inventario


def ejecutar(raw):
    catalogo, ventas, inventario, resumen_normalizacion = normalizar_fuentes(*raw)
    catalogo, ventas, resumen_correcciones = corregir_catalogo_y_vendedores(
        catalogo, ventas
    )
    ventas, problemas_ventas, resumen_ventas = depurar_ventas(ventas, catalogo)
    inventario, problemas_inventario, resumen_inventario = conciliar_inventario(
        inventario, catalogo
    )
    return (
        catalogo, ventas, inventario,
        resumen_normalizacion, resumen_correcciones,
        problemas_ventas, resumen_ventas,
        problemas_inventario, resumen_inventario,
    )


def test_transformaciones_coinciden_con_csv_publicados(raw):
    catalogo, ventas, inventario, *_ = ejecutar(raw)
    expected_cat = pd.read_csv(
        RAIZ / "data/processed/catalogo_productos_limpio.csv", encoding="utf-8-sig"
    )
    expected_sales = pd.read_csv(
        RAIZ / "data/processed/ventas_limpias.csv", encoding="utf-8-sig"
    )
    expected_stock = pd.read_csv(
        RAIZ / "data/processed/inventario_conciliado.csv", encoding="utf-8-sig"
    )
    expected_sales["fecha"] = pd.to_datetime(expected_sales["fecha"])
    expected_stock["fecha_corte"] = pd.to_datetime(expected_stock["fecha_corte"])

    pd.testing.assert_frame_equal(catalogo.reset_index(drop=True), expected_cat,
                                  check_dtype=False, check_exact=False, atol=0.00001)
    pd.testing.assert_frame_equal(ventas, expected_sales, check_dtype=False,
                                  check_exact=False, atol=0.00001)
    pd.testing.assert_frame_equal(inventario, expected_stock, check_dtype=False,
                                  check_exact=False, atol=0.00001)


def test_limpieza_no_modifica_fuentes_originales(raw):
    fotografias = [df.copy(deep=True) for df in raw]
    primera = ejecutar(raw)
    segunda = ejecutar(raw)
    for original, fotografia in zip(raw, fotografias):
        pd.testing.assert_frame_equal(original, fotografia)
    for una, otra in zip(primera, segunda):
        pd.testing.assert_frame_equal(una, otra)


def test_reportes_intermedios_y_kpi_sinteticos(raw):
    (
        catalogo, ventas, inventario, normalizacion, correcciones,
        problemas_ventas, resumen_ventas, problemas_inventario, resumen_inventario,
    ) = ejecutar(raw)

    assert normalizacion["duplicados_eliminados"].tolist() == [1, 5, 1]
    assert correcciones["registros_corregidos"].tolist() == [1, 1, 1]
    assert len(ventas) == 491
    assert len(inventario) == 58
    assert int(resumen_ventas["filas_descartadas"].iloc[0]) == 9
    assert int(resumen_inventario["filas_descartadas"].iloc[0]) == 2
    assert int(resumen_inventario["inventarios_con_diferencia"].iloc[0]) == 51
    assert int(problemas_ventas["registros_detectados"].sum()) >= 9
    assert int(problemas_inventario["registros_detectados"].sum()) >= 2

    # Las mismas transformaciones producen datos aptos para el validador.
    ventas_analisis = ventas.merge(
        catalogo[["producto_id", "nombre_producto", "categoria", "precio_estandar"]],
        on="producto_id", how="left", validate="many_to_one",
    )
    inventario_analisis = inventario.merge(
        catalogo[["producto_id", "nombre_producto", "categoria", "precio_estandar"]],
        on="producto_id", how="left", validate="many_to_one",
    )
    inventario_analisis["valor_diferencia"] = (
        inventario_analisis["diferencia_stock"]
        * inventario_analisis["precio_estandar"]
    ).round(2)
    inventario_analisis["impacto_absoluto"] = (
        inventario_analisis["valor_diferencia"].abs()
    )
    assert auditar_dataframes(catalogo, ventas_analisis,
                             inventario_analisis) == LINEA_BASE


def test_producto_inexistente_se_descarta_sin_corromper_datos(raw):
    catalogo, ventas, inventario, _ = normalizar_fuentes(*raw)
    catalogo, ventas, _ = corregir_catalogo_y_vendedores(catalogo, ventas)
    ventas.loc[0, "producto_id"] = "P999"
    limpio, problemas, _ = depurar_ventas(ventas, catalogo)
    assert "P999" not in set(limpio["producto_id"])
    assert "P999" in set(ventas["producto_id"])
    assert int(problemas.loc[
        problemas["problema"] == "Producto inexistente en catálogo",
        "registros_detectados",
    ].iloc[0]) >= 1


def test_errores_de_inventario_se_excluyen_sin_modificar_fuente(raw):
    catalogo, ventas, inventario, _ = normalizar_fuentes(*raw)
    original = inventario.copy(deep=True)
    limpio, problemas, resumen = conciliar_inventario(inventario, catalogo)
    assert (limpio["stock_fisico"] >= 0).all()
    assert limpio["producto_id"].notna().all()
    assert int(problemas["registros_detectados"].sum()) >= 2
    assert int(resumen["filas_descartadas"].iloc[0]) == 2
    pd.testing.assert_frame_equal(inventario, original)
