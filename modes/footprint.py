"""Organisational carbon footprint, following the HuellaChile report structure."""

import pandas as pd
import streamlit as st

from ghg_toolkit import CATEGORIES, footprint, load_emission_factors, load_fuel_properties, load_gwp, units_for

from .common import grid_selector, header, num_input, number, precise
from .i18n import T, lang

ELECTRICITY = "electricity"
OWN = "own"
UNITS = ["L", "kg", "t", "m3", "MJ", "TJ", "kWh", "MWh", "GWh", "otra"]
APPROACHES = ["Control operacional", "Control financiero", "Participación accionaria"]

EXAMPLE = [
    ("Calefacción de oficinas", "Combustión estacionaria", ("fuel", "1A4a_gas_natural"), 3000.0, "m3", None, None),
    ("Camionetas de la empresa", "Combustión móvil", ("fuel", "1A3b_diesel_liviano"), 8000.0, "L", None, None),
    ("Recarga de aire acondicionado", "Emisiones fugitivas", ("refrigerant", "HFC-134a"), 3.0, "kg", None, None),
    ("Electricidad de oficinas y bodega", "Electricidad importada", (ELECTRICITY, None), 120000.0, "kWh", None, None),
    ("Despacho subcontratado", "Transporte", ("fuel", "1A3b_diesel_camion"), 20000.0, "L", None, None),
]


def _factor_options() -> dict:
    """Label shown in the table -> (kind, key)."""
    factors = load_emission_factors()
    fuels = load_fuel_properties()
    options = {}
    for factor_id, r in factors.iterrows():
        label = f"{T('Combustible')} · {r['ipcc_category']} · {T(r['example'])} · {T(fuels.loc[r['fuel'], 'name'])}"
        options[label] = ("fuel", factor_id)
    options[T("Electricidad de la red")] = (ELECTRICITY, None)
    gwp = load_gwp()
    for gas, r in gwp.iterrows():
        if gas not in ("CO2", "CH4", "N2O"):
            options[f"{T('Gas refrigerante o fugitivo')} · {gas} (PCG {int(r['gwp'])})"] = ("refrigerant", gas)
    options[T("Factor propio (escribir el factor)")] = (OWN, None)
    return options


def _blank(value) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or value == ""


def render() -> None:
    header("Huella organizacional", "Inventario de emisiones de una organización por alcances, con la estructura del informe del programa HuellaChile (NCh-ISO 14064-1).")

    st.subheader(T("1. La organización"))
    a, b, c = st.columns(3)
    a.text_input(T("Organización"), value=T("Empresa de ejemplo"), key=f"fp_name_{lang()}")
    year = b.number_input(T("Año del inventario"), 1990, 2100, 2025, key="fp_year")
    c.selectbox(T("Enfoque para fijar los límites"), APPROACHES, format_func=T, key=f"fp_approach_{lang()}")
    d, e, f, g = st.columns(4)
    with d:
        workers = num_input(T("Trabajadores (personas)"), 0.0, None, 50.0, key="fp_workers")
    with e:
        area = num_input(T("Superficie (m2)"), 0.0, None, 2000.0, key="fp_area")
    with f:
        production = num_input(T("Producción total"), 0.0, None, 0.0, key="fp_production")
    with g:
        production_unit = st.text_input(T("Unidad de producción"), value="t", key=f"fp_production_unit_{lang()}")

    st.subheader(T("2. Fuentes de emisión"))
    st.markdown(T("Una fila por fuente. Elige la **categoría** (eso define el alcance) y el **factor**: un combustible, la electricidad de la red, un gas refrigerante o un factor propio. Dentro de la tabla los números van sin separador de miles y con punto decimal."))
    options = _factor_options()
    by_key = {v: k for k, v in options.items()}
    cols = {k: T(k) for k in ["Fuente", "Categoría", "Factor", "Cantidad", "Unidad", "Factor propio (kg CO2e por unidad)", "Fuente del factor propio"]}
    example = pd.DataFrame(
        [
            {
                cols["Fuente"]: T(name),
                cols["Categoría"]: T(category),
                cols["Factor"]: by_key[factor],
                cols["Cantidad"]: quantity,
                cols["Unidad"]: unit,
                cols["Factor propio (kg CO2e por unidad)"]: own,
                cols["Fuente del factor propio"]: own_source,
            }
            for name, category, factor, quantity, unit, own, own_source in EXAMPLE
        ]
    )
    example[cols["Cantidad"]] = example[cols["Cantidad"]].astype(float)
    example[cols["Factor propio (kg CO2e por unidad)"]] = example[cols["Factor propio (kg CO2e por unidad)"]].astype(float)
    example[cols["Fuente del factor propio"]] = example[cols["Fuente del factor propio"]].astype("string")
    category_labels = {T(c): c for c in CATEGORIES}
    edited = st.data_editor(
        example,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=f"fp_sources_{lang()}",
        column_config={
            cols["Fuente"]: st.column_config.TextColumn(required=True),
            cols["Categoría"]: st.column_config.SelectboxColumn(options=list(category_labels), required=True, width="medium"),
            cols["Factor"]: st.column_config.SelectboxColumn(options=list(options), required=True, width="large"),
            cols["Cantidad"]: st.column_config.NumberColumn(min_value=0, format="%.2f", required=True),
            cols["Unidad"]: st.column_config.SelectboxColumn(options=UNITS, required=True, width="small"),
            cols["Factor propio (kg CO2e por unidad)"]: st.column_config.NumberColumn(min_value=0, format="%.4f"),
            cols["Fuente del factor propio"]: st.column_config.TextColumn(),
        },
    )

    left, right = st.columns(2)
    with left:
        pci_source = st.radio(
            T("Poder calorífico de los combustibles"),
            ["bne", "ipcc"],
            format_func=lambda v: T({"bne": "Chile (BNE)", "ipcc": "IPCC por defecto"}[v]),
            horizontal=True,
            key=f"fp_pci_{lang()}",
        )
    with right:
        grid_factor, grid_source = grid_selector("footprint")

    sources, problems, hints = [], [], []
    for n, row in enumerate(edited.to_dict("records"), start=1):
        name = row.get(cols["Fuente"]) or f"{T('Fuente')} {n}"
        category_label, factor_label = row.get(cols["Categoría"]), row.get(cols["Factor"])
        quantity, unit = row.get(cols["Cantidad"]), row.get(cols["Unidad"])
        if any(_blank(v) for v in (category_label, factor_label, quantity, unit)):
            problems.append(f"{name}: " + T("falta la categoría, el factor, la cantidad o la unidad."))
            continue
        category = category_labels[category_label]
        kind, key = options[factor_label]
        source = {"name": name, "category": category, "kind": kind, "quantity": float(quantity), "unit": unit}
        if kind == "fuel":
            allowed = units_for(key)
            if unit not in allowed:
                problems.append(f"{name}: " + T("para este combustible la unidad debe ser una de") + f" {', '.join(allowed)}.")
                continue
            source["factor_id"] = key
        elif kind == ELECTRICITY:
            if unit not in ("kWh", "MWh", "GWh"):
                problems.append(f"{name}: " + T("la electricidad va en kWh, MWh o GWh."))
                continue
            if CATEGORIES[category] != 2:
                hints.append(f"{name}: " + T("la electricidad comprada suele ir en Alcance 2 (Electricidad importada)."))
        elif kind == "refrigerant":
            if unit != "kg":
                problems.append(f"{name}: " + T("los gases refrigerantes van en kg liberados."))
                continue
            source["gas"] = key
            if category != "Emisiones fugitivas":
                hints.append(f"{name}: " + T("las fugas de refrigerante suelen ir en Emisiones fugitivas (Alcance 1)."))
        else:
            own = row.get(cols["Factor propio (kg CO2e por unidad)"])
            if _blank(own):
                problems.append(f"{name}: " + T("falta el factor propio."))
                continue
            source["own_factor"] = float(own)
        sources.append(source)

    for problem in problems:
        st.warning(problem)
    for hint in hints:
        st.info(hint)
    if not sources:
        st.info(T("Agrega al menos una fuente para calcular la huella."))
        return

    result = footprint(sources, grid_factor, pci_source)
    total = result["total_t"]

    st.subheader(f"{T('Resultado')} {year}")
    m = st.columns(4)
    m[0].metric(f"{T('Total')} (t CO2e)", number(total))
    for i in (1, 2, 3):
        m[i].metric(f"{T('Alcance')} {i} (t CO2e)", number(result["scopes"][i]))
        if total:
            m[i].caption(f"{number(result['scopes'][i] / total * 100)} % {T('del total')}")
    st.caption(T("Electricidad calculada con") + f" {precise(grid_factor)} kg CO2e/kWh · {T(grid_source)}")

    chart = pd.DataFrame({"t CO2e": {f"{T('Alcance')} {i}": result["scopes"][i] for i in (1, 2, 3)}})
    st.bar_chart(chart, y_label="t CO2e", horizontal=True)

    st.subheader(T("Emisiones por categoría (Tabla 5 del informe HuellaChile)"))
    summary = result["summary"]
    table = pd.DataFrame(
        {
            T("Alcance"): summary["scope"].astype(str),
            T("Categoría"): summary["category"].map(T),
            T("Incluida"): summary["included"].map(lambda v: T("Sí") if v else T("No")),
            "t CO2e": summary["t_co2e"].map(number),
            "%": (summary["share"] * 100).map(number),
        }
    )
    table.loc[len(table)] = ["", T("Emisión GEI total"), "", number(total), number(100)]
    st.dataframe(table, width="stretch", hide_index=True, height=36 * (len(table) + 1) + 3, column_config={"t CO2e": st.column_config.TextColumn(alignment="right"), "%": st.column_config.TextColumn(alignment="right")})
    st.caption(T("Las categorías sin fuentes aparecen como no incluidas: en el informe hay que justificar si se excluyen o no aplican."))
    if result["biogenic_t"]:
        st.caption(T("Emisiones de carbono biogénico (informativas, no suman al total)") + f": {number(result['biogenic_t'])} t CO2")

    st.subheader(T("Indicadores de intensidad"))
    k = st.columns(3)
    k[0].metric(T("Por trabajador") + " (t CO2e)", number(total / workers) if workers else "–")
    k[1].metric(T("Por m2") + " (kg CO2e)", number(total * 1000 / area) if area else "–")
    k[2].metric(f"{T('Por unidad de producción')} (t CO2e/{production_unit})", number(total / production) if production else "–")

    st.subheader(T("Por fuente"))
    detail = result["by_source"].copy()
    detail = pd.DataFrame(
        {
            T("Fuente"): detail["name"],
            T("Categoría"): detail["category"].map(T),
            T("Alcance"): detail["scope"],
            "t CO2e": detail["t_co2e"].map(number),
            "%": (detail["t_co2e"] / total * 100 if total else detail["t_co2e"] * 0).map(number),
        }
    )
    st.dataframe(detail, width="stretch", hide_index=True, column_config={"t CO2e": st.column_config.TextColumn(alignment="right"), "%": st.column_config.TextColumn(alignment="right")})
    st.download_button(
        T("Descargar tabla (CSV para Excel)"),
        table.to_csv(index=False).encode("utf-8-sig"),
        file_name="huella_organizacional.csv" if lang() == "es" else "organisational_footprint.csv",
        mime="text/csv",
    )
    if st.button(T("Guardar para comparar"), type="primary", key="fp_save"):
        st.session_state["scenarios"][f"{T('Huella organizacional')} {year}"] = total * 1000
        st.toast(T("Guardado"))
