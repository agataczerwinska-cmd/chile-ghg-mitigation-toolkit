"""Organisational carbon footprint (GHG Protocol / NCh-ISO 14064-1 / HuellaChile).

Every source follows the same rule: activity data x emission factor = CO2e.
Sources are grouped into the categories of the HuellaChile report (Tabla 5)
and each category belongs to one scope:

    Scope 1  direct emissions (owned or controlled sources)
    Scope 2  indirect emissions from imported energy
    Scope 3  other indirect emissions in the value chain

Biogenic CO2 is reported separately as an informative item, not in the total.
"""

from typing import List

import pandas as pd

from .breakdown import breakdown_from_quantity, total_of
from .factors import load_gwp

KWH_PER = {"kWh": 1, "MWh": 1_000, "GWh": 1_000_000}

# HuellaChile Tabla 5 categories, in report order, with their scope
CATEGORIES = {
    "Combustión estacionaria": 1,
    "Combustión móvil": 1,
    "Uso de suelo, cambio de uso de suelo y silvicultura": 1,
    "Procesos industriales": 1,
    "Emisiones fugitivas": 1,
    "Electricidad importada": 2,
    "Otra energía importada y/o pérdidas T&D": 2,
    "Transporte": 3,
    "Productos que utiliza la organización": 3,
    "Uso de productos de la organización": 3,
}


def source_emissions(source: dict, grid_factor: float, pci_source: str = "bne") -> dict:
    """kg CO2e (and biogenic kg CO2) of one source.

    source["kind"] is one of:
      "fuel"         factor_id, quantity, unit (L, kg, t, m3, MJ, TJ)
      "electricity"  quantity, unit (kWh, MWh, GWh); uses grid_factor (kg CO2e/kWh)
      "refrigerant"  gas (a row of gwp_ar5.csv), quantity in kg released
      "own"          quantity and own_factor (kg CO2e per unit of quantity)
    """
    kind = source["kind"]
    quantity = float(source["quantity"])
    biogenic = 0.0
    if kind == "fuel":
        table = breakdown_from_quantity(quantity, source["unit"], source["factor_id"], pci_source)
        kg = total_of(table)
        step = table[table["Paso"].str.startswith("Emisiones CO2 (biogénico")]
        biogenic = float(step["Valor"].iloc[0]) if len(step) else 0.0
    elif kind == "electricity":
        kg = quantity * KWH_PER[source["unit"]] * grid_factor
    elif kind == "refrigerant":
        kg = quantity * float(load_gwp().loc[source["gas"], "gwp"])
    elif kind == "own":
        kg = quantity * float(source["own_factor"])
    else:
        raise ValueError(f"Unknown kind '{kind}'")
    return {"kg_co2e": kg, "biogenic_kg_co2": biogenic}


def footprint(sources: List[dict], grid_factor: float, pci_source: str = "bne") -> dict:
    """Per-source results, the category summary (Tabla 5) and scope totals, in t CO2e."""
    rows = []
    for s in sources:
        if s["category"] not in CATEGORIES:
            raise ValueError(f"Unknown category '{s['category']}'")
        result = source_emissions(s, grid_factor, pci_source)
        rows.append(
            {
                "name": s["name"],
                "category": s["category"],
                "scope": CATEGORIES[s["category"]],
                "t_co2e": result["kg_co2e"] / 1000,
                "biogenic_t_co2": result["biogenic_kg_co2"] / 1000,
            }
        )
    by_source = pd.DataFrame(rows, columns=["name", "category", "scope", "t_co2e", "biogenic_t_co2"])
    total = by_source["t_co2e"].sum()
    summary = pd.DataFrame({"category": list(CATEGORIES), "scope": list(CATEGORIES.values())})
    summary["t_co2e"] = summary["category"].map(by_source.groupby("category")["t_co2e"].sum()).fillna(0.0)
    summary["included"] = summary["category"].isin(set(by_source["category"]))
    summary["share"] = summary["t_co2e"] / total if total else 0.0
    scopes = {n: float(by_source.loc[by_source["scope"] == n, "t_co2e"].sum()) for n in (1, 2, 3)}
    return {
        "by_source": by_source,
        "summary": summary,
        "scopes": scopes,
        "total_t": float(total),
        "biogenic_t": float(by_source["biogenic_t_co2"].sum()),
    }
