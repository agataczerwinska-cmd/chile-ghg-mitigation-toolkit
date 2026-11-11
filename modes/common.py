"""Formatting and widgets shared by every mode."""

import pandas as pd
import streamlit as st


def number(value: float) -> str:
    """Chilean-style number: 1.234.567,89"""
    decimals = 0 if abs(value) >= 1000 else 2 if abs(value) >= 1 else 4
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def precise(value: float) -> str:
    """Like number(), but keeps the decimals needed to follow the calculation."""
    if value == 0 or abs(value) >= 1:
        text = f"{value:,.2f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:.6g}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def show_steps(table: pd.DataFrame) -> None:
    """Step-by-step table: value and unit in separate columns."""
    st.subheader("Paso a paso")
    st.dataframe(
        table.assign(Valor=table["Valor"].map(precise)),
        width="stretch",
        height=38 * (len(table) + 1),
        column_config={"Valor": st.column_config.TextColumn(alignment="right")},
    )


def save_and_download(table: pd.DataFrame, default_name: str, total_kg_co2e: float, key: str) -> None:
    """Buttons to keep a result for comparison and to export the table."""
    save_col, download_col = st.columns(2)
    name = save_col.text_input("Nombre del escenario", value=default_name, label_visibility="collapsed", key=f"name_{key}")
    if save_col.button("Guardar para comparar", type="primary", key=f"save_{key}"):
        st.session_state["scenarios"][name] = total_kg_co2e
        st.toast(f"Guardado: {name}")
    download_col.download_button(
        "Descargar tabla (CSV para Excel)",
        table.to_csv(index=True).encode("utf-8-sig"),
        file_name="calculo_emisiones.csv",
        mime="text/csv",
        key=f"download_{key}",
    )
