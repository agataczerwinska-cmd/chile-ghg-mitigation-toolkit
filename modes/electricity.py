"""Purchased electricity: consumption x grid emission factor."""

import streamlit as st

from ghg_toolkit import breakdown_from_electricity, load_grid_factors, total_of

from .common import header, num_input, number, save_and_download, show_steps
from .i18n import T

OWN = "Otro (escribir el factor)"


def render() -> None:
    grids = load_grid_factors()
    header("Electricidad", "Emisiones de la electricidad comprada a la red: consumo × factor de emisión.")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(T("1. ¿Cuánta electricidad?"))
        unit = st.selectbox(T("Unidad"), ["kWh", "MWh", "GWh"])
        quantity = num_input(f"{T('Consumo')} ({unit})", min_value=0.0, value=1000.0, step=100.0)

        st.subheader(T("2. Factor de emisión de la red"))
        grid = st.selectbox(T("Red"), list(grids.index) + [OWN], format_func=T)
        if grid == OWN:
            factor = num_input(T("Factor (kg CO2e/kWh)"), min_value=0.0, value=0.25, step=0.01, format="%.4f")
            source = "dato propio"
        else:
            factor = float(grids.loc[grid, "ef"])
            noted = grids.loc[grid, "source"]
            source = f"{grid}" + (f", {noted}" if isinstance(noted, str) and noted else "")
            st.caption(f"{number(factor)} kg CO2e/kWh")

    table = breakdown_from_electricity(quantity, unit, factor, source)

    with right:
        st.subheader(T("Resultado"))
        a, b = st.columns(2)
        a.metric(T("Total"), f"{number(total_of(table))} kg CO2e")
        b.metric(T("Total"), f"{number(total_of(table, 't CO2e'))} t CO2e")
        st.caption(T("En el inventario nacional estas emisiones se informan en generación eléctrica (1A1). En una huella corporativa son Alcance 2."))
        show_steps(table)
        save_and_download(table, f"{T('Electricidad')}, {number(quantity)} {unit}", total_of(table), "electricity")
