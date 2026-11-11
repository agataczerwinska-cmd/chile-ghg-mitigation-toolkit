"""Solid waste disposal (IPCC category 4A / 5.A): First Order Decay model.

IPCC 2006, Vol. 5, Chapter 3. One waste type in one site type:

    Eq. 3.2  deposited DDOCm   = W x DOC x DOCf x MCF
    Eq. 3.4  stock(T)          = deposited(T) + stock(T-1) x e^-k
    Eq. 3.5  decomposed(T)     = stock(T-1) x (1 - e^-k)
    Eq. 3.6  CH4 generated(T)  = decomposed(T) x F x 16/12
    Eq. 3.1  CH4 emitted(T)    = (generated - recovered) x (1 - OX)

Waste deposited in year T starts emitting in year T+1.
"""

import math
from typing import Dict

import pandas as pd

from .combustion import GWP_AR5


def fod_series(
    waste_t_by_year: Dict[int, float],
    doc: float,
    k: float,
    mcf: float,
    docf: float = 0.5,
    f: float = 0.5,
    recovered_fraction: float = 0.0,
    ox: float = 0.0,
) -> pd.DataFrame:
    """Year-by-year landfill methane, in tonnes, indexed by year."""
    rows = []
    stock = 0.0
    decay = math.exp(-k)
    for year in sorted(waste_t_by_year):
        waste = waste_t_by_year[year]
        deposited = waste * doc * docf * mcf
        decomposed = stock * (1 - decay)
        stock = deposited + stock * decay
        generated = decomposed * f * 16 / 12
        recovered = generated * recovered_fraction
        emitted = (generated - recovered) * (1 - ox)
        rows.append(
            {
                "Año": year,
                "Residuos depositados (t)": waste,
                "DDOCm depositado (t C)": deposited,
                "DDOCm acumulado (t C)": stock,
                "DDOCm descompuesto (t C)": decomposed,
                "CH4 generado (t)": generated,
                "CH4 recuperado (t)": recovered,
                "CH4 emitido (t)": emitted,
                "Emisiones (t CO2e)": emitted * GWP_AR5["ch4"],
            }
        )
    return pd.DataFrame(rows).set_index("Año")


def half_life_years(k: float) -> float:
    """Time for half of the degradable carbon to decompose: ln(2) / k."""
    return math.log(2) / k
