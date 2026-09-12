"""Quality control and deterministic deduplication for the EPIP catalog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .events import CatalogEvent


@dataclass(frozen=True)
class CatalogQC:
    accepted: int
    rejected: int
    duplicates: int


def validate_event(event: CatalogEvent) -> bool:
    """Return True when an event satisfies basic physical constraints."""

    if not event.event_id:
        return False

    if event.magnitude is not None and not -2.0 <= event.magnitude <= 10.0:
        return False

    if event.depth_km is not None and event.depth_km < 0:
        return False

    return True


def quality_control(
    events: Iterable[CatalogEvent],
) -> tuple[list[CatalogEvent], CatalogQC]:
    """Validate events and remove duplicate event IDs deterministically."""

    accepted: list[CatalogEvent] = []
    seen: set[str] = set()
    rejected = 0
    duplicates = 0

    for event in events:
        if event.event_id in seen:
            duplicates += 1
            continue

        if not validate_event(event):
            rejected += 1
            continue

        seen.add(event.event_id)
        accepted.append(event)

    accepted.sort(key=lambda event: event.time)

    return accepted, CatalogQC(
        accepted=len(accepted),
        rejected=rejected,
        duplicates=duplicates,
    )
