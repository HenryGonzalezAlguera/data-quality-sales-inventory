"""Regresión de la documentación pública del portafolio.

No hace requests HTTP; comprueba enlaces locales y evita referencias a archivos
inexistentes o afirmaciones que contradigan el alcance de la demo sintética.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd

from src.informe_ejecutivo import analizar_hallazgos

RAIZ = Path(__file__).resolve().parents[1]
DOCUMENTOS = [
    RAIZ / "README.md",
    RAIZ / "docs/GUIA_DEMO.md",
    RAIZ / "docs/PUBLICACION_LINKEDIN.md",
    RAIZ / "docs/INFORME_EJECUTIVO.md",
]


def test_enlaces_locales_de_documentacion_existen():
    patron = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
    for documento in DOCUMENTOS:
        assert documento.is_file(), str(documento)
        for raw in patron.findall(documento.read_text(encoding="utf-8")):
            direccion = raw.strip().split("#", 1)[0]
            if not direccion or re.match(r"^(https?://|mailto:)", direccion):
                continue
            # Los enlaces de Markdown son relativos al archivo que los contiene.
            destino = (documento.parent / direccion).resolve()
            assert destino.is_relative_to(RAIZ.resolve()), f"Enlace fuera del repositorio: {raw}"
            assert destino.exists(), f"{documento}: enlace inexistente {raw}"


def test_portafolio_tiene_evidencia_visual_y_limites_explicitos():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert "reports/figures/dashboard_ejecutivo.svg" in readme
    assert "docs/INFORME_EJECUTIVO.md" in readme
    assert "docs/GUIA_DEMO.md" in readme
    assert "datos son **sintéticos**" in readme
    assert "no representa una pérdida contable comprobada" in readme
    assert "GitHub Actions" in readme
    assert "₡5,073,392.98" in readme
    assert "51 de 58" in readme


def test_fechas_invalidas_se_rechazan_sin_advertencias():
    ventas = pd.read_csv(RAIZ / "data/processed/ventas_analisis.csv",
                        encoding="utf-8-sig")
    inventario = pd.read_csv(RAIZ / "data/processed/inventario_analisis.csv",
                            encoding="utf-8-sig")
    ventas.loc[0, "fecha"] = "fecha-invalida"
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        try:
            analizar_hallazgos(ventas, inventario)
        except ValueError as error:
            assert "fechas inválidas" in str(error)
        else:
            raise AssertionError("Una fecha inválida debería rechazarse")
    assert not any(isinstance(aviso.message, UserWarning)
                   for aviso in avisos), "Pandas emitió una advertencia de formato"
