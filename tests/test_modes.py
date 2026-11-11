"""Electricity, waste and own-factor (Tier 2) calculations."""

import math

import pytest

from ghg_toolkit import (
    breakdown_from_distance,
    breakdown_from_electricity,
    breakdown_from_quantity,
    fod_series,
    half_life_years,
    total_of,
)


def test_electric_bus_exercise():
    # 60,000 km x 1.2 kWh/km = 72,000 kWh; x 0.25 kg CO2/kWh = 18,000 kg
    assert total_of(breakdown_from_electricity(72000, "kWh", 0.25)) == pytest.approx(18000)


def test_electricity_units():
    assert total_of(breakdown_from_electricity(2, "GWh", 0.3), "t CO2e") == pytest.approx(600)


def test_own_factor_replaces_default():
    own = breakdown_from_distance(15000, 10, "1A3b_gasolina_moderno", overrides={"pci": 44.3})
    ipcc = breakdown_from_distance(15000, 10, "1A3b_gasolina_moderno", pci_source="ipcc")
    assert total_of(own) == pytest.approx(total_of(ipcc))
    assert "dato propio (Nivel 2)" in set(own["Cálculo / fuente"])


def test_own_emission_factor():
    table = breakdown_from_quantity(1, "TJ", "1A1_diesel", overrides={"ef_co2": 70000, "ef_ch4": 0, "ef_n2o": 0})
    assert total_of(table) == pytest.approx(70000)


def test_fod_first_years_by_hand():
    # 1000 t/year of food waste, DOC 0.15, DOCf 0.5, MCF 1, k 0.19
    s = fod_series({2020: 1000, 2021: 1000, 2022: 1000}, doc=0.15, k=0.19, mcf=1.0)
    deposited = 1000 * 0.15 * 0.5 * 1.0
    decay = math.exp(-0.19)
    assert s.loc[2020, "CH4 emitido (t)"] == 0  # nothing decomposes in the first year
    assert s.loc[2021, "CH4 emitido (t)"] == pytest.approx(deposited * (1 - decay) * 0.5 * 16 / 12)
    stock_2021 = deposited + deposited * decay
    assert s.loc[2022, "DDOCm descompuesto (t C)"] == pytest.approx(stock_2021 * (1 - decay))
    assert s.loc[2022, "Emisiones (t CO2e)"] == pytest.approx(s.loc[2022, "CH4 emitido (t)"] * 28)


def test_fod_capture_and_oxidation():
    base = fod_series({1: 1000, 2: 1000}, doc=0.4, k=0.06, mcf=1.0)
    mitigated = fod_series({1: 1000, 2: 1000}, doc=0.4, k=0.06, mcf=1.0, recovered_fraction=0.5, ox=0.1)
    assert mitigated.loc[2, "CH4 emitido (t)"] == pytest.approx(base.loc[2, "CH4 emitido (t)"] * 0.5 * 0.9)


def test_half_life():
    assert half_life_years(0.19) == pytest.approx(3.648, abs=0.001)


def test_electric_haul_truck_matches_class_exercise():
    from ghg_toolkit import break_even_grid_factor, breakdown_electric_replacement

    # 54.18 TJ of diesel at 35% -> 18.963 TJ useful; at 85% -> 6197.06 MWh; x 0.25 -> 1549.26 t
    table = breakdown_electric_replacement(54.18, 0.35, 0.85, 0.25)
    values = dict(zip(zip(table["Paso"], table["Unidad"]), table["Valor"]))
    assert values[("Energía útil", "TJ")] == pytest.approx(18.963)
    assert values[("Pérdidas de calor", "TJ")] == pytest.approx(35.217)
    assert values[("Electricidad necesaria", "MWh")] == pytest.approx(6197.06, abs=0.01)
    assert total_of(table, "t CO2e") == pytest.approx(1549.26, abs=0.01)
    assert break_even_grid_factor(4014738, 6197058.8) == pytest.approx(0.6478, abs=0.0001)


def test_bus_fleet_matches_class_exercise():
    from ghg_toolkit import breakdown_electric_vehicle, breakdown_from_distance

    # 3000 buses x 60,000 km; diesel 45 L/100 km (IPCC calorific value); electric 1.2 kWh/km at 0.25 kg/kWh
    diesel = breakdown_from_distance(60000, 45, "1A3b_diesel_bus", pci_source="ipcc", units=3000)
    co2 = float(diesel[diesel["Unidad"] == "kg CO2"]["Valor"].iloc[0])
    assert co2 / 1000 == pytest.approx(216795.852)
    one = breakdown_from_distance(60000, 45, "1A3b_diesel_bus", pci_source="ipcc")
    assert total_of(diesel) == pytest.approx(total_of(one) * 3000)
    electric = breakdown_electric_vehicle(60000, 1.2, 0.25, units=3000)
    assert total_of(electric, "t CO2e") == pytest.approx(54000)


def test_units_multiply_fuel_and_electricity():
    assert total_of(breakdown_from_quantity(100, "L", "1A2_diesel", units=5)) == pytest.approx(
        total_of(breakdown_from_quantity(500, "L", "1A2_diesel"))
    )
    assert total_of(breakdown_from_electricity(10, "MWh", 0.3, units=4)) == pytest.approx(12000)
