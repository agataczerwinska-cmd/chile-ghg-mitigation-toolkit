"""Emission factor of an electricity system built from its power plants.

    grid factor (kg CO2e/kWh) = emissions of all plants / electricity generated

Each fossil plant is described either by the fuel it burned in the year or by
its generation and efficiency:

    fuel energy (TJ) = generation (MWh) x 0.0036 / efficiency

Renewable plants (solar, wind, hydro, geothermal) count as zero emissions.
"""

from typing import List, Optional

import pandas as pd

from .breakdown import breakdown_from_quantity, total_of

TJ_PER_MWH = 0.0036
RENEWABLE = "renovable"


def plant_emissions(
    factor_id: str,
    generation_mwh: float,
    efficiency: Optional[float] = None,
    fuel_quantity: Optional[float] = None,
    fuel_unit: Optional[str] = None,
    pci_source: str = "bne",
) -> float:
    """kg CO2e of one plant in a year. Efficiency is a fraction (0.38 = 38%)."""
    if factor_id == RENEWABLE:
        return 0.0
    if fuel_quantity:
        if not fuel_unit:
            raise ValueError("fuel_unit is needed with fuel_quantity")
        return total_of(breakdown_from_quantity(fuel_quantity, fuel_unit, factor_id, pci_source))
    if not efficiency:
        raise ValueError("Give the fuel burned or the plant's efficiency")
    fuel_tj = generation_mwh * TJ_PER_MWH / efficiency
    return total_of(breakdown_from_quantity(fuel_tj, "TJ", factor_id, pci_source))


def grid_factor(plants: List[dict], losses: float = 0.0, pci_source: str = "bne") -> dict:
    """Grid factor from a list of plants.

    Each plant: {"name", "factor_id", "generation_mwh", "efficiency" (fraction, optional),
    "fuel_quantity" and "fuel_unit" (optional)}. `losses` is the fraction of the
    electricity lost in transmission and distribution (0.05 = 5%).
    """
    rows = []
    for p in plants:
        kg = plant_emissions(
            p["factor_id"],
            p["generation_mwh"],
            p.get("efficiency"),
            p.get("fuel_quantity"),
            p.get("fuel_unit"),
            pci_source,
        )
        rows.append({"name": p["name"], "generation_mwh": p["generation_mwh"], "emissions_t": kg / 1000})
    plants_df = pd.DataFrame(rows)
    generation = plants_df["generation_mwh"].sum()
    emissions = plants_df["emissions_t"].sum()
    if generation <= 0:
        raise ValueError("Total generation must be positive")
    plants_df["intensity_kg_kwh"] = plants_df["emissions_t"] / plants_df["generation_mwh"].where(plants_df["generation_mwh"] > 0)
    plants_df["share_generation"] = plants_df["generation_mwh"] / generation
    plants_df["share_emissions"] = plants_df["emissions_t"] / emissions if emissions else 0.0
    generation_factor = emissions / generation  # t/MWh = kg/kWh
    if not 0 <= losses < 1:
        raise ValueError("losses must be between 0 and 1")
    return {
        "plants": plants_df,
        "generation_mwh": generation,
        "emissions_t": emissions,
        "factor_generation": generation_factor,
        "factor_consumption": generation_factor / (1 - losses),
    }
