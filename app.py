"""Calculadora de emisiones GEI · Chile / GHG Emissions Calculator · Chile.

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
# Widget values are dropped when a widget is not drawn; keep the language across pages.
st.session_state["lang_choice"] = st.session_state.get("lang_choice") or "Español"

pages = {
    T(section): [
        st.Page(function, title=T(title), url_path=address, icon=icon, default=(address == "fuels"))
        for title, address, icon, function in entries
    ]
    for section, entries in SECTIONS.items()
}
page = st.navigation(pages)

with st.sidebar:
    st.segmented_control("Idioma / Language", list(LANGUAGES), key="lang_choice", selection_mode="single")
    st.divider()
    st.caption(T("Próximamente"))
    for name in PLANNED:
        st.caption(f"· {T(name)}")
    st.divider()
    st.caption(T("Directrices IPCC 2006 · Poderes caloríficos del Balance Nacional de Energía · Potenciales de calentamiento global del AR5"))

page.run()
