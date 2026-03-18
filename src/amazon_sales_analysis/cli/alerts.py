from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from amazon_sales_analysis import __version__
from amazon_sales_analysis.anomaly_detection import (
    detect_discount_spikes,
    export_discount_spike_alerts,
)
from amazon_sales_analysis.config import get_settings
from amazon_sales_analysis.pipelines.runtime import write_json_artifact
from amazon_sales_analysis.transformations.data_preprocessing import read_sales_dataset


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Generate operational discount spike alerts with standardized outputs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=settings.processed_data_dir / "amazon_sales_clean.csv",
        help="Path to the processed CSV input.",
    )
    parser.add_argument(
        "--z-threshold",
        type=float,
        default=2.5,
        help="Z-score threshold used to trigger an alert.",
    )
    parser.add_argument(
        "--min-observations",
        type=int,
        default=5,
        help="Minimum number of observations per category to compute a baseline.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=settings.metrics_dir / "alerts_summary.json",
        help="Path to the JSON operational summary.",
    )
    return parser


def run(
    *, input_path: Path, z_threshold: float, min_observations: int, summary_output: Path
) -> None:
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if z_threshold <= 0:
        raise SystemExit("--z-threshold must be greater than 0.")
    if min_observations < 2:
        raise SystemExit("--min-observations must be greater than or equal to 2.")

    frame = read_sales_dataset(input_path)
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    alerts = detect_discount_spikes(
        frame,
        z_threshold=z_threshold,
        min_observations=min_observations,
    )
    alerts_csv_path = export_discount_spike_alerts(alerts)

    severity_counts = (
        alerts["severity"].value_counts().sort_index().to_dict() if not alerts.empty else {}
    )
    status = "ok" if alerts.empty else "attention"

    summary = {
        "pipeline_version": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "input_dataset": str(input_path),
        "alerts_output_csv": str(alerts_csv_path),
        "parameters": {
            "z_threshold": float(z_threshold),
            "min_observations": int(min_observations),
        },
        "alerts_count": int(len(alerts)),
        "severity_counts": {str(key): int(value) for key, value in severity_counts.items()},
    }
    write_json_artifact(summary, summary_output)

    print("Operational alerts generated successfully.")
    print(f"- Alerts CSV:   {alerts_csv_path}")
    print(f"- Summary JSON: {summary_output}")
    print(f"- Alerts count: {len(alerts)}")


def main() -> None:
    args = build_parser().parse_args()
    run(
        input_path=args.input,
        z_threshold=args.z_threshold,
        min_observations=args.min_observations,
        summary_output=args.summary_output,
    )
