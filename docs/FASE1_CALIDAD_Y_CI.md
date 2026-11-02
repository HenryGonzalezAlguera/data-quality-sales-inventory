# Fase 1 — Calidad, reproducibilidad y GitHub Actions

## Diagnóstico inicial

El repositorio ya contenía fuentes sintéticas, un notebook de análisis y seis salidas CSV procesadas, además de un dashboard PNG y reportes Excel. Sin embargo, no tenía pruebas automáticas ni integración continua. Las transformaciones y exportaciones estaban concentradas en un notebook de 40 celdas.

## Qué incorpora esta fase

- `src/validar_entregables.py`: comprobación **de solo lectura** de integridad, referencias, nulos, duplicados, fechas, precios, importes, stock y estados de conciliación; también revisa las hojas de ambos libros Excel y la presencia del dashboard.
- Línea base de resultados para **este dataset sintético con semilla 42**: 491 transacciones, ₡5,073,392.98 analizados y 51 diferencias de 58 inventarios, entre otros indicadores.
- `tests/test_calidad_datos.py`: casos positivos, datos inválidos intencionales y comparación de hashes de archivos generados en **una carpeta temporal**, sin sobrescribir los datos del repositorio durante la prueba.
- `requirements-dev.txt`: dependencias de CI para pytest y nbconvert.
- `.github/workflows/python-data-quality.yml`: ejecuta generación → notebook → verificación → pytest con Python 3.13 en cada PR y cambio en `main`.

## Reproducir desde PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

# ATENCIÓN: el generador SOBREESCRIBE las fuentes sintéticas en data/raw.
# Úsalo solo si no has personalizado esos archivos; respalda primero.
python src/generar_datos.py

# Ejecuta el notebook, actualizando CSV, XLSX y dashboard
python -m jupyter nbconvert --to notebook --execute notebooks/01_auditoria_calidad_datos.ipynb --output 01_auditoria_ci.ipynb

python -m src.validar_entregables
python -m pytest -q tests/
```

El comando nbconvert escribe su notebook ejecutado, y el notebook modifica los resultados procesados **del directorio donde se ejecuta**. La CI hace estas operaciones en un *runner efímero* y no publica ni hace commit de los archivos recreados.

## Semántica de las verificaciones

Los **KPI exactos** son exclusivos del escenario sintético que incluye el repositorio; no deben utilizarse como verdades universales para otros conjuntos de datos. Para verificar únicamente reglas de calidad en otro conjunto procesado compatible:

```powershell
python -m src.validar_entregables --sin-linea-base
```

La validación de estructura y reglas no sustituye inspección estadística, pruebas contra casos reales ni la revisión de la lógica del notebook. Esta fase **no extrae todavía las transformaciones a funciones importables**: esa será una siguiente mejora para facilitar mantenimiento, parametrización y pruebas unitarias más finas.
