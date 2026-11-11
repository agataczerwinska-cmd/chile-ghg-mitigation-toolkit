"""English mode must not leave Spanish text in step tables or data labels."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ghg_toolkit import (  # noqa: E402
    breakdown_electric_replacement,
    breakdown_electric_vehicle,
    breakdown_from_distance,
    breakdown_from_electricity,
    breakdown_from_forest_growth,
    breakdown_from_quantity,
    breakdown_from_wood_volume,
    fod_series,
    load_emission_factors,
    load_forest_factors,
    load_fuel_properties,
    load_grid_factors,
    load_waste_parameters,
)
from modes import PLANNED, SECTIONS, i18n  # noqa: E402

SPANISH = re.compile(r"[áéíóúñ¿«]|\b(de|del|la|el|por|en|dato|tabla|año)\b", re.IGNORECASE)
ALLOWED = ("Gayoso et al", "INGEI Chile", "SEN ", "Vol.")


@pytest.fixture(autouse=True)
def english(monkeypatch):
    monkeypatch.setattr(i18n, "lang", lambda: "en")
    i18n.MISSING.clear()


def leftovers(table):
    cells = list(table.columns) + [c for col in table.columns for c in table[col]]
    return [c for c in cells if isinstance(c, str) and SPANISH.search(c) and not any(a in c for a in ALLOWED)]


def test_step_tables_are_fully_translated():
    tables = [
        breakdown_from_distance(15000, 10, "1A3b_gasolina_moderno"),
        breakdown_from_quantity(1000, "L", "1A3b_diesel_bus", overrides={"density": 0.85, "pci": 43, "ef_co2": 1}),
        breakdown_from_quantity(1000, "m3", "1A1_gas_natural", pci_source="ipcc"),
        breakdown_from_quantity(1000, "t", "1A4b_lena"),
        breakdown_from_quantity(5, "TJ", "1A2_licor_negro"),
        breakdown_from_electricity(2, "GWh", 0.3, "dato propio"),
        breakdown_electric_replacement(54.18, 0.35, 0.85, 0.25, "SEN (Chile)"),
        breakdown_electric_vehicle(60000, 1.2, 0.25, "dato propio", 3000),
        breakdown_from_distance(60000, 45, "1A3b_diesel_bus", units=3000),
        breakdown_from_quantity(100, "L", "1A2_diesel", units=5),
        breakdown_from_electricity(10, "MWh", 0.3, "SEN (Chile)", 4),
        breakdown_from_wood_volume(1000, "Especies nativas", overrides={"feb": 2}),
        breakdown_from_forest_growth(100, 6, "Pino insigne (Pinus radiata)"),
        __import__("ghg_toolkit").breakdown_from_biomass_growth(100, 12, "Pino insigne (Pinus radiata)", growth_source="INGEI 2024 (incremento medio anual)"),
        fod_series({2020: 1000, 2021: 1000}, doc=0.15, k=0.19, mcf=1.0).reset_index(),
    ]
    for table in tables:
        translated = i18n.T_table(table)
        assert leftovers(translated) == []
    # the check itself must be able to see Spanish text
    assert leftovers(tables[0]) != []


def test_every_data_label_has_a_translation():
    params = load_waste_parameters()
    labels = (
        list(load_emission_factors()["example"])
        + list(load_fuel_properties()["name"])
        + list(load_forest_factors().index)
        + [n for n in load_forest_factors()["note"] if isinstance(n, str)]
        + list(load_grid_factors().index)
        + list(params[params["parameter"].isin(["DOC", "MCF"])]["item"])
        + ["Central a carbón", "Ciclo combinado", "Parque solar", "Parque eólico"]
        + list(__import__("ghg_toolkit").CATEGORIES)
        + list(__import__("ghg_toolkit").load_forest_growth()["type"].unique())
        + PLANNED
        + list(SECTIONS)
        + [title for entries in SECTIONS.values() for title, *_ in entries]
    )
    for label in labels:
        i18n.T(label)
    assert i18n.MISSING == set()
