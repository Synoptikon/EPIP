import pytest

from epip.stress.receiver import ReceiverFault


def test_receiver_fault_creation():
    receiver = ReceiverFault(
        strike=90.0,
        dip=45.0,
        rake=0.0,
    )

    assert receiver.strike == 90.0
    assert receiver.dip == 45.0
    assert receiver.rake == 0.0
    assert receiver.friction_coefficient == 0.4


def test_invalid_strike():
    with pytest.raises(ValueError):
        ReceiverFault(strike=361.0, dip=45.0, rake=0.0)


def test_invalid_dip():
    with pytest.raises(ValueError):
        ReceiverFault(strike=90.0, dip=0.0, rake=0.0)


def test_invalid_rake():
    with pytest.raises(ValueError):
        ReceiverFault(strike=90.0, dip=45.0, rake=181.0)


def test_invalid_friction():
    with pytest.raises(ValueError):
        ReceiverFault(
            strike=90.0,
            dip=45.0,
            rake=0.0,
            friction_coefficient=-0.1,
        )
