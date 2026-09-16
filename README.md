# Auditoría y conciliación de datos de ventas e inventario

Proyecto de análisis de datos desarrollado con Python, pandas, Excel y Power Query. Su objetivo es detectar problemas de calidad, limpiar información comercial y analizar diferencias entre el inventario registrado en el sistema y el conteo físico.

Los datos son sintéticos y contienen errores intencionales para simular un escenario empresarial real.

## Dashboard

![Dashboard de ventas e inventario](reports/figures/dashboard_ventas_inventario.png)

## Resultados principales

- **491** transacciones válidas analizadas.
- **₡5,073,392.98** en ingresos.
- **3,578** unidades vendidas.
- **20** productos comercializados.
- **51 de 58** registros de inventario presentaron diferencias.
- **87.9%** del inventario analizado tuvo inconsistencias.
- **230 unidades** de diferencia absoluta.
- **₡322,700.00** de impacto monetario absoluto.

## Objetivos

- Auditar diferentes fuentes de datos.
- Detectar valores faltantes, duplicados y formatos inconsistentes.
- Comprobar la integridad entre ventas, inventario y catálogo.
- Aplicar reglas de limpieza documentadas.
- Conciliar el stock del sistema con el conteo físico.
- Construir indicadores y visualizaciones.
- Generar archivos preparados para Excel y Power Query.

## Fuentes de datos

El proyecto utiliza tres fuentes sintéticas:

- `catalogo_productos.csv`: catálogo maestro de productos.
- `ventas.csv`: transacciones comerciales.
- `inventario.xlsx`: existencias registradas y conteos físicos.

Los archivos originales se encuentran en `data/raw`.

## Problemas identificados

Durante la auditoría se detectaron:

- Registros duplicados.
- Valores faltantes.
- Fechas inválidas.
- Cantidades iguales o menores que cero.
- Precios inválidos.
- Productos inexistentes en el catálogo.
- Variaciones de mayúsculas, minúsculas y espacios.
- Existencias físicas negativas.
- Diferencias entre el stock del sistema y el conteo físico.

## Proceso aplicado

1. Carga de archivos CSV y Excel.
2. Análisis de estructura y tipos de datos.
3. Detección de valores faltantes.
4. Identificación de duplicados.
5. Validación de fechas, precios y cantidades.
6. Comprobación de integridad referencial.
7. Normalización de categorías y sucursales.
8. Tratamiento de errores recuperables.
9. Exclusión de registros no recuperables.
10. Conciliación de inventario.
11. Validación final automatizada.
12. Exportación y visualización de resultados.

## Criterios de limpieza

- Los duplicados exactos fueron eliminados.
- Los textos fueron normalizados para corregir espacios y diferencias de escritura.
- Los nombres descriptivos faltantes se reemplazaron con etiquetas controladas.
- Los precios inválidos del catálogo se corrigieron utilizando la mediana de su categoría.
- Los precios inválidos de ventas se reemplazaron con el precio estándar del catálogo.
- Las ventas sin producto identificable, con fechas inválidas o cantidades no positivas fueron excluidas.
- Los registros de inventario con identificadores faltantes o existencias físicas negativas fueron excluidos.

Los archivos originales no fueron modificados.

## Hallazgos comerciales

### Sucursales

| Sucursal | Ingresos | Participación |
|---|---:|---:|
| Heredia | ₡1,734,179.99 | 34.18% |
| San José | ₡1,724,364.79 | 33.99% |
| Alajuela | ₡1,614,848.20 | 31.83% |

Heredia lideró los ingresos, aunque la distribución entre las tres sucursales fue equilibrada.

### Productos con mayores ingresos

| Producto | Categoría | Unidades | Ingresos |
|---|---|---:|---:|
| Pulpa de Fresa | Congelados | 216 | ₡505,639.81 |
| Jugo de Piña | Bebidas | 218 | ₡371,059.10 |
| Pulpa de Mango | Congelados | 154 | ₡353,381.20 |
| Jugo de Naranja | Bebidas | 183 | ₡320,626.39 |
| Té Frío | Bebidas | 254 | ₡308,057.12 |

Las categorías Bebidas y Congelados concentran los productos con mayores ingresos.

## Conciliación de inventario

| Sucursal | Productos revisados | Con diferencias | Impacto absoluto |
|---|---:|---:|---:|
| Alajuela | 20 | 17 | ₡179,600.00 |
| San José | 20 | 18 | ₡87,900.00 |
| Heredia | 18 | 16 | ₡55,200.00 |

Alajuela presentó el mayor impacto monetario, mientras que San José tuvo el mayor porcentaje de productos con diferencias.

## Recomendaciones

- Implementar conteos cíclicos de inventario.
- Priorizar la revisión de Alajuela y San José.
- Investigar los productos con mayor impacto monetario.
- Automatizar la conciliación entre el sistema y el conteo físico.
- Establecer validaciones obligatorias durante la captura de datos.
- Mantener catálogos maestros de productos y sucursales.
- Crear alertas para diferencias superiores a límites definidos.

## Tecnologías utilizadas

- Python 3.13
- pandas
- NumPy
- Matplotlib
- Seaborn
- Jupyter Notebook
- Excel
- Power Query
- openpyxl
- Git y GitHub

## Estructura del proyecto

```text
data-quality-sales-inventory/
├── data/
│   ├── raw/
│   │   ├── catalogo_productos.csv
│   │   ├── ventas.csv
│   │   └── inventario.xlsx
│   └── processed/
│       ├── catalogo_productos_limpio.csv
│       ├── ventas_limpias.csv
│       ├── inventario_conciliado.csv
│       ├── ventas_analisis.csv
│       ├── inventario_analisis.csv
│       └── datos_procesados.xlsx
├── notebooks/
│   └── 01_auditoria_calidad_datos.ipynb
├── reports/
│   ├── figures/
│   │   └── dashboard_ventas_inventario.png
│   └── reporte_analisis.xlsx
├── src/
│   └── generar_datos.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Cómo ejecutar el proyecto

### 1. Crear el entorno virtual

```powershell
py -m venv .venv
```

### 2. Activar el entorno

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias

```powershell
python -m pip install -r requirements.txt
```

### 4. Generar los datos sintéticos

```powershell
python src/generar_datos.py
```

### 5. Ejecutar el notebook

Abrir:

```text
notebooks/01_auditoria_calidad_datos.ipynb
```

Seleccionar el entorno `.venv` como kernel y ejecutar todas las celdas.

## Archivos finales

- `datos_procesados.xlsx`: datos limpios para Excel y Power Query.
- `reporte_analisis.xlsx`: indicadores, rankings y tablas detalladas.
- `dashboard_ventas_inventario.png`: resumen visual.
- `01_auditoria_calidad_datos.ipynb`: proceso completo y reproducible.

## Autor

**Henry González Alguera**  
Estudiante de Ingeniería en Sistemas  
Costa Rica

## Aviso

Este proyecto utiliza exclusivamente datos sintéticos creados con fines académicos y de portafolio. No contiene información real, personal ni confidencial.