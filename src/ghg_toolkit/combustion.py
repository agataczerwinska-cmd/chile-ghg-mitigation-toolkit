"""Core Tier 1 combustion equation shared by every energy sector.

    emissions_gas [kg] = energy [TJ] x emission factor_gas [kg/TJ]

CO2e uses the IPCC AR5 100-year GWPs, the ones Chile's national inventory
(INGEI) reports with under the Paris Agreement.
"""

from dataclasses import dataclass

from .factors import get_factor, load_gwp

_gwp = load_gwp()["gwp"]
GWP_AR5 = {"co2": int(_gwp["CO2"]), "ch4": int(_gwp["CH4"]), "n2o": int(_gwp["N2O"])}


@dataclass(frozen=True)
class Emissions:
    """Emissions of one activity, in kg of each gas.

    Biogenic CO2 (wood, biogas, black liquor) is kept apart and is not
    counted in co2e_kg, following IPCC reporting rules.
    """

    co2_kg: float
    ch4_kg: float
    n2o_kg: float
    biogenic_co2_kg: float = 0.0

    @property
    def co2e_kg(self) -> float:
        return (
            self.co2_kg * GWP_AR5["co2"]
            + self.ch4_kg * GWP_AR5["ch4"]
            + self.n2o_kg * GWP_AR5["n2o"]
        )

    @property
    def co2e_t(self) -> float:
        return self.co2e_kg / 1000

    def __add__(self, other: "Emissions") -> "Emissions":
        return Emissions(
            self.co2_kg + other.co2_kg,
            self.ch4_kg + other.ch4_kg,
            self.n2o_kg + other.n2o_kg,
            self.biogenic_co2_kg + other.biogenic_co2_kg,
        )

    def as_dict(self) -> dict:
        return {
            "co2_kg": self.co2_kg,
            "ch4_kg": self.ch4_kg,
            "n2o_kg": self.n2o_kg,
            "biogenic_co2_kg": self.biogenic_co2_kg,
            "co2e_kg": self.co2e_kg,
        }


def combustion_emissions(energy_tj: float, factor_id: str) -> Emissions:
    """Emissions from burning `energy_tj` of fuel, using the factor row `factor_id`."""
    if energy_tj < 0:
        raise ValueError("energy_tj must be zero or positive")
    ef = get_factor(factor_id)
    co2 = energy_tj * ef["ef_co2_kg_tj"]
    biogenic = bool(ef["biogenic_co2"])
    return Emissions(
        co2_kg=0.0 if biogenic else co2,
        ch4_kg=energy_tj * ef["ef_ch4_kg_tj"],
        n2o_kg=energy_tj * ef["ef_n2o_kg_tj"],
        biogenic_co2_kg=co2 if biogenic else 0.0,
    )
