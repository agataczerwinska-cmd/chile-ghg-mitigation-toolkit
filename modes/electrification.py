"""Compare a fuel-burning machine with an electric one doing the same work."""

import pandas as pd
import streamlit as st

from ghg_toolkit import (
    break_even_grid_factor,
    breakdown_electric_replacement,
    breakdown_from_quantity,
    load_emission_factors,
    load_fuel_properties,
    load_grid_factors,
    total_of,
    units_for,
)

from .combustion import SECTORS, UNIT_NAMES
from .common import header, num_input, number, precise, show_steps
from .i18n import T, lang

OWN = "Otro (escribir el factor)"


def render() -> None:
    factors = load_emission_factors()
    fuels = load_fuel_properties()
    grids = load_grid_factors()
    header("Electrificar un equipo", "Compara un equipo a combustible con uno eléctrico que hace el mismo trabajo útil.")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(T("1. Equipo a combustible"))
        sectors = [s for s in SECTORS if s in set(factors["ipcc_category"])]
        sector = st.selectbox(T("Sector"), sectors, format_func=lambda c: f"{T(SECTORS[c])} ({c})", index=sectors.index("1A2"), key="el_sector")
        options = factors[factors["ipcc_category"] == sector]
        default = list(options.index).index("1A2_diesel_fuera_de_ruta") if sector == "1A2" else 0
        factor_id = st.selectbox(
            T("Equipo o vehículo"),
            list(options.index),
            index=default,
            format_func=lambda i: f"{T(options.loc[i, 'example'])} · {T(fuels.loc[options.loc[i, 'fuel'], 'name'])}",
            key=f"el_equipment_{sector}_{lang()}",
        )
        unit = st.selectbox(T("Unidad"), units_for(factor_id), format_func=lambda u: T(UNIT_NAMES[u]), key=f"el_unit_{factor_id}_{lang()}")
        quantity = num_input(f"{T('Combustible al año')} ({unit})", value=1500000.0, key="el_quantity")
        pci_source = st.radio(
            T("Poder calorífico"),
            ["bne", "ipcc"],
            format_func=lambda v: T({"bne": "Chile (BNE)", "ipcc": "IPCC por defecto"}[v]),
            horizontal=True,
            key="el_pci",
        )
        fuel_eff = num_input(T("Eficiencia del equipo a combustible (%)"), 1.0, 100.0, 35.0, key="el_eff_fuel", help=T("Parte de la energía del combustible que se convierte en trabajo o calor útil."))

        st.subheader(T("2. Equipo eléctrico"))
        electric_eff = num_input(T("Eficiencia del equipo eléctrico (%)"), 1.0, 1000.0, 85.0, key="el_eff_electric", help=T("Motor eléctrico: 85 a 95%. Bomba de calor: usa su COP en porcentaje (COP 3 = 300%)."))
        grid = st.selectbox(T("Red"), list(grids.index) + [OWN], format_func=T, key="el_grid")
        if grid == OWN:
            grid_factor = num_input(T("Factor (kg CO2e/kWh)"), value=0.25, key="el_grid_factor")
            source = "dato propio"
        else:
            grid_factor = float(grids.loc[grid, "ef"])
            source = grid
            st.caption(f"{precise(grid_factor)} kg CO2e/kWh")

    fuel_table = breakdown_from_quantity(quantity, unit, factor_id, pci_source)
    fuel_tj = float(fuel_table[fuel_table["Unidad"] == "TJ"]["Valor"].iloc[0])
    electric_table = breakdown_electric_replacement(fuel_tj, fuel_eff / 100, electric_eff / 100, grid_factor, source)
    fuel_t = total_of(fuel_table, "t CO2e")
    electric_t = total_of(electric_table, "t CO2e")
    kwh = float(electric_table[electric_table["Unidad"] == "kWh"]["Valor"].iloc[0])
    saved = fuel_t - electric_t

    with right:
        st.subheader(T("Resultado"))
        a, b, c = st.columns(3)
        a.metric(f"{T('Equipo a combustible')} (t CO2e)", number(fuel_t))
        b.metric(f"{T('Equipo eléctrico')} (t CO2e)", number(electric_t))
        c.metric(f"{T('Emisiones evitadas')} (t CO2e)", number(saved), delta=f"{number(-saved / fuel_t * 100) if fuel_t else '0'} %", delta_color="inverse")
        if kwh:
            st.caption(T("El equipo eléctrico deja de convenir si el factor de la red supera") + f" {precise(break_even_grid_factor(total_of(fuel_table), kwh))} kg CO2e/kWh.")
        st.caption(T("El total del combustible incluye CO2, CH4 y N2O. En el inventario nacional el equipo eléctrico se informa en generación eléctrica (1A1); en la huella de la empresa pasa de Alcance 1 a Alcance 2."))
        st.bar_chart(pd.DataFrame({"t CO2e": {T("Equipo a combustible"): fuel_t, T("Equipo eléctrico"): electric_t}}), y_label="t CO2e", horizontal=True)

        st.markdown(f"**{T('Equipo eléctrico')}**")
        show_steps(electric_table)
        st.markdown(f"**{T('Equipo a combustible')}**")
        show_steps(fuel_table)

        if st.button(T("Guardar ambos para comparar"), type="primary"):
            label = T(options.loc[factor_id, "example"])
            st.session_state["scenarios"][f"{label} ({T('combustible')})"] = total_of(fuel_table)
            st.session_state["scenarios"][f"{label} ({T('eléctrico')})"] = total_of(electric_table)
            st.toast(T("Guardado"))
