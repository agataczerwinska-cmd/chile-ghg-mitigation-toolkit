"""Purchased electricity: consumption x grid emission factor."""

import pandas as pd

KWH_PER = {"kWh": 1, "MWh": 1_000, "GWh": 1_000_000}


def breakdown_from_electricity(
    quantity: float, unit: str, grid_factor_kg_per_kwh: float, factor_source: str = "dato"
) -> pd.DataFrame:
    """Table with every step from electricity used (kWh, MWh or GWh) to kg CO2e."""
    if unit not in KWH_PER:
        raise ValueError(f"unit must be one of {list(KWH_PER)}")
    kwh = quantity * KWH_PER[unit]
    co2e = kwh * grid_factor_kg_per_kwh
    rows = [("Electricidad consumida", quantity, unit, "dato")]
    if unit != "kWh":
        rows.append(("Electricidad consumida", kwh, "kWh", f"{unit} × {KWH_PER[unit]:,}".replace(",", ".")))
    rows += [
        ("Factor de emisión de la red", grid_factor_kg_per_kwh, "kg CO2e/kWh", factor_source),
        ("TOTAL", co2e, "kg CO2e", "kWh × factor de la red"),
        ("TOTAL", co2e / 1000, "t CO2e", "kg CO2e ÷ 1000"),
    ]
    df = pd.DataFrame(rows, columns=["Paso", "Valor", "Unidad", "Cálculo / fuente"])
    df["Valor"] = df["Valor"].astype(float)
    df.index = range(1, len(df) + 1)
    return df
