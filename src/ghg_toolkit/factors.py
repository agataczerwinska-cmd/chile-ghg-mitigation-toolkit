"""Load the reference tables in /data as pandas DataFrames."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=None)
def load_emission_factors() -> pd.DataFrame:
    """IPCC 2006 Tier 1 combustion factors by category (kg gas / TJ), indexed by id."""
    return pd.read_csv(DATA_DIR / "emission_factors.csv", dtype={"ipcc_table": str}).set_index("id")


@lru_cache(maxsize=None)
def load_fuel_properties() -> pd.DataFrame:
    """Density and calorific values per fuel (Chile's BNE and IPCC), indexed by fuel."""
    return pd.read_csv(DATA_DIR / "fuel_properties.csv").set_index("fuel")


@lru_cache(maxsize=None)
def load_gwp() -> pd.DataFrame:
    """IPCC AR5 100-year global warming potentials, indexed by gas."""
    return pd.read_csv(DATA_DIR / "gwp_ar5.csv").set_index("gas")


@lru_cache(maxsize=None)
def load_conversions() -> pd.DataFrame:
    """Unit conversion factors (from_unit, to_unit, multiply_by)."""
    return pd.read_csv(DATA_DIR / "conversions.csv")


@lru_cache(maxsize=None)
def load_wood_density() -> pd.DataFrame:
    """Firewood density by species (kg per solid m3)."""
    return pd.read_csv(DATA_DIR / "wood_density.csv")


@lru_cache(maxsize=None)
def load_grid_factors() -> pd.DataFrame:
    """Electricity grid emission factors (kg CO2e/kWh), indexed by grid."""
    return pd.read_csv(DATA_DIR / "grid_emission_factors.csv").set_index("grid")


@lru_cache(maxsize=None)
def load_waste_parameters() -> pd.DataFrame:
    """Landfill model parameters (DOC, k, MCF, DOCf, F, OX)."""
    return pd.read_csv(DATA_DIR / "waste_parameters.csv")


@lru_cache(maxsize=None)
def load_forest_factors() -> pd.DataFrame:
    """Wood density, biomass expansion factor and root ratio by species."""
    return pd.read_csv(DATA_DIR / "forest_factors.csv").set_index("species")


TABLE_FILES = {
    "forest_factors.csv": load_forest_factors,
    "emission_factors.csv": load_emission_factors,
    "fuel_properties.csv": load_fuel_properties,
    "gwp_ar5.csv": load_gwp,
    "conversions.csv": load_conversions,
    "wood_density.csv": load_wood_density,
    "grid_emission_factors.csv": load_grid_factors,
    "waste_parameters.csv": load_waste_parameters,
}


def reload_tables() -> None:
    """Forget cached tables so edited CSV files are read again."""
    for loader in TABLE_FILES.values():
        loader.cache_clear()


def get_factor(factor_id: str) -> pd.Series:
    """Return one emission-factor row, with a helpful error if the id is unknown."""
    factors = load_emission_factors()
    if factor_id not in factors.index:
        raise KeyError(
            f"Unknown factor id '{factor_id}'. Available ids: {', '.join(factors.index)}"
        )
    return factors.loc[factor_id]


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert a value using data/conversions.csv, e.g. convert(2000, "GWh", "TJ")."""
    table = load_conversions()
    row = table[(table["from_unit"] == from_unit) & (table["to_unit"] == to_unit)]
    if row.empty:
        raise KeyError(f"No conversion stored from '{from_unit}' to '{to_unit}'")
    return value * float(row["multiply_by"].iloc[0])
