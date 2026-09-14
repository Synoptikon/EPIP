"""Run the EPIP end-to-end baseline pipeline against USGS FDSN."""

from __future__ import annotations

import argparse
import json

from epip.pipeline import ScientificPipelineConfig, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="training window start, ISO-8601")
    parser.add_argument("--cutoff", required=True, help="forecast generation cutoff, ISO-8601")
    parser.add_argument("--end", required=True, help="prospective evaluation window end, ISO-8601")
    parser.add_argument("--region", required=True)
    parser.add_argument("--min-magnitude", type=float, default=4.0)
    parser.add_argument("--acquisition-min-magnitude", type=float, default=None)
    parser.add_argument("--minlatitude", type=float)
    parser.add_argument("--maxlatitude", type=float)
    parser.add_argument("--minlongitude", type=float)
    parser.add_argument("--maxlongitude", type=float)
    parser.add_argument("--horizon-days", type=float, default=7.0)
    parser.add_argument("--limit", type=int, default=20000)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    config = ScientificPipelineConfig(
        training_start=args.start,
        cutoff=args.cutoff,
        evaluation_end=args.end,
        region=args.region,
        minimum_magnitude=args.min_magnitude,
        forecast_horizon_days=args.horizon_days,
        minlatitude=args.minlatitude,
        maxlatitude=args.maxlatitude,
        minlongitude=args.minlongitude,
        maxlongitude=args.maxlongitude,
        acquisition_min_magnitude=args.acquisition_min_magnitude,
        fetch_limit=args.limit,
        timeout=args.timeout,
    )

    result = run_pipeline(config)
    payload = {
        "generated_at": result.generated_at.isoformat(),
        "training_events": len(result.training_events),
        "evaluation_events": len(result.evaluation_events),
        "mc": result.completeness.mc,
        "mc_method": result.completeness.method,
        "rate_per_year": result.rate.rate_per_year,
        "forecast_probability": result.forecast.probability,
        "forecast_minimum_magnitude": result.forecast.minimum_magnitude,
        "forecast_generated_at": result.forecast.generated_at.isoformat(),
        "forecast_expires_at": result.forecast.expires_at.isoformat(),
        "observed": result.outcome.occurred,
        "observed_event_ids": result.outcome.observed_event_ids,
        "brier_score": result.outcome.brier_score,
        "model_version": result.forecast.model_version,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
