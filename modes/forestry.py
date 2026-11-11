"""Forest land: from wood volume to CO2, with Chilean national factors."""

import streamlit as st

from ghg_toolkit import (
    breakdown_from_biomass_growth,
    breakdown_from_forest_growth,
    load_forest_growth,
    breakdown_from_wood_volume,
    load_forest_factors,
    total_of,
)

from .common import header, num_input, number, save_and_download, show_steps
from .i18n import T, lang

CASES = {
    "Crecimiento de bosque nativo o plantación (captura)": "growth",
    "Cosecha o raleo (emisión)": "volume_out",
    "Consumo de leña (emisión)": "volume_out",
    "Incendio: biomasa quemada (emisión de CO2)": "volume_out",
}


def render() -> None:
    factors = load_forest_factors()
    header("Bosques", "Captura y emisión de CO2 de los bosques a partir del volumen de madera, con factores nacionales de Chile.")
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(T("1. ¿Qué flujo del bosque?"))
        case = st.radio(T("Caso"), list(CASES), format_func=T, label_visibility="collapsed")

        st.subheader(T("2. ¿Cuánto?"))
        use_table = False
        if CASES[case] == "growth":
            area = num_input(T("Superficie (ha)"), min_value=0.0, value=100.0, step=10.0)
            use_table = st.radio(
                T("Dato de crecimiento"),
                ["table", "volume"],
                format_func=lambda v: T({"table": "Tabla del INGEI 2024 (t/ha/año)", "volume": "Volumen escrito por mí (m3/ha/año)"}[v]),
                key=f"growth_source_{lang()}",
            ) == "table"
            if use_table:
                growth_table = load_forest_growth()
                forest = st.radio(T("Tipo de bosque"), ["Plantación", "Bosque nativo"], format_func=T, horizontal=True, key=f"forest_kind_{lang()}")
                rows = growth_table[growth_table["forest"] == forest]
                kind = st.selectbox(T("Especie o tipo forestal"), list(dict.fromkeys(rows["type"])), format_func=T, key=f"growth_type_{forest}_{lang()}")
                rows = rows[rows["type"] == kind]
                if forest == "Plantación":
                    region = st.selectbox(T("Región"), list(rows["region"]), key=f"growth_region_{kind}")
                    row = rows[rows["region"] == region].iloc[0]
                else:
                    row = rows.iloc[0]
                growth = num_input(T("Crecimiento anual de biomasa (t/ha/año)"), 0.0, None, float(row["growth_t_ha_year"]), key=f"growth_value_{kind}_{row['region']}")
                species = row["factor_species"]
                f = factors.loc[species]
                growth_source = str(row["source"])
                st.caption(T("Se toma como biomasa aérea: no se aplican la densidad ni el FEB. Raíces con los factores de") + f" «{T(species)}».")
            else:
                species = st.selectbox(T("Especie"), list(factors.index), format_func=T, key=f"species_{lang()}")
                f = factors.loc[species]
                growth = num_input(T("Crecimiento anual (m3/ha/año)"), min_value=0.0, value=6.0, step=0.5, help=T("Incremento del volumen de madera. Usa el valor de tu fuente (INFOR, INGEI) para la especie y la región."))
        else:
            species = st.selectbox(T("Especie"), list(factors.index), format_func=T, key=f"species_{lang()}")
            f = factors.loc[species]
            volume = num_input(T("Volumen de madera (m3)"), min_value=0.0, value=1000.0, step=100.0)

        st.subheader(T("3. Factores"))
        overrides = {}
        with st.expander(T("Ver o cambiar (dato específico)")):
            values = {
                "density": num_input(T("Densidad (t/m3)"), 0.0, 2.0, float(f["density_t_m3"]), format="%.2f", key=f"d_{species}"),
                "feb": num_input(T("Factor de expansión de biomasa (FEB)"), 0.0, 5.0, float(f["feb"]), format="%.2f", key=f"feb_{species}"),
                "root_ratio": num_input(T("Proporción de raíces (R)"), 0.0, 2.0, float(f["root_ratio"]), format="%.2f", key=f"r_{species}"),
                "carbon_fraction": num_input(T("Fracción de carbono (FC)"), 0.0, 1.0, 0.5, format="%.2f"),
            }
            defaults = {"density": f["density_t_m3"], "feb": f["feb"], "root_ratio": f["root_ratio"], "carbon_fraction": 0.5}
            overrides = {k: v for k, v in values.items() if v != float(defaults[k])}

    if use_table:
        table = breakdown_from_biomass_growth(area, growth, species, overrides, growth_source)
        label = f"{T('Captura')} {T(kind)}, {number(area)} ha"
    elif CASES[case] == "growth":
        table = breakdown_from_forest_growth(area, growth, species, overrides)
        label = f"{T('Captura')} {T(species)}, {number(area)} ha"
    else:
        table = breakdown_from_wood_volume(volume, species, overrides=overrides)
        label = f"{T(species)}, {number(volume)} m3"

    with right:
        st.subheader(T("Resultado"))
        total = total_of(table, "t CO2e")
        a, b = st.columns(2)
        a.metric(T("Captura (por año)" if total < 0 else "Emisión"), f"{number(abs(total))} t CO2")
        b.metric(T("En el balance"), f"{number(total)} t CO2e", help=T("Las capturas van con signo negativo."))
        if use_table:
            st.caption(T("CO2 = superficie × crecimiento de biomasa × (1 + R) × FC × 44/12. Crecimiento del INGEI 2024; raíces de Gayoso et al. (2002); fracción de carbono del IPCC 2006."))
        else:
            st.caption(T("CO2 = V × D × FEB × (1 + R) × FC × 44/12. Factores nacionales del INGEI (Gayoso et al., 2002) y fracción de carbono del IPCC 2006."))
        if isinstance(f["note"], str) and f["note"]:
            st.caption(f"{T('Nota')}: {T(f['note'])}.")
        if case.startswith("Incendio"):
            st.caption(T("Solo se calcula el CO2 de la biomasa. Un incendio emite además CH4 y N2O, que esta herramienta todavía no incluye."))
        show_steps(table)
        save_and_download(table, label, total_of(table), "forestry")
