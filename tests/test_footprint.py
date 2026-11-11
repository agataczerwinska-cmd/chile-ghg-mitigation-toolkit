"""Organisational footprint: scopes, categories and totals."""

import pytest

from ghg_toolkit import breakdown_from_quantity, footprint, total_of

SOURCES = [
    {"name": "vans", "category": "Combustión móvil", "kind": "fuel", "factor_id": "1A3b_diesel_liviano", "quantity": 8000, "unit": "L"},
    {"name": "ac", "category": "Emisiones fugitivas", "kind": "refrigerant", "gas": "HFC-134a", "quantity": 3},
    {"name": "power", "category": "Electricidad importada", "kind": "electricity", "quantity": 120, "unit": "MWh"},
    {"name": "flights", "category": "Transporte", "kind": "own", "quantity": 10000, "own_factor": 0.15},
    {"name": "boiler", "category": "Combustión estacionaria", "kind": "fuel", "factor_id": "1A2_madera", "quantity": 10, "unit": "t"},
]


def test_scopes_and_total():
    result = footprint(SOURCES, grid_factor=0.3)
    vans = total_of(breakdown_from_quantity(8000, "L", "1A3b_diesel_liviano")) / 1000
    boiler = total_of(breakdown_from_quantity(10, "t", "1A2_madera")) / 1000
    assert result["scopes"][1] == pytest.approx(vans + 3 * 1300 / 1000 + boiler)
    assert result["scopes"][2] == pytest.approx(120_000 * 0.3 / 1000)
    assert result["scopes"][3] == pytest.approx(1.5)
    assert result["total_t"] == pytest.approx(sum(result["scopes"].values()))


def test_biogenic_is_informative():
    result = footprint(SOURCES, grid_factor=0.3)
    # 10 t wood x 13.92 MJ/kg (BNE) = 139.2 GJ = 0.1392 TJ x 112,000 kg CO2/TJ
    assert result["biogenic_t"] == pytest.approx(0.1392 * 112)
    assert result["summary"]["share"].sum() == pytest.approx(1)


def test_summary_marks_included_categories():
    summary = footprint(SOURCES, grid_factor=0.3)["summary"].set_index("category")
    assert summary.loc["Transporte", "included"]
    assert not summary.loc["Procesos industriales", "included"]
    assert summary.loc["Procesos industriales", "t_co2e"] == 0
