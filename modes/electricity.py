"""Purchased electricity: consumption x grid emission factor."""

import streamlit as st

from ghg_toolkit import breakdown_from_electricity, total_of

from .common import grid_selector, header, num_input, number, save_and_download, show_steps
from .i18n import T



def render() -> None:
    header("Electricidad", "Emisiones de la electricidad comprada a la red: consumo × factor de emisión.")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(T("1. ¿Cuánta electricidad?"))
        unit = st.selectbox(T("Unidad"), ["kWh", "MWh", "GWh"])
        quantity = num_input(f"{T('Consumo')} ({unit})", min_value=0.0, value=1000.0, step=100.0)

        n_units = num_input(T("Número de equipos o vehículos iguales"), 1.0, None, 1.0, key="elec_units", help=T("La cantidad de arriba es por unidad; el resultado se multiplica por este número."))

        st.subheader(T("2. Factor de emisión de la red"))
        factor, source = grid_selector("electricity")

    table = breakdown_from_electricity(quantity, unit, factor, source, n_units)

    with right:
        st.subheader(T("Resultado"))
        a, b = st.columns(2)
        a.metric(T("Total"), f"{number(total_of(table))} kg CO2e")
        b.metric(T("Total"), f"{number(total_of(table, 't CO2e'))} t CO2e")
        st.caption(T("En el inventario nacional estas emisiones se informan en generación eléctrica (1A1). En una huella corporativa son Alcance 2."))
        show_steps(table)
        save_and_download(table, f"{T('Electricidad')}, {number(quantity)} {unit}" + (f" × {n_units:g}" if n_units != 1 else ""), total_of(table), "electricity")
