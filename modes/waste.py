"""Landfill methane with the IPCC First Order Decay model."""

import streamlit as st

from ghg_toolkit import fod_series, half_life_years, load_waste_parameters

from .common import header, number, save_and_download
from .i18n import T, T_table


def _options(params, parameter):
    rows = params[params["parameter"] == parameter]
    return dict(zip(rows["item"], rows["value"].astype(float)))


def render() -> None:
    params = load_waste_parameters()
    doc_by_type = _options(params, "DOC")
    mcf_by_site = _options(params, "MCF")
    header("Rellenos sanitarios", "Metano de los residuos enterrados, año a año, con el modelo de descomposición de primer orden del IPCC.")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(T("1. ¿Qué residuo y dónde?"))
        waste_type = st.selectbox(T("Tipo de residuo"), list(doc_by_type), format_func=T)
        site = st.selectbox(T("Sitio de disposición"), list(mcf_by_site), format_func=T)
        zone = st.radio(T("Macrozona"), ["k seco (Norte)", "k húmedo (Sur)"], format_func=lambda z: T("Norte (seca)" if "seco" in z else "Sur (húmeda)"), horizontal=True, index=1)

        st.subheader(T("2. ¿Cuánto y cuándo?"))
        tonnes = st.number_input(T("Residuos depositados (t por año)"), min_value=0.0, value=1000.0, step=100.0)
        first, last = st.slider(T("Años de depósito"), 1990, 2050, (2014, 2050))
        stop = st.checkbox(T("Dejar de depositar desde un año"), help=T("Sirve para ver la inercia: el relleno sigue emitiendo después de cerrar o de desviar el residuo."))
        stop_year = st.slider(T("Último año con depósito"), first, last, min(2030, last)) if stop else last

        st.subheader(T("3. Parámetros"))
        key = f"{waste_type}_{site}_{zone}"
        k_default = _options(params, zone).get(waste_type, 0.05)
        with st.expander(T("Ver o cambiar (Nivel 2 o dato específico)")):
            doc = st.number_input(T("DOC (fracción)"), 0.0, 1.0, doc_by_type[waste_type], format="%.3f", key=f"doc_{key}")
            k = st.number_input(T("k (1/año)"), 0.001, 1.0, k_default, format="%.3f", key=f"k_{key}")
            mcf = st.number_input(T("MCF (fracción)"), 0.0, 1.0, mcf_by_site[site], format="%.2f", key=f"mcf_{key}")
            docf = st.number_input(T("DOCf (fracción)"), 0.0, 1.0, _options(params, "DOCf")["Por defecto"], format="%.2f")
            f = st.number_input(T("F, fracción de CH4 en el biogás"), 0.0, 1.0, _options(params, "F")["Por defecto"], format="%.2f")
            recovered = st.number_input(T("R, fracción de CH4 capturado"), 0.0, 1.0, 0.0, format="%.2f", help=T("Medida de mitigación: captura y quema o uso del biogás."))
            ox = st.number_input(T("OX, oxidación en la cubierta"), 0.0, 1.0, _options(params, "OX")["Por defecto"], format="%.2f")

    deposits = {year: (tonnes if year <= stop_year else 0.0) for year in range(first, last + 1)}
    series = fod_series(deposits, doc=doc, k=k, mcf=mcf, docf=docf, f=f, recovered_fraction=recovered, ox=ox)

    with right:
        st.subheader(T("Resultado"))
        a, b, c = st.columns(3)
        a.metric(f"{T('Emisiones en')} {last}", f"{number(series['Emisiones (t CO2e)'].iloc[-1])} t CO2e")
        b.metric(f"{T('Acumulado')} {first}–{last}", f"{number(series['Emisiones (t CO2e)'].sum())} t CO2e")
        c.metric(T("Vida media del residuo"), f"{number(half_life_years(k))} {T('años')}")
        st.line_chart(series["Emisiones (t CO2e)"].rename(index=str), y_label=T("t CO2e por año"), x_label=T("Año"))
        st.caption(T("Lo depositado en un año empieza a emitir al año siguiente. Parámetros:") + " " + f"DOC {doc:g} · DOCf {docf:g} · MCF {mcf:g} · k {k:g} · F {f:g} · R {recovered:g} · OX {ox:g}")

        st.subheader(T("Año a año"))
        st.dataframe(T_table(series).style.format(number), width="stretch", height=420)
        label = f"{T(waste_type)}, {T(site)}, {number(tonnes)} {T('t/año')} ({last})"
        save_and_download(series, label, series["Emisiones (t CO2e)"].iloc[-1] * 1000, "waste")
