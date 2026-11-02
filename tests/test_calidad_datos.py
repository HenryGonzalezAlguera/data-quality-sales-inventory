"""Pruebas de regresión de los datos publicados y las reglas de conciliación."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.validar_entregables import (
    LINEA_BASE,
    auditar_dataframes,
    verificar_entregables,
)

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def tablas():
    return (
        pd.read_csv(RAIZ / "data/processed/catalogo_productos_limpio.csv",
                    encoding="utf-8-sig"),
        pd.read_csv(RAIZ / "data/processed/ventas_analisis.csv",
                    encoding="utf-8-sig"),
        pd.read_csv(RAIZ / "data/processed/inventario_analisis.csv",
                    encoding="utf-8-sig"),
    )


def test_resultados_y_archivos_finales_coinciden_con_readme():
    """KPI sintéticos publicados y evidencia Excel/dashboard disponibles."""
    assert verificar_entregables(RAIZ) == LINEA_BASE


def test_rechaza_productos_desconocidos_en_ventas(tablas):
    catalogo, ventas, inventario = (t.copy() for t in tablas)
    ventas.loc[0, "producto_id"] = "P999"
    with pytest.raises(ValueError, match="producto que no existe"):
        auditar_dataframes(catalogo, ventas, inventario)


def test_rechaza_ventas_con_ids_duplicados(tablas):
    catalogo, ventas, inventario = (t.copy() for t in tablas)
    ventas.loc[1, "venta_id"] = ventas.loc[0, "venta_id"]
    with pytest.raises(ValueError, match="IDs duplicados"):
        auditar_dataframes(catalogo, ventas, inventario)


def test_rechaza_stock_negativo(tablas):
    catalogo, ventas, inventario = (t.copy() for t in tablas)
    inventario.loc[0, "stock_fisico"] = -10
    with pytest.raises(ValueError, match="inventario/físico"):
        auditar_dataframes(catalogo, ventas, inventario)


def test_rechaza_diferencia_o_impacto_incorrectos(tablas):
    catalogo, ventas, inventario = (t.copy() for t in tablas)
    inventario.loc[0, "diferencia_stock"] += 1
    with pytest.raises(ValueError, match="diferencia_stock incorrecta"):
        auditar_dataframes(catalogo, ventas, inventario)

    inventario = tablas[2].copy()
    inventario.loc[0, "impacto_absoluto"] += 1000
    with pytest.raises(ValueError, match="impacto absoluto incorrecto"):
        auditar_dataframes(catalogo, ventas, inventario)


def test_rechaza_precio_no_positivo_y_ventas_inconsistentes(tablas):
    catalogo, ventas, inventario = (t.copy() for t in tablas)
    ventas.loc[0, "precio_unitario"] = 0
    with pytest.raises(ValueError, match="ventas/precio"):
        auditar_dataframes(catalogo, ventas, inventario)

    ventas = tablas[1].copy()
    ventas.loc[0, "importe_total"] += 100
    with pytest.raises(ValueError, match="importe_total"):
        auditar_dataframes(catalogo, ventas, inventario)


def test_generador_sintetico_reproducible_sin_tocar_el_repositorio(tmp_path):
    """Dos ejecuciones independientes deben producir exactamente los mismos bytes."""
    scripts = tmp_path / "src"
    scripts.mkdir()
    shutil.copy2(RAIZ / "src/generar_datos.py", scripts / "generar_datos.py")
    archivos = [
        tmp_path / "data/raw/catalogo_productos.csv",
        tmp_path / "data/raw/ventas.csv",
        tmp_path / "data/raw/inventario.xlsx",
    ]

    def ejecutar_y_hashes():
        subprocess.run([sys.executable, str(scripts / "generar_datos.py")],
                       cwd=tmp_path, check=True, capture_output=True, text=True)
        assert all(x.is_file() for x in archivos)
        return [hashlib.sha256(x.read_bytes()).hexdigest() for x in archivos]

    assert ejecutar_y_hashes() == ejecutar_y_hashes()
