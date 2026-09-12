from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiverFault:
    """
    Geometric and mechanical representation of a receiver fault.

    Angles are expressed in degrees.
    """

    strike: float
    dip: float
    rake: float
    friction_coefficient: float = 0.4

    def __post_init__(self):
        if not 0.0 <= self.strike <= 360.0:
            raise ValueError("strike must be between 0 and 360 degrees")

        if not 0.0 < self.dip <= 90.0:
            raise ValueError("dip must be greater than 0 and <= 90 degrees")

        if not -180.0 <= self.rake <= 180.0:
            raise ValueError("rake must be between -180 and 180 degrees")

        if self.friction_coefficient < 0.0:
            raise ValueError("friction_coefficient must be non-negative")
