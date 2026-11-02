"""Regresión del informe ejecutivo para decisiones basadas en evidencia."""

from pathlib import Path

import pandas as pd
import pytest

from src.informe_ejecutivo import (
    analizar_hallazgos,
    generar,
    renderizar_informe,
)

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def datos():
    ventas = pd.read_csv(
        RAIZ / "data/processed/ventas_analisis.csv", encoding="utf-8-sig"
    )
    inventario = pd.read_csv(
        RAIZ / "data/processed/inventario_analisis.csv", encoding="utf-8-sig"
    )
    return ventas, inventario


def test_hallazgos_y_prioridad_comprobables(datos):
    a = analizar_hallazgos(*datos)
    assert a["fecha_min"] == "2026-01-01"
    assert a["fecha_max"] == "2026-06-30"
    assert a["transacciones"] == 491
    assert a["unidades"] == 3578
    assert a["total_ventas"] == 5_073_392.98
    assert a["registros_inventario"] == 58
    assert a["registros_afectados"] == 51
    assert a["impacto_absoluto"] == 322_700
    assert a["impacto_neto"] == 87_900
    assert a["unidades_abs"] == 230
    assert a["unidades_netas"] == 60

    assert a["inventario"][0]["sucursal"] == "Alajuela"
    assert a["inventario"][0]["impacto_absoluto"] == 179_600
    assert a["principal_discrepancia"]["producto_id"] == "P013"
    assert a["principal_discrepancia"]["sucursal"] == "Alajuela"
    assert a["principal_discrepancia"]["diferencia_stock"] == 80
    assert a["principal_discrepancia"]["impacto_absoluto"] == 116_000
    assert sum(x["ingresos"] for x in a["sucursales"]) == pytest.approx(
        a["total_ventas"]
    )
    assert sum(x["impacto_absoluto"] for x in a["inventario"]) == pytest.approx(
        a["impacto_absoluto"]
    )


def test_informe_versionado_coincide_con_los_datos(datos):
    a = analizar_hallazgos(*datos)
    texto = renderizar_informe(a)
    archivo = RAIZ / "docs/INFORME_EJECUTIVO.md"
    assert texto == archivo.read_text(encoding="utf-8")
    assert generar(RAIZ, verificar=True) == archivo
    assert "datos inventados" in texto
    assert "₡116,000.00" in texto
    assert "35.95%" in texto
    assert "diferencia neta de +60 unidades" in texto
    assert "no equivale a pérdida contable" in texto
    assert "Responsable sugerido" in texto


def test_calculo_no_modifica_los_datos(datos):
    ventas, inventario = datos
    ventas_originales, inventario_original = (
        ventas.copy(deep=True), inventario.copy(deep=True)
    )
    analizar_hallazgos(ventas, inventario)
    pd.testing.assert_frame_equal(ventas, ventas_originales)
    pd.testing.assert_frame_equal(inventario, inventario_original)


def test_no_confunde_impacto_absoluto_y_neto(datos):
    a = analizar_hallazgos(*datos)
    assert a["impacto_absoluto"] > abs(a["impacto_neto"])
    assert a["unidades_abs"] > abs(a["unidades_netas"])
    assert (
        sum(x["valor_neto"] for x in a["inventario"])
        == pytest.approx(a["impacto_neto"])
    )


def test_rechaza_fuentes_vacias_o_incompletas(datos):
    ventas, inventario = datos
    with pytest.raises(ValueError, match="no vacíos"):
        analizar_hallazgos(ventas.iloc[0:0], inventario)
    with pytest.raises(ValueError, match="columnas faltantes"):
        analizar_hallazgos(ventas.drop(columns=["sucursal"]), inventario)
    with pytest.raises(ValueError, match="fechas inválidas"):
        alteradas = ventas.copy()
        alteradas.loc[0, "fecha"] = "no-fecha"
        analizar_hallazgos(alteradas, inventario)


def test_la_prioridad_cambia_si_cambia_el_mayor_impacto(datos):
    ventas, inventario = datos
    modificado = inventario.copy(deep=True)
    mayor = modificado["impacto_absoluto"].idxmax()
    modificado.loc[mayor, "impacto_absoluto"] = 0
    resultado = analizar_hallazgos(ventas, modificado)
    assert resultado["principal_discrepancia"]["producto_id"] != "P013"
    assert modificado.loc[mayor, "impacto_absoluto"] == 0
    assert inventario.loc[mayor, "impacto_absoluto"] == 116_000
