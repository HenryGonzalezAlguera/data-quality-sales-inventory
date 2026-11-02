# Informe ejecutivo — Calidad de datos de ventas e inventario

> **Caso sintético de portafolio.** Los valores representan datos inventados y no deben interpretarse como resultados de una empresa real.

## Resumen ejecutivo

Se analizaron **491 transacciones válidas** entre **2026-01-01 y 2026-06-30**, con importes por **₡5,073,392.98** y **3,578 unidades vendidas**.
En inventario, **51 de 58 registros** (87.93%) mostraron diferencias entre el sistema y el conteo físico.
La suma de desviaciones absolutas valorizadas fue **₡322,700.00**; no equivale a pérdida contable ni al faltante neto.

## 1. Desempeño de ventas por sucursal

| Sucursal | Transacciones | Unidades | Importe analizado | Participación |
| --- | ---: | ---: | ---: | ---: |
| Heredia | 160 | 1,185 | ₡1,734,179.99 | 34.18% |
| San José | 167 | 1,230 | ₡1,724,364.79 | 33.99% |
| Alajuela | 164 | 1,163 | ₡1,614,848.20 | 31.83% |

Las diferencias de importe entre sucursales no demuestran por sí solas diferencias de rentabilidad: no se analizan costos operativos ni cobros reales.

## 2. Categorías y productos destacados

| Categoría | Importe analizado | Participación |
| --- | ---: | ---: |
| Bebidas | ₡1,255,502.60 | 24.75% |
| Frutas | ₡1,092,631.09 | 21.54% |
| Granos | ₡1,085,785.86 | 21.40% |
| Congelados | ₡859,021.01 | 16.93% |
| Vegetales | ₡780,452.42 | 15.38% |

**Cinco productos con mayor importe:**

| Producto | Unidades vendidas | Importe |
| --- | ---: | ---: |
| P020 — Pulpa De Fresa | 216 | ₡505,639.81 |
| P016 — Jugo De Piña | 218 | ₡371,059.10 |
| P019 — Pulpa De Mango | 154 | ₡353,381.20 |
| P015 — Jugo De Naranja | 183 | ₡320,626.39 |
| P018 — Té Frío | 254 | ₡308,057.12 |

## 3. Conciliación de inventario por sucursal

| Sucursal | Revisados | Con diferencia | % con diferencia | Impacto absoluto | % del impacto total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alajuela | 20 | 17 | 85.00% | ₡179,600.00 | 55.66% |
| San José | 20 | 18 | 90.00% | ₡87,900.00 | 27.24% |
| Heredia | 18 | 16 | 88.89% | ₡55,200.00 | 17.11% |

**Magnitudes distintas:** desviación absoluta de **230 unidades**, frente a una **diferencia neta de +60 unidades**; valor absoluto **₡322,700.00** frente a valor neto **₡87,900.00**.
La compensación de sobrantes y faltantes no elimina la necesidad de revisar cada discrepancia.

### Mayor discrepancia individual

**Alajuela · P013 — Lentejas**: stock del sistema **193**, stock físico **273**, diferencia **+80 unidades (Sobrante)** e impacto absoluto **₡116,000.00** (35.95% del impacto total).

## 4. Plan de acción sugerido

| Prioridad | Acción propuesta | Responsable sugerido | Indicador de seguimiento |
| --- | --- | --- | --- |
| Alta | Revisar primero la discrepancia individual de mayor impacto: conteo independiente y movimientos de entrada/salida. | Encargado de inventario | Diferencia en unidades y valor conciliado |
| Alta | Implementar conteos cíclicos en la sucursal con mayor impacto absoluto; documentar causas y correcciones. | Operaciones y almacén | % de registros con diferencia e impacto absoluto |
| Media | Estandarizar captura de fechas, cantidades, IDs y precios; rechazar datos inválidos antes del análisis. | Responsable de datos | Errores por regla y registros descartados |
| Media | Monitorear semanalmente sucursales y productos de mayor importe, sin asumir márgenes o rentabilidad. | Analista comercial | Importe por sucursal/categoría y transacciones válidas |

## 5. Metodología y límites

- **Origen:** CSV de ventas/catálogo y Excel de inventario sintéticos; datos transformados por `src/procesamiento.py`.
- **Reglas:** normalización de etiquetas, deduplicación, validación de fechas, cantidades y referencias; conciliación por stock físico menos stock del sistema.
- **Fórmulas:** importe de venta = cantidad × precio unitario; diferencia = stock físico − stock del sistema; impacto absoluto = |diferencia × precio estándar|.
- **No inferencias:** los datos no evidencian fraude, pérdida real, causas de diferencias, impuestos, costos ni cobros efectivamente recibidos.
- **Reproducibilidad:** `python -m src.informe_ejecutivo` regenera este documento desde los archivos procesados. `python -m pytest -q tests` verifica los hallazgos.

---

Informe generado automáticamente desde `data/processed/ventas_analisis.csv` e `data/processed/inventario_analisis.csv`. No incluye datos personales ni fuentes empresariales reales.
