from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill


# Semilla fija para generar siempre los mismos datos
SEMILLA = 42
generador = np.random.default_rng(SEMILLA)

# Rutas principales del proyecto
RUTA_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_DATOS_ORIGINALES = RUTA_PROYECTO / "data" / "raw"

RUTA_DATOS_ORIGINALES.mkdir(parents=True, exist_ok=True)


def crear_catalogo_productos():
    """
    Crea un catálogo de productos limpio y una copia
    con inconsistencias intencionales.
    """

    productos = [
        ("P001", "Piña dorada", "Frutas", 1250.00, True),
        ("P002", "Mango", "Frutas", 1100.00, True),
        ("P003", "Papaya", "Frutas", 950.00, True),
        ("P004", "Banano", "Frutas", 700.00, True),
        ("P005", "Sandía", "Frutas", 1800.00, True),
        ("P006", "Melón", "Frutas", 1600.00, True),
        ("P007", "Tomate", "Vegetales", 1300.00, True),
        ("P008", "Chile dulce", "Vegetales", 1150.00, True),
        ("P009", "Cebolla", "Vegetales", 900.00, True),
        ("P010", "Zanahoria", "Vegetales", 850.00, True),
        ("P011", "Frijoles", "Granos", 1550.00, True),
        ("P012", "Arroz", "Granos", 1350.00, True),
        ("P013", "Lentejas", "Granos", 1450.00, True),
        ("P014", "Garbanzos", "Granos", 1650.00, True),
        ("P015", "Jugo de naranja", "Bebidas", 1750.00, True),
        ("P016", "Jugo de piña", "Bebidas", 1700.00, True),
        ("P017", "Agua de coco", "Bebidas", 1400.00, True),
        ("P018", "Té frío", "Bebidas", 1200.00, True),
        ("P019", "Pulpa de mango", "Congelados", 2200.00, True),
        ("P020", "Pulpa de fresa", "Congelados", 2350.00, True),
    ]

    columnas = [
        "producto_id",
        "nombre_producto",
        "categoria",
        "precio_estandar",
        "activo",
    ]

    catalogo_limpio = pd.DataFrame(productos, columns=columnas)
    catalogo_con_errores = catalogo_limpio.copy()

    # Errores intencionales
    catalogo_con_errores.loc[5, "nombre_producto"] = None
    catalogo_con_errores.loc[8, "categoria"] = "vegetales"
    catalogo_con_errores.loc[11, "producto_id"] = " P012 "
    catalogo_con_errores.loc[14, "precio_estandar"] = -500.00

    # Producto duplicado
    fila_duplicada = catalogo_con_errores.iloc[[4]].copy()

    catalogo_con_errores = pd.concat(
        [catalogo_con_errores, fila_duplicada],
        ignore_index=True,
    )

    return catalogo_limpio, catalogo_con_errores


def crear_ventas(catalogo_limpio):
    """
    Genera 500 ventas y agrega inconsistencias intencionales.
    """

    cantidad_ventas = 500

    fechas = pd.date_range(
        start="2026-01-01",
        end="2026-06-30",
        freq="D",
    )

    sucursales = ["Heredia", "Alajuela", "San José"]
    vendedores = ["Ana", "Carlos", "Daniela", "José", "María"]
    canales = ["Tienda", "Teléfono", "En línea"]

    ventas = pd.DataFrame(
        {
            "venta_id": [
                f"V{numero:05d}"
                for numero in range(1, cantidad_ventas + 1)
            ],
            "fecha": generador.choice(
                fechas.to_numpy(),
                cantidad_ventas,
            ),
            "sucursal": generador.choice(
                sucursales,
                cantidad_ventas,
            ),
            "producto_id": generador.choice(
                catalogo_limpio["producto_id"],
                cantidad_ventas,
            ),
            "cantidad": generador.integers(
                1,
                15,
                cantidad_ventas,
            ),
            "vendedor": generador.choice(
                vendedores,
                cantidad_ventas,
            ),
            "canal": generador.choice(
                canales,
                cantidad_ventas,
            ),
        }
    )

    mapa_precios = catalogo_limpio.set_index(
        "producto_id"
    )["precio_estandar"]

    precio_base = ventas["producto_id"].map(mapa_precios)
    variacion_precio = generador.uniform(
        0.95,
        1.05,
        cantidad_ventas,
    )

    ventas["precio_unitario"] = (
        precio_base * variacion_precio
    ).round(2)

    ventas["fecha"] = pd.to_datetime(
        ventas["fecha"]
    ).dt.strftime("%Y-%m-%d")

    # Valores faltantes
    ventas.loc[[12, 87, 204], "producto_id"] = None
    ventas.loc[250, "vendedor"] = None

    # Producto inexistente
    ventas.loc[[45, 321], "producto_id"] = "P999"

    # Cantidades inválidas
    ventas.loc[33, "cantidad"] = -2
    ventas.loc[144, "cantidad"] = -4
    ventas.loc[402, "cantidad"] = 0

    # Precios inválidos
    ventas.loc[[75, 276], "precio_unitario"] = 0

    ventas.loc[[102, 340], "precio_unitario"] = (
        ventas.loc[[102, 340], "precio_unitario"] * 1.50
    )

    # Nombres de sucursal inconsistentes
    ventas.loc[60, "sucursal"] = " heredia "
    ventas.loc[160, "sucursal"] = "HEREDIA"
    ventas.loc[260, "sucursal"] = "san josé"

    # Fecha inválida
    ventas.loc[190, "fecha"] = "31/02/2026"

    # Cinco ventas duplicadas
    ventas_duplicadas = ventas.iloc[10:15].copy()

    ventas = pd.concat(
        [ventas, ventas_duplicadas],
        ignore_index=True,
    )

    return ventas


def crear_inventario(catalogo_limpio):
    """
    Crea el inventario por producto y sucursal.
    """

    sucursales = ["Heredia", "Alajuela", "San José"]
    registros = []

    responsables = {
        "Heredia": "Laura",
        "Alajuela": "Miguel",
        "San José": "Sofía",
    }

    for sucursal in sucursales:
        for producto_id in catalogo_limpio["producto_id"]:
            stock_sistema = int(
                generador.integers(20, 250)
            )

            stock_fisico = stock_sistema + int(
                generador.integers(-5, 6)
            )

            registros.append(
                {
                    "sucursal": sucursal,
                    "producto_id": producto_id,
                    "stock_sistema": stock_sistema,
                    "stock_fisico": stock_fisico,
                    "fecha_corte": pd.Timestamp("2026-06-30"),
                    "responsable": responsables[sucursal],
                }
            )

    inventario = pd.DataFrame(registros)

    # Errores intencionales
    inventario.loc[4, "stock_fisico"] = -8
    inventario.loc[17, "producto_id"] = None
    inventario.loc[26, "producto_id"] = " p007 "
    inventario.loc[32, "stock_fisico"] = (
        inventario.loc[32, "stock_sistema"] + 80
    )
    inventario.loc[41, "sucursal"] = "san josé"
    inventario.loc[52, "fecha_corte"] = "30/06/26"

    # Registro duplicado
    fila_duplicada = inventario.iloc[[7]].copy()

    inventario = pd.concat(
        [inventario, fila_duplicada],
        ignore_index=True,
    )

    return inventario


def guardar_inventario_excel(inventario, ruta_archivo):
    """
    Guarda el inventario en Excel con formato básico.
    """

    with pd.ExcelWriter(
        ruta_archivo,
        engine="openpyxl",
    ) as escritor:

        inventario.to_excel(
            escritor,
            sheet_name="Inventario",
            index=False,
        )

        hoja = escritor.book["Inventario"]

        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions

        color_encabezado = PatternFill(
            fill_type="solid",
            fgColor="1F4E78",
        )

        for celda in hoja[1]:
            celda.fill = color_encabezado
            celda.font = Font(
                color="FFFFFF",
                bold=True,
            )
            celda.alignment = Alignment(
                horizontal="center",
            )

        anchos = {
            "A": 16,
            "B": 16,
            "C": 18,
            "D": 16,
            "E": 16,
            "F": 18,
        }

        for columna, ancho in anchos.items():
            hoja.column_dimensions[columna].width = ancho


def ejecutar():
    catalogo_limpio, catalogo_con_errores = (
        crear_catalogo_productos()
    )

    ventas = crear_ventas(catalogo_limpio)
    inventario = crear_inventario(catalogo_limpio)

    ruta_catalogo = (
        RUTA_DATOS_ORIGINALES / "catalogo_productos.csv"
    )

    ruta_ventas = (
        RUTA_DATOS_ORIGINALES / "ventas.csv"
    )

    ruta_inventario = (
        RUTA_DATOS_ORIGINALES / "inventario.xlsx"
    )

    catalogo_con_errores.to_csv(
        ruta_catalogo,
        index=False,
        encoding="utf-8-sig",
    )

    ventas.to_csv(
        ruta_ventas,
        index=False,
        encoding="utf-8-sig",
    )

    guardar_inventario_excel(
        inventario,
        ruta_inventario,
    )

    print("ARCHIVOS GENERADOS CORRECTAMENTE")
    print(f"Catálogo: {len(catalogo_con_errores)} registros")
    print(f"Ventas: {len(ventas)} registros")
    print(f"Inventario: {len(inventario)} registros")
    print()
    print(f"Ubicación: {RUTA_DATOS_ORIGINALES}")
    print()
    print("Los archivos contienen errores intencionales.")
    print("No deben corregirse manualmente.")


if __name__ == "__main__":
    ejecutar()