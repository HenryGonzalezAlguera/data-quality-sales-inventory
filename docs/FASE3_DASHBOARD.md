# Fase 3 — Dashboard ejecutivo para GitHub y portafolio

## Objetivo

Mostrar **hallazgos de calidad de datos y operaciones comerciales** de manera
clara para puestos Data Analyst Junior y Python Junior, sin depender de un
servicio web ni de una captura generada manualmente.

La vista principal es [dashboard_ejecutivo.svg](../reports/figures/dashboard_ejecutivo.svg):
se trata de un **SVG estático reproducible**, no de un dashboard interactivo.
El [PNG exploratorio original](../reports/figures/dashboard_ventas_inventario.png)
sigue disponible con la tendencia mensual.

## Indicadores principales (datos sintéticos)

| Métrica | Resultado | Interpretación |
| --- | ---: | --- |
| Importe de ventas analizadas | ₡5,073,392.98 | Suma de importes válidos, **no flujo de caja real** |
| Transacciones limpias | 491 | Filas de ventas utilizadas tras aplicar reglas de calidad |
| Diferencias de inventario | 51 de 58 (87.9%) | Registros con stock físico distinto al stock del sistema |
| Impacto absoluto valorizado | ₡322,700.00 | Suma de valores absolutos de diferencia; **no pérdida neta** |

La vista también muestra:

- **Ventas por sucursal:** Heredia, San José y Alajuela.
- **Ventas por categoría:** Bebidas, Frutas, Granos, Congelados y Vegetales.
- **Impacto absoluto de inventario por sucursal:** Alajuela, San José y Heredia.
- **Distribución de conciliación:** 29 faltantes, 7 coincidencias y 22 sobrantes.

## Arquitectura

El módulo [`src/dashboard_ejecutivo.py`](../src/dashboard_ejecutivo.py)
separa tres responsabilidades:

1. `resumir_dashboard(ventas, inventario)`: agrega datos de pandas sin modificar los
   DataFrames originales; no utiliza KPI fijos como entrada.
2. `generar_dashboard_svg(resumen)`: construye SVG con título y descripción
   accesibles y **escapa** las etiquetas dinámicas antes de insertarlas en XML.
3. `guardar_dashboard(ventas, inventario, destino)`: escribe el SVG en la ruta
   seleccionada y devuelve el resumen calculado.

El notebook llama a estas funciones después de construir
`ventas_analisis` e `inventario_analisis`. No cambian las reglas de limpieza
ni las exportaciones históricas.

## Reproducir

Desde la carpeta raíz en PowerShell:

```powershell
# Solo regenera el SVG (sin tocar data/raw o los archivos Excel)
.\.venv\Scripts\python.exe -m src.dashboard_ejecutivo

# Verifica que coincide con los KPI y el SVG publicado
.\.venv\Scripts\python.exe -m pytest -q tests

# Comprueba integridad de entregables
.\.venv\Scripts\python.exe -m src.validar_entregables
```

**GitHub Actions** reconstruye los datos sintéticos en su runner efímero,
ejecuta el notebook, compara el SVG regenerado con el archivo versionado y
valida métricas y pruebas.

## Transparencia y limitaciones

- El análisis representa **datos sintéticos**. No permite inferir resultados
  de comercios reales.
- El impacto absoluto suma desviaciones independientemente de su signo.
  **No equivale a faltantes netos, pérdida contable ni valor recuperable.**
- Los indicadores no distinguen pagos cobrados, devoluciones o impuestos.
- Es un dashboard **estático** para README; no tiene filtros interactivos,
  actualización en tiempo real, servidores ni autenticación.
- El PNG original del análisis conserva el gráfico de tendencia mensual y puede
  servir como evidencia complementaria.

## Propuesta de lectura para una entrevista

Se detectan diferencias en 51 de 58 registros de inventario; en términos
monetarios, el mayor impacto absoluto se concentra en Alajuela. Conviene
priorizar allí la revisión de movimientos, ajustes de stock y conteos cíclicos.
Es una **recomendación analítica** sobre el escenario sintético, no evidencia
de fraude ni de pérdidas económicas definitivas.
