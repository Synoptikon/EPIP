from dataclasses import dataclass


@dataclass(frozen=True)
class StressObservation:
    """
    Physical stress observation used by EPIP.

    All stress quantities use a consistent unit system.
    """

    shear_stress: float
    normal_stress: float
    pore_pressure: float = 0.0


@dataclass(frozen=True)
class CFSObservation:
    """
    Coulomb Failure Stress result associated with an observation.
    """

    cfs: float
    friction_coefficient: float
