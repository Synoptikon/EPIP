import pytest

from epip.governance import Registry, RegistryEntry


def entry(entry_id="HYP-001", kind="HYP"):
    return RegistryEntry(
        entry_id=entry_id,
        kind=kind,
        name="test entry",
        description="test description",
        source="test",
        version="1",
    )


def test_registry_preserves_entries_and_kind_filter():
    registry = Registry()
    registry.register(entry())
    registry.register(entry("OBS-001", "OBS"))

    assert registry.get("HYP-001").kind == "HYP"
    assert [item.entry_id for item in registry.by_kind("OBS")] == ["OBS-001"]


def test_registry_rejects_id_collision():
    registry = Registry()
    registry.register(entry())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(entry())
