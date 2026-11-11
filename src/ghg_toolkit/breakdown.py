"""Step-by-step tables: the same calculation chain you would lay out in Excel.

    km -> L -> kg -> MJ -> TJ -> kg of each gas -> kg CO2e

Every row has the value, its unit and the formula that produced it.
"""

from typing import Dict, Optional

import pandas as pd

from .combustion import GWP_AR5, Emissions
from .factors import get_factor, load_fuel_properties

MJ_PER_TJ = 1_000_000
PCI_LABEL = {"bne": "PCI Chile (BNE)", "ipcc": "PCI por defecto IPCC 2006"}


def units_for(factor_id: str) -> list:
    """Units you can enter the fuel quantity in, for this emission-factor row."""
    props = load_fuel_properties().loc[get_factor(factor_id)["fuel"]]
    pci_units = {props["pci_bne_unit"], props["pci_ipcc_unit"]}
    units = []
    if props["pci_bne_unit"] == "MJ/m3":
        units.append("m3")  # gases: Chile reports them by volume
    if "MJ/kg" in pci_units:
        if props["density_unit"] == "kg/L":
            units.append("L")
        units += ["kg", "t"]
    if "MJ/m3" in pci_units and "m3" not in units:
        units.append("m3")
    return units + ["MJ", "TJ"]


def breakdown_from_quantity(
    quantity: float,
    unit: str,
    factor_id: str,
    pci_source: str = "bne",
    _first_rows: Optional[list] = None,
    overrides: Optional[dict] = None,
    units: float = 1,
) -> pd.DataFrame:
    """Table with every step from a fuel quantity (L, kg, t, m3, MJ or TJ) to kg CO2e.

    `units` is the number of identical machines or vehicles; `quantity` is per unit.

    `overrides` replaces default values with your own (Tier 2 or plant data).
    Keys: "density", "pci", "ef_co2", "ef_ch4", "ef_n2o".

    Works for any row of data/emission_factors.csv, so it covers every
    combustion sector: power plants, industry, transport, households.
    If the Chilean (BNE) calorific value is missing, the IPCC one is used.
    """
    if unit not in units_for(factor_id):
        raise ValueError(f"Unit '{unit}' not available for '{factor_id}'. Use one of {units_for(factor_id)}")
    if pci_source not in PCI_LABEL:
        raise ValueError("pci_source must be 'bne' or 'ipcc'")
    own = overrides or {}
    OWN = "dato propio (Nivel 2)"
    ef = get_factor(factor_id).copy()
    for gas in ("co2", "ch4", "n2o"):
        if f"ef_{gas}" in own:
            ef[f"ef_{gas}_kg_tj"] = own[f"ef_{gas}"]
    props = load_fuel_properties().loc[ef["fuel"]]
    if _first_rows:
        rows = list(_first_rows)
    elif units != 1:
        rows = [
            ("Combustible por unidad", quantity, unit, "dato"),
            ("Número de unidades", units, "–", "dato"),
            ("Combustible consumido", quantity * units, unit, "por unidad × número de unidades"),
        ]
        quantity = quantity * units
    else:
        rows = [("Combustible consumido", quantity, unit, "dato")]

    if unit in ("MJ", "TJ"):
        mj = quantity if unit == "MJ" else quantity * MJ_PER_TJ
    else:
        wanted = "MJ/m3" if unit == "m3" else "MJ/kg"
        source = pci_source if props[f"pci_{pci_source}_unit"] == wanted else (
            "ipcc" if pci_source == "bne" else "bne"
        )
        pci = float(own.get("pci", props[f"pci_{source}"]))
        amount = quantity
        if unit == "L":
            density = float(own.get("density", props["density"]))
            amount = quantity * density
            rows += [
                (f"Densidad ({props['name']})", density, "kg/L", OWN if "density" in own else "tabla de combustibles"),
                ("Masa de combustible", amount, "kg", "L × densidad"),
            ]
        elif unit == "t":
            amount = quantity * 1000
            rows.append(("Masa de combustible", amount, "kg", "t × 1000"))
        rows.append(("Poder calorífico inferior", pci, wanted, OWN if "pci" in own else PCI_LABEL[source]))
        mj = amount * pci
    tj = mj / MJ_PER_TJ
    if unit != "MJ":
        rows.append(("Energía", mj, "MJ", "TJ × 1.000.000" if unit == "TJ" else f"{'m3' if unit == 'm3' else 'kg'} × PCI"))
    if unit != "TJ":
        rows.append(("Energía", tj, "TJ", "MJ ÷ 1.000.000"))

    co2 = tj * ef["ef_co2_kg_tj"]
    ch4 = tj * ef["ef_ch4_kg_tj"]
    n2o = tj * ef["ef_n2o_kg_tj"]
    biogenic = bool(ef["biogenic_co2"])
    co2e = (0 if biogenic else co2) + ch4 * GWP_AR5["ch4"] + n2o * GWP_AR5["n2o"]
    table = f"IPCC 2006, Vol. 2, tabla {ef['ipcc_table']}"
    rows += [
        ("Factor de emisión CO2", ef["ef_co2_kg_tj"], "kg CO2/TJ", OWN if "ef_co2" in own else "IPCC 2006, Vol. 2, tabla 1.4"),
        ("Emisiones CO2" + (" (biogénico, memo)" if biogenic else ""), co2, "kg CO2", "TJ × FE CO2"),
        ("Factor de emisión CH4", ef["ef_ch4_kg_tj"], "kg CH4/TJ", OWN if "ef_ch4" in own else table),
        ("Emisiones CH4", ch4, "kg CH4", "TJ × FE CH4"),
        ("Factor de emisión N2O", ef["ef_n2o_kg_tj"], "kg N2O/TJ", OWN if "ef_n2o" in own else table),
        ("Emisiones N2O", n2o, "kg N2O", "TJ × FE N2O"),
        ("CH4 en CO2e", ch4 * GWP_AR5["ch4"], "kg CO2e", f"kg CH4 × {GWP_AR5['ch4']} (PCG AR5)"),
        ("N2O en CO2e", n2o * GWP_AR5["n2o"], "kg CO2e", f"kg N2O × {GWP_AR5['n2o']} (PCG AR5)"),
        ("TOTAL", co2e, "kg CO2e", "CH4 + N2O en CO2e" if biogenic else "CO2 + CH4 + N2O en CO2e"),
        ("TOTAL", co2e / 1000, "t CO2e", "kg CO2e ÷ 1000"),
    ]
    df = pd.DataFrame(rows, columns=["Paso", "Valor", "Unidad", "Cálculo / fuente"])
    df["Valor"] = df["Valor"].astype(float)
    df.index = range(1, len(df) + 1)
    return df


def breakdown_from_fuel_volume(
    litres: float, factor_id: str, pci_source: str = "bne"
) -> pd.DataFrame:
    """Table with every step from litres of fuel to kg CO2e."""
    return breakdown_from_quantity(litres, "L", factor_id, pci_source)


def breakdown_from_distance(
    km: float,
    litres_per_100km: float,
    factor_id: str,
    pci_source: str = "bne",
    overrides: Optional[dict] = None,
    units: float = 1,
) -> pd.DataFrame:
    """Table with every step from kilometres driven to kg CO2e.

    `units` is the number of identical vehicles; `km` is per vehicle.
    """
    first = []
    if units != 1:
        first = [
            ("Distancia por unidad", km, "km", "dato"),
            ("Número de unidades", units, "–", "dato"),
        ]
        km = km * units
    litres = km * litres_per_100km / 100
    first += [
        ("Distancia recorrida", km, "km", "por unidad × número de unidades" if units != 1 else "dato"),
        ("Rendimiento", litres_per_100km, "L/100 km", "dato"),
        ("Combustible consumido", litres, "L", "km × L/100 km ÷ 100"),
    ]
    return breakdown_from_quantity(litres, "L", factor_id, pci_source, first, overrides)


def total_of(table: pd.DataFrame, unit: str = "kg CO2e") -> float:
    """Read the TOTAL row of a breakdown table."""
    return float(table[(table["Paso"] == "TOTAL") & (table["Unidad"] == unit)]["Valor"].iloc[0])


def compare(scenarios: Dict[str, Emissions]) -> pd.DataFrame:
    """Side-by-side table of scenarios; the first one is the reference."""
    df = pd.DataFrame({name: e.as_dict() for name, e in scenarios.items()}).T
    df = df.rename(
        columns={
            "co2_kg": "CO2 (kg)",
            "ch4_kg": "CH4 (kg)",
            "n2o_kg": "N2O (kg)",
            "biogenic_co2_kg": "CO2 biogénico (kg)",
            "co2e_kg": "Total (kg CO2e)",
        }
    ).astype(float)
    df["Total (t CO2e)"] = df["Total (kg CO2e)"] / 1000
    reference = df["Total (kg CO2e)"].iloc[0]
    df[f"Diferencia vs {df.index[0]} (%)"] = (df["Total (kg CO2e)"] / reference - 1) * 100
    return df
