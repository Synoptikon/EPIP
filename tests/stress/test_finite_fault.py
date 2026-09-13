import pytest

from epip.stress import FiniteFaultPatch


def test_patch_area():
    patch = FiniteFaultPatch(
        strike=90.0,
        dip=30.0,
        rake=0.0,
        length_km=10.0,
        width_km=5.0,
        slip_m=1.0,
    )
    assert patch.area_km2 == 50.0


def test_patch_rejects_non_positive_dimensions():
    with pytest.raises(ValueError, match="length_km"):
        FiniteFaultPatch(
            strike=90.0,
            dip=30.0,
            rake=0.0,
            length_km=0.0,
            width_km=5.0,
        )
