"""Finite-fault geometry contracts for stress-transfer calculations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FiniteFaultPatch:
    """Minimal geometric/mechanical description of a rectangular fault patch.

    Coordinates are not embedded here; this contract deliberately keeps
    geometry separate from any geographic projection or elastic solver.
    Angles are degrees, lengths are kilometres, and slip is metres.
    """

    strike: float
    dip: float
    rake: float
    length_km: float
    width_km: float
    slip_m: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.strike <= 360.0:
            raise ValueError("strike must be between 0 and 360 degrees")
        if not 0.0 < self.dip <= 90.0:
            raise ValueError("dip must be greater than 0 and <= 90 degrees")
        if not -180.0 <= self.rake <= 180.0:
            raise ValueError("rake must be between -180 and 180 degrees")
        if self.length_km <= 0.0:
            raise ValueError("length_km must be > 0")
        if self.width_km <= 0.0:
            raise ValueError("width_km must be > 0")
        if self.slip_m < 0.0:
            raise ValueError("slip_m must be >= 0")

    @property
    def area_km2(self) -> float:
        """Surface area of the rectangular patch in km²."""
        return self.length_km * self.width_km
