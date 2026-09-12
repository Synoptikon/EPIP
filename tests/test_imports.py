def test_epip_import():
    import epip

    assert epip.__version__ == "3.3.0"


def test_epip_modules_import():
    import epip.governance
    import epip.ingest
    import epip.models
    import epip.prospective
    import epip.stress
    import epip.tectonics
