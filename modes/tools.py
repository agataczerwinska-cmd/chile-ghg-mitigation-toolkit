"""Pages that work across sectors: scenario comparison and reference tables."""

import pandas as pd
import streamlit as st

from ghg_toolkit import TABLE_FILES, reload_tables
from ghg_toolkit.factors import DATA_DIR

from .common import header
from .i18n import T

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


def _running_locally() -> bool:
    """Tables can be edited only on your own computer, not on the public site."""
    host = st.context.headers.get("host", "")
    return host.startswith(("localhost", "127.0.0.1"))


def render_compare() -> None:
    header("Comparar escenarios", "")
    scenarios = st.session_state["scenarios"]
    if not scenarios:
        st.info(T("Todavía no hay escenarios. En cualquier calculadora, pulsa «Guardar para comparar» en cada caso que quieras comparar. Puedes mezclar sectores: por ejemplo, un bus diésel y la electricidad de un bus eléctrico."))
        return
    kg, t, diff = T("Total (kg CO2e)"), T("Total (t CO2e)"), T("Diferencia vs el primero (%)")
    comparison = pd.DataFrame({kg: scenarios})
    comparison[t] = comparison[kg] / 1000
    reference = comparison[kg].iloc[0]
    comparison[diff] = (comparison[kg] / reference - 1) * 100 if reference else 0.0
    st.bar_chart(comparison[t], y_label="t CO2e", horizontal=True)
    st.dataframe(
        comparison,
        width="stretch",
        column_config={
            kg: st.column_config.NumberColumn(format="localized"),
            t: st.column_config.NumberColumn(format="localized"),
            diff: st.column_config.NumberColumn(format="%.1f %%"),
        },
    )
    if st.button(T("Borrar escenarios")):
        st.session_state["scenarios"] = {}
        st.rerun()


def render_tables() -> None:
    header("Factores y tablas", "")
    choice = st.selectbox(T("Tabla"), list(TABLE_NAMES), format_func=T)
    path = DATA_DIR / TABLE_NAMES[choice]
    original = pd.read_csv(path, dtype={"ipcc_table": str})
    if not _running_locally():
        st.caption(f"{T('Archivo')}: data/{path.name}. " + T("Tablas de solo lectura en la versión en línea. Los datos están en español, tal como en sus fuentes."))
        st.dataframe(original, width="stretch", hide_index=True, height=560)
        return
    st.caption(f"{T('Archivo')}: data/{path.name}. " + T("Puedes cambiar valores, o agregar filas al final (por ejemplo, un factor chileno de Nivel 2 con su fuente). Los cálculos usan la tabla guardada."))
    edited = st.data_editor(original, num_rows="dynamic", width="stretch", hide_index=True, height=560, key=f"editor_{path.name}")
    if st.button(T("Guardar cambios"), type="primary", disabled=edited.equals(original)):
        edited.to_csv(path, index=False)
        reload_tables()
        st.toast(f"{T('Guardado en')} data/{path.name}")
        st.rerun()
