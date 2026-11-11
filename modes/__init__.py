"""Pages of the visual calculator, grouped by inventory sector.

To add a calculator: create a file here with a render() function, then add
one line to SECTIONS below (and its English names to i18n.py).
"""

from . import combustion, electricity, electrification, forestry, tools, waste

# section -> [(page title, address, icon, function)]
SECTIONS = {
    "Energía": [
        ("Combustibles", "fuels", ":material/local_gas_station:", combustion.render),
        ("Electricidad", "electricity", ":material/bolt:", electricity.render),
        ("Electrificar un equipo", "electrify", ":material/ev_station:", electrification.render),
    ],
    "Residuos": [
        ("Rellenos sanitarios", "landfills", ":material/delete:", waste.render),
    ],
    "Uso de la tierra": [
        ("Bosques", "forests", ":material/forest:", forestry.render),
    ],
    "Herramientas": [
        ("Comparar escenarios", "compare", ":material/compare_arrows:", tools.render_compare),
        ("Factores y tablas", "tables", ":material/table:", tools.render_tables),
    ],
}

PLANNED = [
    "Agropecuario",
    "Huella de carbono (organizacional, comunal, eventos)",
    "Proyectos de mitigación y análisis económico",
    "Escenarios y proyección",
]
