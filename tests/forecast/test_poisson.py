from datetime import datetime, timezone
from math import isclose

import pytest

from epip.forecast import PoissonForecastModel


def test_zero_rate_has_zero_probability():
    model = PoissonForecastModel(rate_per_year=0.0)
    assert model.probability(30.0) == 0.0


def test_poisson_probability_is_bounded_and_monotonic():
    model = PoissonForecastModel(rate_per_year=12.0)
    short = model.probability(7.0)
    long = model.probability(30.0)

    assert 0.0 <= short <= 1.0
    assert 0.0 <= long <= 1.0
    assert long > short


def test_forecast_record_preserves_model_and_cutoff():
    generated = datetime(2026, 9, 13, tzinfo=timezone.utc)
    model = PoissonForecastModel(rate_per_year=365.25)

    forecast = model.forecast(
        generated_at=generated,
        region="TEST",
        horizon_days=1.0,
        minimum_magnitude=4.0,
    )

    assert forecast.generated_at == generated
    assert forecast.model_version == "poisson-baseline-1"
    assert isclose(forecast.probability, 1.0 - 2.718281828459045 ** -1.0)


def test_negative_rate_is_rejected():
    with pytest.raises(ValueError, match="rate_per_year"):
        PoissonForecastModel(rate_per_year=-1.0)
