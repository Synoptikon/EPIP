from datetime import datetime, timezone

from epip.stress.engine import CoulombStressEngine


def main() -> int:
    print("=== EPIP v3.3.0 LIVE SCIENTIFIC PIPELINE ===")

    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"UTC: {timestamp}")

    engine = CoulombStressEngine()

    cfs = engine.calculate(
        shear_stress=10.0,
        normal_stress=20.0,
        pore_pressure=2.0,
    )

    print("=== STRESS ===")
    print(f"CFS: {cfs}")

    print("=== PIPELINE STATUS ===")
    print("OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
