"""Each test repeats the calculation by hand, the same way you would in Excel."""

import pytest

from ghg_toolkit import emissions_from_distance, emissions_from_fuel_volume


def test_gasoline_1000_litres():
    # 1000 L x 0.73 kg/L = 730 kg; x 44.55 MJ/kg (BNE) = 32521.5 MJ = 0.0325215 TJ
    energy_tj = 1000 * 0.73 * 44.55 / 1_000_000
    e = emissions_from_fuel_volume(1000, "1A3b_gasolina_moderno")
    assert e.co2_kg == pytest.approx(energy_tj * 69300)
    assert e.ch4_kg == pytest.approx(energy_tj * 3.8)
    assert e.n2o_kg == pytest.approx(energy_tj * 5.7)
    assert e.co2e_kg == pytest.approx(
        energy_tj * 69300 + energy_tj * 3.8 * 28 + energy_tj * 5.7 * 265
    )


def test_distance_matches_fuel_volume():
    by_km = emissions_from_distance(10_000, 30, "1A3b_diesel_bus")
    by_litres = emissions_from_fuel_volume(3_000, "1A3b_diesel_bus")
    assert by_km.co2e_kg == pytest.approx(by_litres.co2e_kg)


def test_custom_density_is_used():
    default = emissions_from_fuel_volume(1000, "1A3b_diesel_camion")
    custom = emissions_from_fuel_volume(1000, "1A3b_diesel_camion", density_kg_per_l=0.42)
    assert custom.co2_kg == pytest.approx(default.co2_kg / 2)


def test_unknown_factor_id():
    with pytest.raises(KeyError):
        emissions_from_fuel_volume(1000, "no_existe")


def test_ipcc_calorific_value_matches_class_exercise():
    # Class exercise: 1500 L gasoline, IPCC PCI 44.3 MJ/kg -> 3361.64 kg CO2
    e = emissions_from_fuel_volume(1500, "1A3b_gasolina_moderno", pci_source="ipcc")
    assert e.co2_kg == pytest.approx(3361.64, abs=0.01)


def test_every_factor_fuel_has_properties():
    from ghg_toolkit import load_emission_factors, load_fuel_properties

    missing = set(load_emission_factors()["fuel"]) - set(load_fuel_properties().index)
    assert not missing
