"""Formatting and widgets shared by every page."""

import pandas as pd
import streamlit as st

from .i18n import T, T_table, lang


def _local(text: str) -> str:
    """1,234.56 in English; 1.234,56 in Spanish."""
    if lang() == "en":
        return text
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def number(value: float) -> str:
    decimals = 0 if abs(value) >= 1000 else 2 if abs(value) >= 1 else 4
    return _local(f"{value:,.{decimals}f}")


def precise(value: float) -> str:
    """Like number(), but keeps the decimals needed to follow the calculation."""
    if value == 0 or abs(value) >= 1:
        return _local(f"{value:,.2f}".rstrip("0").rstrip("."))
    return _local(f"{value:.6g}")


def header(title: str, description: str) -> None:
    st.title(T(title))
    if description:
        st.caption(T(description))


def show_steps(table: pd.DataFrame) -> None:
    """Step-by-step table: value and unit in separate columns."""
    st.subheader(T("Paso a paso"))
    shown = T_table(table.assign(Valor=table["Valor"].map(precise)))
    st.dataframe(
        shown,
        width="stretch",
        height=38 * (len(shown) + 1),
        column_config={shown.columns[1]: st.column_config.TextColumn(alignment="right")},
    )


def save_and_download(table: pd.DataFrame, default_name: str, total_kg_co2e: float, key: str) -> None:
    """Buttons to keep a result for comparison and to export the table."""
    save_col, download_col = st.columns(2)
    name = save_col.text_input(T("Nombre del escenario"), value=default_name, label_visibility="collapsed", key=f"name_{key}_{lang()}")
    if save_col.button(T("Guardar para comparar"), type="primary", key=f"save_{key}"):
        st.session_state["scenarios"][name] = total_kg_co2e
        st.toast(f"{T('Guardado')}: {name}")
    download_col.download_button(
        T("Descargar tabla (CSV para Excel)"),
        T_table(table).to_csv(index=True).encode("utf-8-sig"),
        file_name="calculo_emisiones.csv" if lang() == "es" else "emissions_calculation.csv",
        mime="text/csv",
        key=f"download_{key}",
    )
