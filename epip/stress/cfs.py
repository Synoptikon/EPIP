import numpy as np


DEFAULT_FRICTION_COEFFICIENT = 0.4


def coulomb_failure_stress(
    shear_stress,
    normal_stress,
    pore_pressure=0.0,
    friction_coefficient=DEFAULT_FRICTION_COEFFICIENT,
):
    """
    Calculate Coulomb Failure Stress (CFS).

    ΔCFS = Δτ + μ(Δσn + Δp)

    Parameters
    ----------
    shear_stress : float or array-like
        Shear stress change.
    normal_stress : float or array-like
        Normal stress change.
    pore_pressure : float or array-like
        Pore-pressure change.
    friction_coefficient : float
        Effective friction coefficient.

    Returns
    -------
    float or numpy.ndarray
        Coulomb Failure Stress change.
    """
    if friction_coefficient < 0:
        raise ValueError("friction_coefficient must be non-negative")

    shear = np.asarray(shear_stress, dtype=float)
    normal = np.asarray(normal_stress, dtype=float)
    pressure = np.asarray(pore_pressure, dtype=float)

    return shear + friction_coefficient * (normal + pressure)
