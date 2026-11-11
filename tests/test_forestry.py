"""Forest land: wood volume to CO2 with Chilean national factors."""

import pytest

from ghg_toolkit import breakdown_from_forest_growth, breakdown_from_wood_volume, total_of


def test_pine_harvest_by_hand():
    # 1000 m3 x 0.39 t/m3 x 1.56 x (1 + 0.25) x 0.5 x 3.667
    expected = 1000 * 0.39 * 1.56 * 1.25 * 0.5 * 3.667
    table = breakdown_from_wood_volume(1000, "Pino insigne (Pinus radiata)")
    assert total_of(table, "t CO2e") == pytest.approx(expected)


def test_growth_is_a_negative_emission():
    table = breakdown_from_forest_growth(100, 6, "Especies nativas")
    expected = 100 * 6 * 0.50 * 1.75 * 1.29 * 0.5 * 3.667
    assert total_of(table, "t CO2e") == pytest.approx(-expected)


def test_own_density():
    a = breakdown_from_wood_volume(10, "Otras especies", overrides={"density": 0.92})
    b = breakdown_from_wood_volume(10, "Otras especies")
    assert total_of(a) == pytest.approx(total_of(b) * 2)


def test_biomass_growth_from_ingei_table():
    from ghg_toolkit import breakdown_from_biomass_growth, load_forest_growth

    growth = load_forest_growth()
    pine = growth[(growth["type"] == "Pino radiata") & (growth["region"] == "Biobío")]["growth_t_ha_year"].iloc[0]
    assert pine == 12.0
    # 1000 ha x 12 t/ha/yr x (1 + 0.25) x 0.5 x 3.667
    table = breakdown_from_biomass_growth(1000, pine, "Pino insigne (Pinus radiata)")
    assert total_of(table, "t CO2e") == pytest.approx(-1000 * 12 * 1.25 * 0.5 * 3.667)


def test_growth_table_species_exist_in_factors():
    from ghg_toolkit import load_forest_factors, load_forest_growth

    assert set(load_forest_growth()["factor_species"]) <= set(load_forest_factors().index)
