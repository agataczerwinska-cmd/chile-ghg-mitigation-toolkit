"""Build the emission factor of an electricity system from its power plants."""

import pandas as pd
import streamlit as st

from ghg_toolkit import RENEWABLE, breakdown_from_quantity, grid_factor, load_emission_factors, load_fuel_properties, units_for

from .common import ef_note, header, num_input, number, pci_note, precise
from .i18n import T, lang

RENEWABLE_LABEL = "Renovable: solar, eólica, hidro, geotermia (sin emisiones)"

EXAMPLE = [
    {"Central": "Central a carbón", "type": "1A1_carbon_bituminoso", "Generación (MWh)": 1_000_000.0, "Eficiencia (%)": 38.0, "Combustible quemado": None, "Unidad del combustible": None},
    {"Central": "Ciclo combinado", "type": "1A1_gas_natural", "Generación (MWh)": 800_000.0, "Eficiencia (%)": 55.0, "Combustible quemado": None, "Unidad del combustible": None},
    {"Central": "Parque solar", "type": RENEWABLE, "Generación (MWh)": 1_200_000.0, "Eficiencia (%)": None, "Combustible quemado": None, "Unidad del combustible": None},
    {"Central": "Parque eólico", "type": RENEWABLE, "Generación (MWh)": 500_000.0, "Eficiencia (%)": None, "Combustible quemado": None, "Unidad del combustible": None},
]


def _types() -> dict:
    """Label shown in the table -> factor id."""
    factors = load_emission_factors()
    fuels = load_fuel_properties()
    plants = factors[(factors["ipcc_category"] == "1A1") & (factors["use"] == "Generación eléctrica")]
    labels = {f"{T(r['example'])} · {T(fuels.loc[r['fuel'], 'name'])}": i for i, r in plants.iterrows()}
    labels[T(RENEWABLE_LABEL)] = RENEWABLE
    return labels


def _blank(value) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or value == ""


def render() -> None:
    header("Factor de la red", "Calcula el factor de emisión de un sistema eléctrico (un país, una región o una empresa generadora) a partir de sus centrales.")
    types = _types()
    by_id = {v: k for k, v in types.items()}
    cols = {
        "Central": T("Central"),
        "Tipo": T("Tipo de central"),
        "Generación (MWh)": T("Generación (MWh)"),
        "Eficiencia (%)": T("Eficiencia (%)"),
        "Combustible quemado": T("Combustible quemado"),
        "Unidad del combustible": T("Unidad del combustible"),
    }

    st.markdown(T("**Cómo llenar la tabla.** Una fila por central. Para las centrales térmicas basta con la generación y la eficiencia; si conoces el combustible quemado en el año, escríbelo con su unidad y se usa ese dato en lugar de la eficiencia. Agrega o borra filas con los controles de la tabla. Dentro de la tabla los números se escriben sin separador de miles y con punto decimal."))

    example = pd.DataFrame(
        [
            {
                cols["Central"]: T(row["Central"]),
                cols["Tipo"]: by_id[row["type"]],
                cols["Generación (MWh)"]: row["Generación (MWh)"],
                cols["Eficiencia (%)"]: row["Eficiencia (%)"],
                cols["Combustible quemado"]: row["Combustible quemado"],
                cols["Unidad del combustible"]: row["Unidad del combustible"],
            }
            for row in EXAMPLE
        ]
    )
    for column in (cols["Generación (MWh)"], cols["Eficiencia (%)"], cols["Combustible quemado"]):
        example[column] = example[column].astype(float)
    example[cols["Unidad del combustible"]] = example[cols["Unidad del combustible"]].astype("string")
    edited = st.data_editor(
        example,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=f"grid_plants_{lang()}",
        column_config={
            cols["Central"]: st.column_config.TextColumn(required=True),
            cols["Tipo"]: st.column_config.SelectboxColumn(options=list(types), required=True, width="large"),
            cols["Generación (MWh)"]: st.column_config.NumberColumn(min_value=0, format="%.0f", required=True),
            cols["Eficiencia (%)"]: st.column_config.NumberColumn(min_value=1, max_value=100, format="%.1f"),
            cols["Combustible quemado"]: st.column_config.NumberColumn(min_value=0, format="%.0f"),
            cols["Unidad del combustible"]: st.column_config.SelectboxColumn(options=["L", "kg", "t", "m3", "TJ"]),
        },
    )

    left, right = st.columns([1, 2], gap="large")
    with left:
        st.subheader(T("Opciones"))
        pci_source = st.radio(
            T("Poder calorífico"),
            ["bne", "ipcc"],
            format_func=lambda v: T({"bne": "Chile (BNE)", "ipcc": "IPCC por defecto"}[v]),
            horizontal=True,
            key=f"grid_pci_{lang()}",
        )
        st.caption(T("Solo se usa en filas con combustible quemado."))
        pci_box = st.container()
        losses = num_input(T("Pérdidas de transmisión y distribución (%)"), 0.0, 99.0, 0.0, key="grid_losses", help=T("Si las indicas, también se calcula el factor por kWh consumido, que es mayor que el factor por kWh generado."))

    plants, problems = [], []
    for n, row in enumerate(edited.to_dict("records"), start=1):
        name = row.get(cols["Central"]) or f"{T('Central')} {n}"
        type_label = row.get(cols["Tipo"])
        generation = row.get(cols["Generación (MWh)"])
        if _blank(type_label) or _blank(generation):
            problems.append(f"{name}: " + T("falta el tipo de central o la generación."))
            continue
        factor_id = types[type_label]
        plant = {"name": name, "factor_id": factor_id, "generation_mwh": float(generation)}
        if factor_id != RENEWABLE:
            fuel = row.get(cols["Combustible quemado"])
            unit = row.get(cols["Unidad del combustible"])
            efficiency = row.get(cols["Eficiencia (%)"])
            if not _blank(fuel):
                if _blank(unit) or unit not in units_for(factor_id):
                    problems.append(f"{name}: " + T("la unidad del combustible debe ser una de") + f" {', '.join(units_for(factor_id))}.")
                    continue
                plant.update(fuel_quantity=float(fuel), fuel_unit=unit)
            elif not _blank(efficiency):
                plant["efficiency"] = float(efficiency) / 100
            else:
                problems.append(f"{name}: " + T("falta la eficiencia o el combustible quemado."))
                continue
        plants.append(plant)

    for problem in problems:
        st.warning(problem)
    if not plants or sum(p["generation_mwh"] for p in plants) <= 0:
        st.info(T("Agrega al menos una central con generación para calcular el factor."))
        return

    result = grid_factor(plants, losses / 100, pci_source)

    with pci_box:
        for p in plants:
            if p["factor_id"] == RENEWABLE:
                continue
            if p.get("fuel_quantity"):
                st.caption(f"{p['name']} · {pci_note(p['factor_id'], p['fuel_unit'], pci_source)}")
                steps = breakdown_from_quantity(p["fuel_quantity"], p["fuel_unit"], p["factor_id"], pci_source)
                fuel_tj = float(steps[steps["Unidad"] == "TJ"]["Valor"].iloc[0])
                implied = p["generation_mwh"] * 0.0036 / fuel_tj * 100 if fuel_tj else float("inf")
                message = f"{p['name']}: " + T("con ese combustible, la eficiencia sería de") + f" {number(implied)} %."
                if implied > 100 or implied < 15:
                    st.warning(message + " " + T("No es posible: revisa la cantidad y la unidad del combustible quemado en el año."))
                else:
                    st.caption(message)
            else:
                unit = next(u for u in units_for(p["factor_id"]) if u not in ("MJ", "TJ"))
                st.caption(f"{p['name']} · {pci_note(p['factor_id'], unit, pci_source)} · " + T("no se usa en esta fila"))

    with right:
        st.subheader(T("Resultado"))
        a, b = st.columns(2)
        a.metric(f"{T('Factor por kWh generado')} (kg CO2e/kWh)", precise(result["factor_generation"]))
        if losses:
            b.metric(f"{T('Factor por kWh consumido')} (kg CO2e/kWh)", precise(result["factor_consumption"]))
        c, d = st.columns(2)
        c.metric(f"{T('Generación total')} (MWh)", number(result["generation_mwh"]))
        d.metric(f"{T('Emisiones totales')} (t CO2e)", number(result["emissions_t"]))
        st.caption(T("Factor = emisiones de todas las centrales ÷ electricidad generada. Las emisiones de cada central térmica se calculan como en la página Combustibles (CO2, CH4 y N2O, categoría 1A1)."))

    table = result["plants"].rename(
        columns={
            "name": T("Central"),
            "generation_mwh": T("Generación (MWh)"),
            "emissions_t": T("Emisiones (t CO2e)"),
            "intensity_kg_kwh": T("Intensidad (kg CO2e/kWh)"),
            "share_generation": T("% de la generación"),
            "share_emissions": T("% de las emisiones"),
        }
    )
    for column in (T("% de la generación"), T("% de las emisiones")):
        table[column] = table[column] * 100
    st.subheader(T("Por central"))
    st.dataframe(
        table.style.format(
            {
                T("Generación (MWh)"): number,
                T("Emisiones (t CO2e)"): number,
                T("Intensidad (kg CO2e/kWh)"): lambda v: "–" if pd.isna(v) else precise(v),
                T("% de la generación"): lambda v: number(v),
                T("% de las emisiones"): lambda v: number(v),
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.caption(T("Factores de emisión usados"))
    for type_label, factor_id in types.items():
        if factor_id != RENEWABLE and any(p["factor_id"] == factor_id for p in plants):
            st.caption(f"· {type_label}: {ef_note(factor_id)}")

    st.subheader(T("Usar este factor"))
    name_col, button_col = st.columns([2, 1])
    name = name_col.text_input(T("Nombre del sistema"), value=T("Sistema calculado"), key=f"grid_name_{lang()}", label_visibility="collapsed")
    value = result["factor_consumption"] if losses else result["factor_generation"]
    if button_col.button(T("Usar en Electricidad y Electrificar"), type="primary"):
        st.session_state["calculated_grid"] = {"name": name, "value": value}
        st.toast(T("Listo: elige «Factor calculado» en el selector Red de esas páginas."))
