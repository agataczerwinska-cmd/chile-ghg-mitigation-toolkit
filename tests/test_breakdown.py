"""The step-by-step tables must reproduce the class exercises solved in Excel."""

import pytest

from ghg_toolkit import (
    breakdown_from_distance,
    breakdown_from_quantity,
    emissions_from_distance,
    total_of,
    units_for,
)


def test_breakdown_total_matches_calculator():
    table = breakdown_from_distance(15000, 10, "1A3b_gasolina_moderno", pci_source="ipcc")
    e = emissions_from_distance(15000, 10, "1A3b_gasolina_moderno", pci_source="ipcc")
    assert total_of(table) == pytest.approx(e.co2e_kg)


def test_gasoline_car_steps():
    table = breakdown_from_distance(15000, 10, "1A3b_gasolina_moderno", pci_source="ipcc")
    values = dict(zip(table["Unidad"], table["Valor"]))
    assert values["kg"] == pytest.approx(1095)
    assert values["MJ"] == pytest.approx(48508.5)
    assert values["kg CO2"] == pytest.approx(3361.64, abs=0.01)


def test_household_lpg():
    # 435 kg of LPG in a home -> 1254.68 kg CO2e
    assert total_of(breakdown_from_quantity(435, "kg", "1A4b_glp")) == pytest.approx(1254.68, abs=0.01)


def test_coal_power_plant():
    # 600,000 t of bituminous coal -> 1,587,305.952 t CO2e
    table = breakdown_from_quantity(600000, "t", "1A1_carbon_bituminoso")
    assert total_of(table, "t CO2e") == pytest.approx(1587305.952)


def test_gas_combined_cycle():
    # 400 million m3 of natural gas -> 790,655.36 t CO2e
    table = breakdown_from_quantity(400e6, "m3", "1A1_gas_natural")
    assert total_of(table, "t CO2e") == pytest.approx(790655.36)


def test_biogenic_co2_is_left_out_of_total():
    table = breakdown_from_quantity(1, "TJ", "1A4b_lena")
    assert total_of(table) == pytest.approx(300 * 28 + 4 * 265)


def test_units_offered():
    assert units_for("1A3b_diesel_bus") == ["L", "kg", "t", "MJ", "TJ"]
    assert units_for("1A1_gas_natural") == ["m3", "MJ", "TJ"]
    with pytest.raises(ValueError):
        breakdown_from_quantity(1, "L", "1A1_gas_natural")
