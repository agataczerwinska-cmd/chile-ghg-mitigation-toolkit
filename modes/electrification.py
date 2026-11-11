"""Compare a fuel-burning machine or vehicle with an electric one doing the same job."""

import pandas as pd
import streamlit as st

from ghg_toolkit import (
    break_even_grid_factor,
    breakdown_electric_replacement,
    breakdown_electric_vehicle,
    breakdown_from_distance,
    breakdown_from_quantity,
    load_emission_factors,
    load_fuel_properties,
    total_of,
    units_for,
)

from .combustion import SECTORS, UNIT_NAMES
from .common import ef_note, gas_table, grid_selector, header, num_input, number, pci_note, precise, show_steps
from .i18n import T, lang

BY_ENERGY = "Mismo trabajo útil (eficiencias)"
BY_DISTANCE = "Misma distancia (consumo por km)"


def render() -> None:
    factors = load_emission_factors()
    fuels = load_fuel_properties()
    header("Electrificar un equipo", "Compara un equipo o vehículo a combustible con uno eléctrico que hace el mismo trabajo.")
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
        st.caption(ef_note(factor_id))
        units = units_for(factor_id)
        modes = [BY_ENERGY, BY_DISTANCE] if "L" in units else [BY_ENERGY]
        mode = st.radio(T("Comparar por"), modes, format_func=T, index=len(modes) - 1 if sector == "1A3b" else 0, key=f"el_mode_{sector}")
        pci_source = st.radio(
            T("Poder calorífico"),
            ["bne", "ipcc"],
            format_func=lambda v: T({"bne": "Chile (BNE)", "ipcc": "IPCC por defecto"}[v]),
            horizontal=True,
            key="el_pci",
        )
        if mode == BY_DISTANCE:
            km = num_input(T("Distancia al año por vehículo (km)"), value=60000.0, key="el_km")
            economy_unit = st.radio(T("Rendimiento en"), ["km/L", "L/100 km"], horizontal=True, index=1, key="el_economy_unit")
            economy = num_input(f"{T('Rendimiento')} ({economy_unit})", 0.01, None, 45.0 if economy_unit == "L/100 km" else 2.2, key=f"el_economy_{economy_unit}")
            litres_per_100km = 100 / economy if economy_unit == "km/L" else economy
        else:
            unit = st.selectbox(T("Unidad"), units, format_func=lambda u: T(UNIT_NAMES[u]), key=f"el_unit_{factor_id}_{lang()}")
            quantity = num_input(f"{T('Combustible al año por equipo')} ({unit})", value=1500000.0, key="el_quantity")
            fuel_eff = num_input(T("Eficiencia del equipo a combustible (%)"), 1.0, 100.0, 35.0, key="el_eff_fuel", help=T("Parte de la energía del combustible que se convierte en trabajo o calor útil."))
        st.caption(pci_note(factor_id, "L" if mode == BY_DISTANCE else unit, pci_source))
        n_units = num_input(T("Número de equipos o vehículos iguales"), 1.0, None, 1.0, key="el_units", help=T("La cantidad de arriba es por unidad; el resultado se multiplica por este número."))

        st.subheader(T("2. Equipo eléctrico"))
        if mode == BY_DISTANCE:
            kwh_per_km = num_input(T("Consumo eléctrico (kWh/km)"), 0.001, None, 1.2, key="el_kwh_km")
        else:
            electric_eff = num_input(T("Eficiencia del equipo eléctrico (%)"), 1.0, 1000.0, 85.0, key="el_eff_electric", help=T("Motor eléctrico: 85 a 95%. Bomba de calor: usa su COP en porcentaje (COP 3 = 300%)."))
        grid_factor, source = grid_selector("electrify")

    if mode == BY_DISTANCE:
        fuel_table = breakdown_from_distance(km, litres_per_100km, factor_id, pci_source, units=n_units)
        electric_table = breakdown_electric_vehicle(km, kwh_per_km, grid_factor, source, n_units)
    else:
        fuel_table = breakdown_from_quantity(quantity, unit, factor_id, pci_source, units=n_units)
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
        st.caption(T("En el inventario nacional el equipo eléctrico se informa en generación eléctrica (1A1); en la huella de la empresa pasa de Alcance 1 a Alcance 2."))
        st.bar_chart(pd.DataFrame({"t CO2e": {T("Equipo a combustible"): fuel_t, T("Equipo eléctrico"): electric_t}}), y_label="t CO2e", horizontal=True)

        st.subheader(T("Equipo a combustible: emisiones por gas"))
        gas_table(fuel_table, bool(options.loc[factor_id, "biogenic_co2"]))
        st.caption(T("El equipo eléctrico no se separa por gas: el factor de la red ya viene expresado en CO2e."))

        st.markdown(f"**{T('Equipo eléctrico')}**")
        show_steps(electric_table)
        st.markdown(f"**{T('Equipo a combustible')}**")
        show_steps(fuel_table)

        if st.button(T("Guardar ambos para comparar"), type="primary"):
            label = T(options.loc[factor_id, "example"]) + (f" × {n_units:g}" if n_units != 1 else "")
            st.session_state["scenarios"][f"{label} ({T('combustible')})"] = total_of(fuel_table)
            st.session_state["scenarios"][f"{label} ({T('eléctrico')})"] = total_of(electric_table)
            st.toast(T("Guardado"))
