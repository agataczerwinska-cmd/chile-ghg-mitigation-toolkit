"""Calculation modes of the visual calculator.

To add a mode: create a file here with a render() function, then add one
line to MODES below. Nothing else needs to change.
"""

from . import combustion, electricity, forestry, waste

MODES = {
    "Combustión de combustibles": combustion,
    "Electricidad de la red": electricity,
    "Residuos: relleno sanitario": waste,
    "Forestal (UTCUTS): biomasa a CO2": forestry,
}

PLANNED = [
    "Agropecuario",
    "Huella de carbono (organizacional, comunal, eventos)",
    "Proyectos de mitigación y análisis económico",
    "Escenarios y proyección (taller)",
]
