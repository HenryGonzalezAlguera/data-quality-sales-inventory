"""Transformaciones de calidad para ventas, catálogo e inventario.

Funciones puras en términos de DataFrames: no leen ni escriben archivos y no
modifican los argumentos originales. Las reglas provienen del notebook original
01_auditoria_calidad_datos.ipynb y preservan sus KPI sintéticos publicados.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def normalizar_fuentes(
    catalogo: pd.DataFrame, ventas: pd.DataFrame, inventario: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Descarta duplicados exactos y normaliza textos/IDs de las tres fuentes."""
    catalogo_limpio = catalogo.drop_duplicates().copy()
    ventas_limpias = ventas.drop_duplicates().copy()
    inventario_limpio = inventario.drop_duplicates().copy()
    filas_antes = {
        "Catálogo de productos": len(catalogo),
        "Ventas": len(ventas),
        "Inventario": len(inventario),
    }
    for df in (catalogo_limpio, ventas_limpias, inventario_limpio):
        df["producto_id"] = df["producto_id"].astype("string").str.strip().str.upper()

    for columna in ("nombre_producto", "categoria"):
        catalogo_limpio[columna] = (
            catalogo_limpio[columna].astype("string").str.strip().str.title()
        )
    for columna in ("sucursal", "vendedor"):
        ventas_limpias[columna] = (
            ventas_limpias[columna].astype("string").str.strip().str.title()
        )
    ventas_limpias["canal"] = (
        ventas_limpias["canal"].astype("string").str.strip().str.capitalize()
    )
    for columna in ("sucursal", "responsable"):
        inventario_limpio[columna] = (
            inventario_limpio[columna].astype("string").str.strip().str.title()
        )

    resumen = pd.DataFrame({
        "fuente": list(filas_antes),
        "filas_antes": list(filas_antes.values()),
        "filas_despues": [
            len(catalogo_limpio), len(ventas_limpias), len(inventario_limpio)
        ],
    })
    resumen["duplicados_eliminados"] = (
        resumen["filas_antes"] - resumen["filas_despues"]
    )
    return catalogo_limpio, ventas_limpias, inventario_limpio, resumen


def corregir_catalogo_y_vendedores(
    catalogo: pd.DataFrame, ventas: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Completa descripciones y corrige precios no positivos por mediana."""
    catalogo_limpio = catalogo.copy(deep=True)
    ventas_limpias = ventas.copy(deep=True)

    nombres_faltantes = int(catalogo_limpio["nombre_producto"].isna().sum())
    vendedores_faltantes = int(ventas_limpias["vendedor"].isna().sum())
    precios_catalogo_invalidos = int(
        (catalogo_limpio["precio_estandar"] <= 0).sum()
    )
    catalogo_limpio["nombre_producto"] = (
        catalogo_limpio["nombre_producto"].fillna("Producto sin nombre")
    )
    ventas_limpias["vendedor"] = (
        ventas_limpias["vendedor"].fillna("No informado")
    )

    precios_validos = catalogo_limpio["precio_estandar"] > 0
    medianas = (
        catalogo_limpio.loc[precios_validos]
        .groupby("categoria")["precio_estandar"].median()
    )
    mediana_global = catalogo_limpio.loc[
        precios_validos, "precio_estandar"
    ].median()

    invalidos = catalogo_limpio["precio_estandar"] <= 0
    reemplazos = (
        catalogo_limpio.loc[invalidos, "categoria"]
        .map(medianas)
        .fillna(mediana_global)
    )
    catalogo_limpio.loc[invalidos, "precio_estandar"] = reemplazos

    resumen = pd.DataFrame({
        "correccion": [
            "Nombres de producto completados",
            "Vendedores completados",
            "Precios de catálogo corregidos",
        ],
        "registros_corregidos": [
            nombres_faltantes, vendedores_faltantes, precios_catalogo_invalidos
        ],
    })
    return catalogo_limpio, ventas_limpias, resumen


def depurar_ventas(
    ventas: pd.DataFrame, catalogo: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Excluye ventas irrecuperables, repara precios y calcula importe."""
    ventas_limpias = ventas.copy(deep=True)
    filas_antes = len(ventas_limpias)
    fechas = pd.to_datetime(ventas_limpias["fecha"], errors="coerce")
    productos_validos = set(catalogo["producto_id"].dropna())

    faltante = ventas_limpias["producto_id"].isna()
    inexistente = (
        ventas_limpias["producto_id"].notna()
        & ~ventas_limpias["producto_id"].isin(productos_validos)
    )
    fecha_invalida = fechas.isna()
    cantidad_invalida = ventas_limpias["cantidad"] <= 0
    precio_invalido_detectado = ventas_limpias["precio_unitario"] <= 0

    problemas = pd.DataFrame({
        "problema": [
            "Producto faltante", "Producto inexistente en catálogo",
            "Fecha inválida", "Cantidad igual o menor que cero",
            "Precio igual o menor que cero",
        ],
        "registros_detectados": [
            int(faltante.sum()), int(inexistente.sum()), int(fecha_invalida.sum()),
            int(cantidad_invalida.sum()), int(precio_invalido_detectado.sum()),
        ],
    })
    ventas_limpias["fecha"] = fechas
    descartar = faltante | inexistente | fecha_invalida | cantidad_invalida
    ventas_limpias = ventas_limpias.loc[~descartar].copy()

    precios = catalogo.set_index("producto_id")["precio_estandar"]
    precio_invalido = ventas_limpias["precio_unitario"] <= 0
    precios_corregidos = int(precio_invalido.sum())
    ventas_limpias.loc[precio_invalido, "precio_unitario"] = (
        ventas_limpias.loc[precio_invalido, "producto_id"].map(precios)
    )
    ventas_limpias["importe_total"] = (
        ventas_limpias["cantidad"] * ventas_limpias["precio_unitario"]
    ).round(2)
    ventas_limpias = ventas_limpias.reset_index(drop=True)

    resumen = pd.DataFrame({
        "filas_antes": [filas_antes],
        "filas_despues": [len(ventas_limpias)],
        "filas_descartadas": [filas_antes - len(ventas_limpias)],
        "precios_corregidos": [precios_corregidos],
    })
    return ventas_limpias, problemas, resumen


def conciliar_inventario(
    inventario: pd.DataFrame, catalogo: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Verifica inventario, clasifica faltantes/sobrantes y calcula diferencias."""
    inventario_limpio = inventario.copy(deep=True)
    filas_antes = len(inventario_limpio)
    fechas = pd.to_datetime(inventario_limpio["fecha_corte"], errors="coerce")
    productos_validos = set(catalogo["producto_id"].dropna())
    faltante = inventario_limpio["producto_id"].isna()
    inexistente = (
        inventario_limpio["producto_id"].notna()
        & ~inventario_limpio["producto_id"].isin(productos_validos)
    )
    stock_sistema_invalido = (
        inventario_limpio["stock_sistema"].isna()
        | (inventario_limpio["stock_sistema"] < 0)
    )
    stock_fisico_invalido = (
        inventario_limpio["stock_fisico"].isna()
        | (inventario_limpio["stock_fisico"] < 0)
    )
    fecha_invalida = fechas.isna()

    problemas = pd.DataFrame({
        "problema": [
            "Producto faltante", "Producto inexistente en catálogo",
            "Stock del sistema inválido", "Stock físico inválido",
            "Fecha de corte inválida",
        ],
        "registros_detectados": [
            int(faltante.sum()), int(inexistente.sum()),
            int(stock_sistema_invalido.sum()), int(stock_fisico_invalido.sum()),
            int(fecha_invalida.sum()),
        ],
    })
    inventario_limpio["fecha_corte"] = fechas
    descartar = (
        faltante | inexistente | stock_sistema_invalido
        | stock_fisico_invalido | fecha_invalida
    )
    inventario_limpio = inventario_limpio.loc[~descartar].copy()
    inventario_limpio["diferencia_stock"] = (
        inventario_limpio["stock_fisico"] - inventario_limpio["stock_sistema"]
    )
    inventario_limpio["estado_stock"] = np.select(
        [
            inventario_limpio["diferencia_stock"] < 0,
            inventario_limpio["diferencia_stock"] > 0,
        ],
        ["Faltante", "Sobrante"], default="Coincide",
    )
    inventario_limpio = inventario_limpio.reset_index(drop=True)

    resumen = pd.DataFrame({
        "filas_antes": [filas_antes],
        "filas_despues": [len(inventario_limpio)],
        "filas_descartadas": [filas_antes - len(inventario_limpio)],
        "inventarios_con_diferencia": [
            int((inventario_limpio["diferencia_stock"] != 0).sum())
        ],
    })
    return inventario_limpio, problemas, resumen
