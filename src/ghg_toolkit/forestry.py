"""Forest land (UTCUTS / LULUCF): from wood volume to CO2.

IPCC 2006 method with Chile's national factors (INGEI; Gayoso et al. 2002):

    CO2 = V x D x FEB x (1 + R) x FC x 44/12

    V    wood volume (m3)
    D    basic wood density (t dry matter / m3)
    FEB  biomass expansion factor (stem -> whole above-ground tree)
    R    root-to-shoot ratio
    FC   carbon fraction of dry matter (0.5)

The same chain gives a removal (growth) or an emission (harvest, firewood,
fire); only the sign changes.
"""

from typing import Optional

import pandas as pd

from .factors import load_forest_factors

CARBON_FRACTION = 0.5
C_TO_CO2 = 3.667


def breakdown_from_wood_volume(
    volume_m3: float,
    species: str,
    removal: bool = False,
    overrides: Optional[dict] = None,
    _first_rows: Optional[list] = None,
) -> pd.DataFrame:
    """Table with every step from m3 of wood to t CO2.

    removal=True reports the result as a capture (negative emission).
    `overrides` keys: "density", "feb", "root_ratio", "carbon_fraction".
    """
    own = overrides or {}
    OWN = "dato propio"
    f = load_forest_factors().loc[species]
    density = float(own.get("density", f["density_t_m3"]))
    feb = float(own.get("feb", f["feb"]))
    root = float(own.get("root_ratio", f["root_ratio"]))
    fc = float(own.get("carbon_fraction", CARBON_FRACTION))
    national = str(f["source"])

    stem = volume_m3 * density
    above = stem * feb
    total_biomass = above * (1 + root)
    carbon = total_biomass * fc
    co2 = carbon * C_TO_CO2
    sign = -1 if removal else 1

    rows = list(_first_rows) if _first_rows else [("Volumen de madera", volume_m3, "m3", "dato")]
    rows += [
        (f"Densidad ({species})", density, "t/m3", OWN if "density" in own else national),
        ("Biomasa del fuste", stem, "t materia seca", "m3 × densidad"),
        ("Factor de expansión de biomasa (FEB)", feb, "–", OWN if "feb" in own else national),
        ("Biomasa aérea", above, "t materia seca", "biomasa del fuste × FEB"),
        ("Proporción de raíces (R)", root, "–", OWN if "root_ratio" in own else national),
        ("Biomasa total (aérea + raíces)", total_biomass, "t materia seca", "biomasa aérea × (1 + R)"),
        ("Fracción de carbono (FC)", fc, "t C/t materia seca", OWN if "carbon_fraction" in own else "IPCC 2006"),
        ("Carbono", carbon, "t C", "biomasa total × FC"),
        ("Conversión de C a CO2", C_TO_CO2, "t CO2/t C", "44 ÷ 12"),
        ("CO2 capturado" if removal else "CO2 emitido", co2, "t CO2", "t C × 3,667"),
        ("TOTAL", sign * co2 * 1000, "kg CO2e", "captura: signo negativo" if removal else "t CO2 × 1000"),
        ("TOTAL", sign * co2, "t CO2e", "captura: signo negativo" if removal else "emisión"),
    ]
    df = pd.DataFrame(rows, columns=["Paso", "Valor", "Unidad", "Cálculo / fuente"])
    df["Valor"] = df["Valor"].astype(float)
    df.index = range(1, len(df) + 1)
    return df


def breakdown_from_forest_growth(
    area_ha: float,
    growth_m3_ha_year: float,
    species: str,
    overrides: Optional[dict] = None,
) -> pd.DataFrame:
    """Annual capture of a forest area growing at a given rate (m3/ha/year)."""
    volume = area_ha * growth_m3_ha_year
    first = [
        ("Superficie", area_ha, "ha", "dato"),
        ("Crecimiento anual", growth_m3_ha_year, "m3/ha/año", "dato"),
        ("Volumen que crece en un año", volume, "m3", "ha × m3/ha/año"),
    ]
    return breakdown_from_wood_volume(volume, species, True, overrides, first)
