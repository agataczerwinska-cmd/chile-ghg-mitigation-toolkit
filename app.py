"""GHG Emissions Calculator · Chile / Calculadora de emisiones GEI · Chile.

Run locally with:  streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st

from modes import PLANNED, SECTIONS
from modes.i18n import LANGUAGES, T

st.set_page_config(page_title="GHG Calculator · Chile", page_icon="🌎", layout="wide")
st.session_state.setdefault("scenarios", {})
# Keep the language across pages; English unless the visitor picks Spanish.
st.session_state["lang_choice"] = st.session_state.get("lang_choice") or "English"

pages = {
    T(section): [
        st.Page(function, title=T(title), url_path=address, icon=icon, default=(address == "fuels"))
        for title, address, icon, function in entries
    ]
    for section, entries in SECTIONS.items()
}
page = st.navigation(pages)

language_column, _ = st.columns([1, 4])
with language_column:
    st.segmented_control("Language / Idioma", list(LANGUAGES), key="lang_choice", selection_mode="single", label_visibility="collapsed")

with st.sidebar:
    st.caption(T("Próximamente"))
    for name in PLANNED:
        st.caption(f"· {T(name)}")
    st.divider()
    st.caption(T("Directrices IPCC 2006 · Poderes caloríficos del Balance Nacional de Energía · Potenciales de calentamiento global del AR5"))

page.run()
