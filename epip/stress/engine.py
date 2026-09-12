import numpy as np

from .cfs import (
    DEFAULT_FRICTION_COEFFICIENT,
    coulomb_failure_stress,
)


class CoulombStressEngine:
    """Vectorized Coulomb Failure Stress engine."""

    def __init__(
        self,
        friction_coefficient=DEFAULT_FRICTION_COEFFICIENT,
    ):
        if friction_coefficient < 0:
            raise ValueError("friction_coefficient must be non-negative")

        self.friction_coefficient = float(friction_coefficient)

    def calculate(
        self,
        shear_stress,
        normal_stress,
        pore_pressure=0.0,
    ):
        """Calculate Coulomb Failure Stress."""
        return coulomb_failure_stress(
            shear_stress=shear_stress,
            normal_stress=normal_stress,
            pore_pressure=pore_pressure,
            friction_coefficient=self.friction_coefficient,
        )

    def calculate_array(
        self,
        shear_stress,
        normal_stress,
        pore_pressure=0.0,
    ):
        """Calculate CFS for scalar or array inputs."""
        return np.asarray(
            self.calculate(
                shear_stress,
                normal_stress,
                pore_pressure,
            )
        )
