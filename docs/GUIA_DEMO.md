# Data Quality — Guía de demo para portafolio

## Objetivo

Presentar de manera verificable el proceso completo de análisis de datos: problema, limpieza, conciliación, visualización, hallazgos y acciones. **Los datos son sintéticos**. El dashboard es una imagen SVG estática, no una aplicación interactiva ni un servicio en Internet.

## Antes de mostrarlo

- Tener disponible el repositorio y su [README](../README.md).
- Verificar [GitHub Actions](https://github.com/HenryGonzalezAlguera/data-quality-sales-inventory/actions/workflows/python-data-quality.yml) y el notebook del proyecto.
- Revisar los indicadores del [informe ejecutivo](INFORME_EJECUTIVO.md) y el [SVG](../reports/figures/dashboard_ejecutivo.svg).
- No enseñar rutas personales del equipo, datos reales de clientes, contraseñas o conversaciones privadas. No afirmar que el sistema es una herramienta empresarial desplegada.

## Recorrido de 4 minutos

| Momento | Acción | Habilidad demostrada |
| --- | --- | --- |
| 0:00–0:40 | Mostrar el problema: tres archivos sintéticos con errores intencionales. | Data profiling y definición de reglas |
| 0:40–1:25 | Abrir `src/procesamiento.py` y explicar la normalización, duplicados y tratamiento de errores. | Python, pandas, calidad y ETL |
| 1:25–2:05 | Mostrar `src/validar_entregables.py` y las pruebas de `pytest`. | Data validation y testing |
| 2:05–3:00 | Mostrar el SVG y comparar ventas e inventario por sucursal. | Data visualization y KPI |
| 3:00–3:35 | Explicar el hallazgo Alajuela/P013 y la recomendación de conteo cíclico. | Business insight y priorización |
| 3:35–4:00 | Enseñar el resultado de GitHub Actions y el informe generado. | Automatización y reproducibilidad |

## Verificaciones rápidas en PowerShell

Dentro de la carpeta raíz del repositorio y con un entorno `.venv` preparado:

```powershell
.\.venv\Scripts\python.exe -m src.validar_entregables
.\.venv\Scripts\python.exe -m src.informe_ejecutivo --verificar
.\.venv\Scripts\python.exe -m pytest -q tests
```

Esos comandos no regeneran `data/raw`. Si deseas reconstruir el dashboard vectorial (solo modifica el SVG de salida):

```powershell
.\.venv\Scripts\python.exe -m src.dashboard_ejecutivo
```

**Precaución:** ejecutar `python src/generar_datos.py` sobrescribe los datos sintéticos originales. Ejecutar el notebook completo también puede sobrescribir productos procesados y reportes. El flujo de GitHub Actions hace esto en un entorno temporal.

## Respuestas breves para entrevistas

**¿Qué encontraste?** 51 de 58 registros de inventario difieren entre el stock físico y el del sistema. El mayor impacto absoluto está en Alajuela, y la mayor desviación individual es P013 (Lentejas).

**¿Cómo priorizaste?** Clasifiqué cada diferencia por valor absoluto, revisé la concentración por sucursal y propuse verificar primero el producto de mayor impacto, seguido de conteos cíclicos y controles de captura.

**¿Es una pérdida real de ₡322,700?** No. Es la suma de diferencias valorizadas absolutas del escenario sintético. El resultado neto es distinto, y ninguno implica por sí solo una pérdida contable real.

**¿Cómo garantizas la calidad?** Las reglas de limpieza son funciones reutilizables de pandas; el validador verifica referencialidad, importes y stock; `pytest` cubre casos válidos e inválidos; GitHub Actions ejecuta el notebook completo y detecta salidas desactualizadas.

**¿Qué mejorarías con datos de una empresa real?** Diccionario de datos, fuentes trazables, reglas de negocio acordadas, registros de correcciones, pipeline programado, controles de acceso, métricas periódicas y revisión del impacto con responsables de operaciones.

## Enlaces útiles

[README](../README.md) · [Informe ejecutivo](INFORME_EJECUTIVO.md) · [Dashboard](../reports/figures/dashboard_ejecutivo.svg) · [Notebook](../notebooks/01_auditoria_calidad_datos.ipynb) · [Pruebas](../tests/) · [Publicación LinkedIn](PUBLICACION_LINKEDIN.md)
