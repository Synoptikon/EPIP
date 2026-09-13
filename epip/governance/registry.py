"""Auditable registry for EPIP scientific definitions and model metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EntryKind = Literal["OBS", "DEF", "HYP", "RULE", "MODEL", "TEST", "RESULT", "INTERP"]


@dataclass(frozen=True)
class RegistryEntry:
    """Traceable epistemic entry.

    The registry stores metadata and provenance references; it does not
    promote hypotheses into observations or results.
    """

    entry_id: str
    kind: EntryKind
    name: str
    description: str
    source: str
    version: str

    def __post_init__(self) -> None:
        for field_name in ("entry_id", "name", "description", "source", "version"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")


class Registry:
    """Small deterministic in-memory registry with collision protection."""

    def __init__(self) -> None:
        self._entries: dict[str, RegistryEntry] = {}

    def register(self, entry: RegistryEntry) -> None:
        """Register an entry and reject ID collisions."""
        if entry.entry_id in self._entries:
            raise ValueError(f"entry_id already registered: {entry.entry_id}")
        self._entries[entry.entry_id] = entry

    def get(self, entry_id: str) -> RegistryEntry:
        """Return an entry or raise ``KeyError`` when absent."""
        return self._entries[entry_id]

    def entries(self) -> tuple[RegistryEntry, ...]:
        """Return entries in deterministic registration order."""
        return tuple(self._entries.values())

    def by_kind(self, kind: EntryKind) -> tuple[RegistryEntry, ...]:
        """Return entries filtered by epistemic kind."""
        return tuple(entry for entry in self._entries.values() if entry.kind == kind)
