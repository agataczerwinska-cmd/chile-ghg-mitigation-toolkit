"""GHG Emissions Calculator · Chile / Calculadora de emisiones GEI · Chile.

Run locally with:  streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st

from modes import PLANNED, SECTIONS
from modes.i18n import LANGUAGES, T

st.set_page_config(page_title="GHG Calculator · Chile (beta)", page_icon="🌎", layout="wide")
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
page = st.navigation(pages, position="hidden")

with st.sidebar:
    st.segmented_control("Language / Idioma", list(LANGUAGES), key="lang_choice", selection_mode="single", label_visibility="collapsed")
    for section, section_pages in pages.items():
        st.caption(section)
        for p in section_pages:
            st.page_link(p, label=p.title, icon=p.icon)
    st.divider()
    st.caption(T("Próximamente"))
    for name in PLANNED:
        st.caption(f"· {T(name)}")
    st.divider()
    st.caption(T("Directrices IPCC 2006 · Poderes caloríficos del Balance Nacional de Energía · Potenciales de calentamiento global del AR5"))

st.badge(T("Beta · en desarrollo"), icon=":material/science:", color="orange")
st.caption(T("Herramienta de aprendizaje creada durante un curso. Revisa los resultados con fuentes oficiales antes de usarlos en un informe."))

page.run()
