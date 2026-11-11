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


def parse_number(text: str, language: str) -> float:
    """Read a number typed in Chilean (1.200.000,5) or English (1,200,000.5) style.

    When both separators appear, the last one is the decimal sign. With only
    one kind, groups of exactly three digits are read as thousands; a lone
    "1.200" is 1200 in Spanish and 1.2 in English.
    """
    t = text.strip().replace(" ", "").replace("\u00a0", "").replace("'", "")
    if not t:
        raise ValueError("empty")
    if "e" in t.lower():
        return float(t.replace(",", "."))
    negative = t.startswith("-")
    t = t.lstrip("+-")
    dots, commas = t.count("."), t.count(",")
    if dots and commas:
        decimal = "." if t.rfind(".") > t.rfind(",") else ","
        thousands = "," if decimal == "." else "."
        t = t.replace(thousands, "").replace(decimal, ".")
    elif dots or commas:
        sep = "." if dots else ","
        parts = t.split(sep)
        grouped = all(len(p) == 3 for p in parts[1:]) and 1 <= len(parts[0]) <= 3 and parts[0] != "0"
        thousands_sign = "." if language == "es" else ","
        if len(parts) > 2 or (grouped and sep == thousands_sign):
            if not grouped:
                raise ValueError(text)
            t = "".join(parts)
        else:
            t = t.replace(sep, ".")
    value = float(t)
    return -value if negative else value


def num_input(label, min_value=0.0, max_value=None, value=0.0, step=None, format=None, key=None, help=None) -> float:
    """Number box that accepts pasted numbers with thousands separators.

    Shows how the number was read whenever that differs from what was typed.
    """
    default = precise(float(value))
    text = st.text_input(label, value=default, key=f"{key or 'num_' + label}_{lang()}", help=help)
    try:
        number_read = parse_number(text, lang())
    except ValueError:
        st.error(T("No es un número válido. Se usa el valor por defecto:") + f" {default}")
        return float(value)
    if number_read < min_value or (max_value is not None and number_read > max_value):
        limit = min_value if number_read < min_value else max_value
        st.warning(T("Fuera del rango permitido. Se usa:") + f" {precise(limit)}")
        return float(limit)
    if text.strip() != precise(number_read):
        st.caption(f"= {precise(number_read)}")
    return number_read


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
