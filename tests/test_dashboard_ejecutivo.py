"""Pruebas del SVG ejecutivo y consistencia con los CSV de análisis publicados."""

from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import pytest

from src.dashboard_ejecutivo import (
    generar_dashboard_svg,
    guardar_dashboard,
    resumir_dashboard,
)

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def datos():
    return (
        pd.read_csv(RAIZ / "data/processed/ventas_analisis.csv", encoding="utf-8-sig"),
        pd.read_csv(RAIZ / "data/processed/inventario_analisis.csv", encoding="utf-8-sig"),
    )


def test_metricas_y_agregaciones_derivadas_de_datos(datos):
    resumen = resumir_dashboard(*datos)
    assert resumen["transacciones"] == 491
    assert resumen["total_ventas"] == 5_073_392.98
    assert resumen["inventarios"] == 58
    assert resumen["con_diferencia"] == 51
    assert resumen["porcentaje_diferencia"] == 87.9
    assert resumen["impacto_absoluto"] == 322_700.0
    assert resumen["estados"] == {"Faltante": 29, "Coincide": 7, "Sobrante": 22}
    assert sum(valor for _, valor in resumen["ventas_sucursal"]) == pytest.approx(
        resumen["total_ventas"]
    )
    assert sum(valor for _, valor in resumen["ventas_categoria"]) == pytest.approx(
        resumen["total_ventas"]
    )
    assert sum(valor for _, valor in resumen["impacto_sucursal"]) == pytest.approx(
        resumen["impacto_absoluto"]
    )


def test_dashboard_publicado_es_reproducible(datos):
    resumen = resumir_dashboard(*datos)
    svg = generar_dashboard_svg(resumen)
    publicado = (RAIZ / "reports/figures/dashboard_ejecutivo.svg").read_text(
        encoding="utf-8"
    )
    assert svg == publicado
    root = ET.fromstring(svg)
    assert root.attrib["viewBox"] == "0 0 1600 1030"
    assert len(root.findall("{http://www.w3.org/2000/svg}text")) > 30
    assert "DATOS SINTÉTICOS" in svg
    assert "₡5.07 M" in svg
    assert "₡322.7 k" in svg


def test_no_modifica_dataframes_y_crea_ruta_solicitada(datos, tmp_path):
    ventas, inventario = datos
    antes_ventas = ventas.copy(deep=True)
    antes_inventario = inventario.copy(deep=True)
    archivo = tmp_path / "nuevo" / "dashboard.svg"
    salida = guardar_dashboard(ventas, inventario, archivo)
    assert salida["transacciones"] == 491
    assert archivo.exists()
    assert archivo.read_text(encoding="utf-8").startswith("<svg ")
    pd.testing.assert_frame_equal(ventas, antes_ventas)
    pd.testing.assert_frame_equal(inventario, antes_inventario)


def test_rechaza_datos_vacios_o_columnas_incompletas(datos):
    ventas, inventario = datos
    with pytest.raises(ValueError, match="no vacíos"):
        resumir_dashboard(ventas.iloc[:0], inventario)
    with pytest.raises(ValueError, match="columnas necesarias"):
        resumir_dashboard(ventas.drop(columns=["sucursal"]), inventario)


def test_etiquetas_de_usuario_se_escapan_correctamente(datos):
    ventas, inventario = datos
    ventas = ventas.copy()
    ventas.loc[0, "sucursal"] = "Heredia <script>alert(1)</script>"
    svg = generar_dashboard_svg(resumir_dashboard(ventas, inventario))
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg
    ET.fromstring(svg)
