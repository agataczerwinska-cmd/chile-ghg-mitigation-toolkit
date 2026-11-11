"""Calculadora de emisiones GEI: interfaz visual del toolkit.

Run locally with:  streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import streamlit as st

from ghg_toolkit import TABLE_FILES, reload_tables
from ghg_toolkit.factors import DATA_DIR
from modes import MODES, PLANNED

TABLE_NAMES = {
    "Factores de emisión por categoría": "emission_factors.csv",
    "Combustibles: densidad y poder calorífico": "fuel_properties.csv",
    "Potenciales de calentamiento global (AR5)": "gwp_ar5.csv",
    "Conversiones de unidades": "conversions.csv",
    "Factores de la red eléctrica": "grid_emission_factors.csv",
    "Residuos: DOC, k, MCF": "waste_parameters.csv",
    "Forestal: densidad, FEB y raíces": "forest_factors.csv",
    "Densidad de la leña por especie": "wood_density.csv",
}
assert set(TABLE_NAMES.values()) == set(TABLE_FILES)

st.set_page_config(page_title="Calculadora de emisiones GEI · Chile", page_icon="🌎", layout="wide")
st.session_state.setdefault("scenarios", {})

with st.sidebar:
    st.header("Modo de cálculo")
    mode = st.radio("Modo", list(MODES), label_visibility="collapsed")
    st.divider()
    st.caption("Próximos módulos")
    for name in PLANNED:
        st.caption(f"· {name}")

st.title("Calculadora de emisiones GEI · Chile")
st.caption("Directrices IPCC 2006 · Poderes caloríficos del Balance Nacional de Energía · Potenciales de calentamiento global del AR5")

tab_calc, tab_compare, tab_tables = st.tabs(["Calcular", "Comparar escenarios", "Factores y tablas"])

with tab_calc:
    MODES[mode].render()

with tab_compare:
    scenarios = st.session_state["scenarios"]
    if not scenarios:
        st.info("Todavía no hay escenarios. En la pestaña Calcular, pulsa «Guardar para comparar» en cada caso que quieras comparar. Puedes mezclar modos: por ejemplo, un bus diésel y la electricidad de un bus eléctrico.")
    else:
        comparison = pd.DataFrame({"Total (kg CO2e)": scenarios})
        comparison["Total (t CO2e)"] = comparison["Total (kg CO2e)"] / 1000
        reference = comparison["Total (kg CO2e)"].iloc[0]
        comparison["Diferencia vs el primero (%)"] = (comparison["Total (kg CO2e)"] / reference - 1) * 100 if reference else 0.0
        st.bar_chart(comparison["Total (t CO2e)"], y_label="t CO2e", horizontal=True)
        st.dataframe(
            comparison,
            width="stretch",
            column_config={
                "Total (kg CO2e)": st.column_config.NumberColumn(format="localized"),
                "Total (t CO2e)": st.column_config.NumberColumn(format="localized"),
                "Diferencia vs el primero (%)": st.column_config.NumberColumn(format="%.1f %%"),
            },
        )
        if st.button("Borrar escenarios"):
            st.session_state["scenarios"] = {}
            st.rerun()

with tab_tables:
    choice = st.selectbox("Tabla", list(TABLE_NAMES))
    path = DATA_DIR / TABLE_NAMES[choice]
    st.caption(f"Archivo: data/{path.name}. Puedes cambiar valores, o agregar filas al final (por ejemplo, un factor chileno de Nivel 2 con su fuente). Los cálculos usan la tabla guardada.")
    original = pd.read_csv(path, dtype={"ipcc_table": str})
    edited = st.data_editor(original, num_rows="dynamic", width="stretch", hide_index=True, height=560, key=f"editor_{path.name}")
    if st.button("Guardar cambios", type="primary", disabled=edited.equals(original)):
        edited.to_csv(path, index=False)
        reload_tables()
        st.toast(f"Guardado en data/{path.name}")
        st.rerun()
