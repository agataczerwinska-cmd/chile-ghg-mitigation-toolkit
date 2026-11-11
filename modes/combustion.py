"""Fuel combustion in any energy sector (IPCC 1A): power, industry, transport, buildings."""

import streamlit as st

from ghg_toolkit import (
    breakdown_from_distance,
    breakdown_from_quantity,
    load_emission_factors,
    load_fuel_properties,
    total_of,
    units_for,
)

from .common import header, num_input, number, save_and_download, show_steps
from .i18n import T, lang

SECTORS = {
    "1A1": "Generación eléctrica y refinación",
    "1A2": "Industria y minería",
    "1A3a": "Aviación",
    "1A3b": "Transporte terrestre",
    "1A3c": "Ferrocarriles",
    "1A3d": "Navegación",
    "1A4a": "Comercial e institucional",
    "1A4b": "Residencial",
    "1A4c": "Agricultura y pesca",
}
UNIT_NAMES = {
    "L": "Litros (L)",
    "kg": "Kilogramos (kg)",
    "t": "Toneladas (t)",
    "m3": "Metros cúbicos (m3)",
    "MJ": "Megajoules (MJ)",
    "TJ": "Terajoules (TJ)",
}


def render() -> None:
    factors = load_emission_factors()
    fuels = load_fuel_properties()
    header("Combustibles", "Emisiones por quemar combustibles en centrales eléctricas, industria, minería, transporte, hogares y comercio.")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(T("1. ¿Dónde se usa el combustible?"))
        sectors = [s for s in SECTORS if s in set(factors["ipcc_category"])]
        sector = st.selectbox(T("Sector"), sectors, format_func=lambda c: f"{T(SECTORS[c])} ({c})", index=sectors.index("1A3b"))
        options = factors[factors["ipcc_category"] == sector]
        factor_id = st.selectbox(
            T("Equipo o vehículo"),
            list(options.index),
            format_func=lambda i: f"{T(options.loc[i, 'example'])} · {T(fuels.loc[options.loc[i, 'fuel'], 'name'])} ({T('Nivel')} {options.loc[i, 'tier']})",
            key=f"equipment_{sector}_{lang()}",
        )
        ef = options.loc[factor_id]
        props = fuels.loc[ef["fuel"]]

        st.subheader(T("2. ¿Cuánto?"))
        units = units_for(factor_id)
        by_distance = False
        if sector == "1A3b" and "L" in units:
            by_distance = st.radio(T("Dato disponible"), ["Distancia recorrida", "Combustible consumido"], format_func=T, horizontal=True) == "Distancia recorrida"
        if by_distance:
            unit = "L"
            km = num_input(T("Distancia (km)"), min_value=0.0, value=15000.0, step=1000.0)
            economy_unit = st.radio(T("Rendimiento en"), ["km/L", "L/100 km"], horizontal=True)
            economy = num_input(f"{T('Rendimiento')} ({economy_unit})", min_value=0.01, value=10.0, step=0.5)
            litres_per_100km = 100 / economy if economy_unit == "km/L" else economy
        else:
            unit = st.selectbox(T("Unidad"), units, format_func=lambda u: T(UNIT_NAMES[u]), key=f"unit_{factor_id}_{lang()}")
            quantity = num_input(f"{T('Cantidad')} ({unit})", min_value=0.0, value=1000.0, step=100.0, key="quantity")

        st.subheader(T("3. Factores"))
        pci_source = st.radio(
            T("Poder calorífico"),
            ["bne", "ipcc"],
            format_func=lambda v: T({"bne": "Chile (BNE)", "ipcc": "IPCC por defecto"}[v]),
            horizontal=True,
            help=T("El curso usa los valores chilenos del Balance Nacional de Energía."),
        )
        overrides = {}
        if st.toggle(T("Usar factores propios (Nivel 2 o dato específico)"), help=T("Reemplaza cualquier valor por defecto por el de tu fuente: INGEI, una empresa, el enunciado de un ejercicio.")):
            key = f"{factor_id}_{pci_source}"
            overrides["ef_co2"] = num_input("CO2 (kg/TJ)", min_value=0.0, value=float(ef["ef_co2_kg_tj"]), key=f"co2_{key}")
            overrides["ef_ch4"] = num_input("CH4 (kg/TJ)", min_value=0.0, value=float(ef["ef_ch4_kg_tj"]), key=f"ch4_{key}")
            overrides["ef_n2o"] = num_input("N2O (kg/TJ)", min_value=0.0, value=float(ef["ef_n2o_kg_tj"]), key=f"n2o_{key}")
            if unit not in ("MJ", "TJ"):
                wanted = "MJ/m3" if unit == "m3" else "MJ/kg"
                source = pci_source if props[f"pci_{pci_source}_unit"] == wanted else ("ipcc" if pci_source == "bne" else "bne")
                overrides["pci"] = num_input(f"{T('Poder calorífico inferior')} ({wanted})", min_value=0.0, value=float(props[f"pci_{source}"]), key=f"pci_{key}_{unit}")
            if unit == "L":
                overrides["density"] = num_input(T("Densidad (kg/L)"), min_value=0.0, value=float(props["density"]), key=f"dens_{key}")
            # keep only the values that really differ from the defaults
            defaults = {"ef_co2": ef["ef_co2_kg_tj"], "ef_ch4": ef["ef_ch4_kg_tj"], "ef_n2o": ef["ef_n2o_kg_tj"]}
            if "pci" in overrides:
                defaults["pci"] = props[f"pci_{source}"]
            if "density" in overrides:
                defaults["density"] = props["density"]
            overrides = {k: v for k, v in overrides.items() if v != float(defaults[k])}

    if by_distance:
        table = breakdown_from_distance(km, litres_per_100km, factor_id, pci_source, overrides)
        label = f"{T(ef['example'])}, {number(km)} km"
    else:
        table = breakdown_from_quantity(quantity, unit, factor_id, pci_source, overrides=overrides)
        label = f"{T(ef['example'])}, {number(quantity)} {unit}"

    by_unit = dict(zip(table["Unidad"], table["Valor"]))
    biogenic = bool(ef["biogenic_co2"])

    with right:
        st.subheader(T("Resultado"))
        a, b, c = st.columns(3)
        a.metric(T("Total"), f"{number(total_of(table))} kg CO2e")
        b.metric(T("Total"), f"{number(total_of(table, 't CO2e'))} t CO2e")
        c.metric(T("CO2 biogénico (memo)" if biogenic else "Solo CO2"), f"{number(by_unit['kg CO2'])} kg")
        if biogenic:
            st.info(T("El CO2 de la biomasa no suma al total del inventario: se informa aparte como partida informativa. Solo cuentan el CH4 y el N2O."))
        if overrides:
            st.warning(T("Cálculo con factores propios") + ": " + ", ".join(sorted(overrides)) + ".")
        show_steps(table)
        save_and_download(table, label, total_of(table), "combustion")
