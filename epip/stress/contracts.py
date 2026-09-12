from dataclasses import dataclass


@dataclass(frozen=True)
class StressInput:
    shear_stress: float
    normal_stress: float
    pore_pressure: float = 0.0
    friction_coefficient: float = 0.4


@dataclass(frozen=True)
class StressResult:
    cfs: float
    shear_stress: float
    normal_stress: float
    pore_pressure: float
    friction_coefficient: float
