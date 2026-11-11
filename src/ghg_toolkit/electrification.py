"""Replacing a fuel-burning machine with an electric one that does the same work.

    useful energy      = fuel energy x efficiency of the fuel machine
    electricity needed = useful energy / efficiency of the electric machine
    emissions          = electricity needed x grid emission factor

An electric efficiency above 100% represents a heat pump (COP 3 = 300%).
"""

import pandas as pd

MJ_PER_TJ = 1_000_000
MJ_PER_KWH = 3.6


def breakdown_electric_replacement(
    fuel_energy_tj: float,
    fuel_efficiency: float,
    electric_efficiency: float,
    grid_factor_kg_per_kwh: float,
    factor_source: str = "dato",
) -> pd.DataFrame:
    """Table with every step from the fuel's energy to the electric machine's emissions.

    Efficiencies are fractions (0.35 = 35%).
    """
    if not 0 < fuel_efficiency <= 1:
        raise ValueError("fuel_efficiency must be between 0 and 1")
    if electric_efficiency <= 0:
        raise ValueError("electric_efficiency must be positive")
    useful = fuel_energy_tj * fuel_efficiency
    losses = fuel_energy_tj - useful
    electric_tj = useful / electric_efficiency
    kwh = electric_tj * MJ_PER_TJ / MJ_PER_KWH
    co2e = kwh * grid_factor_kg_per_kwh
    rows = [
        ("Energía del combustible", fuel_energy_tj, "TJ", "cálculo del combustible"),
        ("Eficiencia del equipo a combustible", fuel_efficiency * 100, "%", "dato"),
        ("Energía útil", useful, "TJ", "energía del combustible × eficiencia"),
        ("Pérdidas de calor", losses, "TJ", "energía del combustible − energía útil"),
        ("Eficiencia del equipo eléctrico", electric_efficiency * 100, "%", "dato"),
        ("Electricidad necesaria", electric_tj, "TJ", "energía útil ÷ eficiencia eléctrica"),
        ("Electricidad necesaria", kwh / 1000, "MWh", "TJ ÷ 0,0036"),
        ("Electricidad necesaria", kwh, "kWh", "MWh × 1000"),
        ("Factor de emisión de la red", grid_factor_kg_per_kwh, "kg CO2e/kWh", factor_source),
        ("TOTAL", co2e, "kg CO2e", "kWh × factor de la red"),
        ("TOTAL", co2e / 1000, "t CO2e", "kg CO2e ÷ 1000"),
    ]
    df = pd.DataFrame(rows, columns=["Paso", "Valor", "Unidad", "Cálculo / fuente"])
    df["Valor"] = df["Valor"].astype(float)
    df.index = range(1, len(df) + 1)
    return df


def breakdown_electric_vehicle(
    km: float,
    kwh_per_km: float,
    grid_factor_kg_per_kwh: float,
    factor_source: str = "dato",
    units: float = 1,
) -> pd.DataFrame:
    """Table with every step from kilometres driven by an electric vehicle to kg CO2e.

    `units` is the number of identical vehicles; `km` is per vehicle.
    """
    rows = []
    if units != 1:
        rows = [
            ("Distancia por unidad", km, "km", "dato"),
            ("Número de unidades", units, "–", "dato"),
        ]
        km = km * units
    kwh = km * kwh_per_km
    co2e = kwh * grid_factor_kg_per_kwh
    rows += [
        ("Distancia recorrida", km, "km", "por unidad × número de unidades" if units != 1 else "dato"),
        ("Consumo eléctrico", kwh_per_km, "kWh/km", "dato"),
        ("Electricidad necesaria", kwh, "kWh", "km × kWh/km"),
        ("Electricidad necesaria", kwh / 1000, "MWh", "kWh ÷ 1000"),
        ("Factor de emisión de la red", grid_factor_kg_per_kwh, "kg CO2e/kWh", factor_source),
        ("TOTAL", co2e, "kg CO2e", "kWh × factor de la red"),
        ("TOTAL", co2e / 1000, "t CO2e", "kg CO2e ÷ 1000"),
    ]
    df = pd.DataFrame(rows, columns=["Paso", "Valor", "Unidad", "Cálculo / fuente"])
    df["Valor"] = df["Valor"].astype(float)
    df.index = range(1, len(df) + 1)
    return df


def break_even_grid_factor(fuel_total_kg_co2e: float, electricity_kwh: float) -> float:
    """Grid factor (kg CO2e/kWh) at which the electric machine emits as much as the fuel one."""
    return fuel_total_kg_co2e / electricity_kwh
