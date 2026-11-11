# Chile GHG Mitigation Toolkit

**Live calculator / Calculadora en línea: https://chile-ghg-calculator.streamlit.app/**

**Status: beta.** A learning project, still in development. Check results against official sources before using them in a report. / **Estado: beta.** Proyecto de aprendizaje en desarrollo; revisa los resultados con fuentes oficiales antes de usarlos en un informe.

Small Python toolkit for greenhouse gas emission calculations and mitigation
scenarios, built while taking the course *Mitigación y Modelación de Políticas
Climáticas* (Diploma Cambio Climático y Desarrollo Resiliente, Universidad de
Chile).

*Herramientas en Python para calcular emisiones de gases de efecto invernadero
y modelar medidas de mitigación, desarrolladas durante el curso Mitigación y
Modelación de Políticas Climáticas (Universidad de Chile).*

## What it does / Qué hace

Fuel combustion follows the IPCC 2006 Tier 1 method, with the option of
replacing any default with a country-specific value (Tier 2):

```
emissions [kg gas] = activity data [TJ] x emission factor [kg gas / TJ]
```

and converts to CO2e with the IPCC AR5 GWPs (CH4 = 28, N2O = 265), the same
ones Chile's national inventory (INGEI) uses.

## Visual calculator / Calculadora visual

`app.py` is a point-and-click calculator in English (default) and Spanish, with one
page per emission source, grouped by inventory sector. Every result comes with the full calculation chain: each
step, its value, its unit and its source.

| Calculator | Method | Status |
|---|---|---|
| Fuel combustion (power, industry and mining, transport, buildings) | IPCC 2006 Vol. 2, Tier 1, or your own factors (Tier 2) | Done |
| Grid electricity | Consumption x grid factor | Done |
| Electrifying a machine or vehicle (fuel vs electric, by useful work or by distance, for one unit or a fleet) | Efficiencies or consumption per km, grid factor, break-even | Done |
| Grid emission factor of a country, region or generating company, built plant by plant | Emissions of all plants / electricity generated, with optional losses | Done |
| Landfill methane | IPCC 2006 Vol. 5, First Order Decay | Done |
| Forest land: wood volume to CO2 (harvest, firewood, fire, growth) | IPCC 2006 with Chilean national factors (Gayoso et al.) and inventory growth tables (INGEI 2024) | Done |
| Agriculture, mitigation projects (emission reductions and economics), scenarios | – | Planned |

It also compares saved scenarios across sectors and shows every reference
table. When run locally the tables are editable, so country-specific (Tier 2)
factors can be added as rows with their source.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Adding a calculator takes one file in `modes/` with a `render()` function,
one line in `modes/__init__.py`, and its English labels in `modes/i18n.py`.

## Quick start (Python package)

```bash
pip install -e ".[dev]"
pytest
```

```python
from ghg_toolkit import emissions_from_fuel_volume

e = emissions_from_fuel_volume(1000, "1A3b_gasolina_moderno")  # 1000 litres
print(e.co2e_kg)
```

Worked examples are in [`notebooks/`](notebooks/).

## Data and method / Datos y método

| File | Content | Source |
|---|---|---|
| `data/emission_factors.csv` | CO2, CH4 and N2O factors by IPCC category and fuel | IPCC 2006 Guidelines, Vol. 2 (table named per row) |
| `data/fuel_properties.csv` | Density, gross and net calorific values per fuel | Balance Nacional de Energía (BNE) and IPCC 2006, Vol. 2, Table 1.2 |
| `data/gwp_ar5.csv` | 100-year global warming potentials | IPCC AR5 |
| `data/conversions.csv` | Energy and mass unit conversions | – |
| `data/wood_density.csv` | Firewood density by species | Named per row |
| `data/grid_emission_factors.csv` | Electricity grid factors for Chile's SEN | To be documented |
| `data/forest_factors.csv` | Wood density, biomass expansion factor and root ratio by species | INGEI Chile; Gayoso et al. 2002 |
| `data/forest_growth.csv` | Annual biomass growth by plantation species and region, and by native forest type | INGEI 2024 |
| `data/waste_parameters.csv` | Landfill model parameters (DOC, k, MCF) | IPCC 2006 Vol. 5 and INGEI Chile |

- Net calorific values default to Chile's BNE figures (gross value x 0.95 for
  liquids and solids, x 0.90 for gases); pass `pci_source="ipcc"` to use the
  IPCC world defaults instead.
- Biogenic CO2 (wood, biogas, black liquor) is reported separately and left
  out of the CO2e total, as the IPCC guidelines require.

## National inventory vs corporate accounting

The toolkit follows national inventory logic (IPCC sectors, territorial
emissions). The same activity-data-times-factor equation underlies corporate
accounting under the GHG Protocol, where it is organised by Scope 1, 2 and 3
instead of by IPCC sector.

## Author / Autora

Agata Czerwińska. ESG and sustainability reporting professional.

## License

MIT
