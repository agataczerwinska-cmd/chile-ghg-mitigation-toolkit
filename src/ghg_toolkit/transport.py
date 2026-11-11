"""Road transport (IPCC category 1A3b), Tier 1.

Two entry points, depending on the activity data you have:

* fuel sold or consumed, in litres  -> emissions_from_fuel_volume
* distance driven and fuel economy  -> emissions_from_distance

Both convert to energy first:

    litres x density [kg/L] -> kg x PCI [MJ/kg] -> MJ / 1,000,000 -> TJ
"""

from typing import Optional

from .combustion import Emissions, combustion_emissions
from .factors import get_factor, load_fuel_properties

MJ_PER_TJ = 1_000_000


def litres_to_tj(
    litres: float,
    fuel: str,
    density_kg_per_l: Optional[float] = None,
    pci_source: str = "bne",
) -> float:
    """Convert a fuel volume to energy using density and net calorific value (PCI).

    pci_source="bne" uses Chile's Balance Nacional de Energía value (the course
    default); "ipcc" uses the IPCC 2006 world default.
    """
    if pci_source not in ("bne", "ipcc"):
        raise ValueError("pci_source must be 'bne' or 'ipcc'")
    props = load_fuel_properties().loc[fuel]
    if density_kg_per_l is None:
        if props["density_unit"] != "kg/L":
            raise ValueError(f"No density in kg/L stored for '{fuel}'; pass density_kg_per_l")
        density_kg_per_l = props["density"]
    if props[f"pci_{pci_source}_unit"] != "MJ/kg":
        raise ValueError(f"No {pci_source.upper()} calorific value in MJ/kg stored for '{fuel}'")
    return litres * density_kg_per_l * props[f"pci_{pci_source}"] / MJ_PER_TJ


def emissions_from_fuel_volume(
    litres: float,
    factor_id: str,
    density_kg_per_l: Optional[float] = None,
    pci_source: str = "bne",
) -> Emissions:
    """Emissions from a volume of fuel burned in a road vehicle.

    Example: emissions_from_fuel_volume(1000, "1A3b_gasolina_moderno")
    """
    fuel = get_factor(factor_id)["fuel"]
    return combustion_emissions(
        litres_to_tj(litres, fuel, density_kg_per_l, pci_source), factor_id
    )


def emissions_from_distance(
    km: float,
    litres_per_100km: float,
    factor_id: str,
    density_kg_per_l: Optional[float] = None,
    pci_source: str = "bne",
) -> Emissions:
    """Emissions from a distance driven at a given fuel economy (L/100 km)."""
    litres = km * litres_per_100km / 100
    return emissions_from_fuel_volume(litres, factor_id, density_kg_per_l, pci_source)
