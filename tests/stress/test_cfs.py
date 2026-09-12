import numpy as np
import pytest

from epip.stress.cfs import coulomb_failure_stress
from epip.stress.engine import CoulombStressEngine


def test_cfs_scalar():
    result = coulomb_failure_stress(
        shear_stress=1.0,
        normal_stress=2.0,
        pore_pressure=0.5,
        friction_coefficient=0.4,
    )

    assert result == pytest.approx(2.0)


def test_cfs_vectorized():
    result = coulomb_failure_stress(
        shear_stress=np.array([1.0, 2.0, 3.0]),
        normal_stress=np.array([2.0, 1.0, 0.0]),
        pore_pressure=np.array([0.5, 0.0, 1.0]),
        friction_coefficient=0.4,
    )

    expected = np.array([2.0, 2.4, 3.4])

    np.testing.assert_allclose(result, expected)


def test_engine_default_friction():
    engine = CoulombStressEngine()

    assert engine.friction_coefficient == pytest.approx(0.4)


def test_engine_calculation():
    engine = CoulombStressEngine()

    result = engine.calculate(
        shear_stress=1.0,
        normal_stress=2.0,
        pore_pressure=0.5,
    )

    assert result == pytest.approx(2.0)


def test_negative_friction_rejected():
    with pytest.raises(ValueError):
        CoulombStressEngine(friction_coefficient=-0.1)
