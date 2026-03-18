from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from amazon_sales_analysis import __version__
from amazon_sales_analysis.config import get_settings
from amazon_sales_analysis.pipelines.runtime import write_dataframe_artifact, write_json_artifact
from amazon_sales_analysis.scenario_simulator import simulate_leakage_recovery
from amazon_sales_analysis.transformations.data_preprocessing import read_sales_dataset


def parse_category_rates(raw_value: str) -> dict[str, float]:
    rates: dict[str, float] = {}
    if not raw_value.strip():
        return rates

    for part in raw_value.split(","):
        item = part.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError("Invalid format for --category-rates. Use 'Beauty=0.08,Fashion=0.12'.")
        category, value = item.split("=", 1)
        category_name = category.strip()
        if not category_name:
            raise ValueError("Empty category name in --category-rates.")
        rates[category_name] = float(value.strip())
    return rates


def build_recovery_rates(
    categories: list[str],
    global_rate: float,
    category_overrides: dict[str, float],
) -> dict[str, float]:
    rates = {category: global_rate for category in categories}
    rates.update(category_overrides)
    return rates


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Run leakage recovery simulation by category and persist the artifacts."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=settings.processed_data_dir / "amazon_sales_clean.csv",
        help="Path to the processed input CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.tables_dir,
        help="Output directory for the generated artifacts.",
    )
    parser.add_argument(
        "--recovery-rate",
        type=float,
        default=0.05,
        help="Global recovery rate (0.0 to 1.0) applied to categories without overrides.",
    )
    parser.add_argument(
        "--category-rates",
        type=str,
        default="",
        help="Overrides per category in the format 'Beauty=0.08,Fashion=0.12'.",
    )
    return parser


def run(*, input_path: Path, output_dir: Path, recovery_rate: float, category_rates: str) -> None:
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if recovery_rate < 0 or recovery_rate > 1:
        raise SystemExit("--recovery-rate must be between 0.0 and 1.0.")

    frame = read_sales_dataset(input_path)
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    categories = sorted(frame["product_category"].dropna().astype(str).unique().tolist())
    overrides = parse_category_rates(category_rates)
    recovery_rates = build_recovery_rates(categories, recovery_rate, overrides)
    simulation = cast(dict[str, Any], simulate_leakage_recovery(frame, recovery_rates))

    output_dir.mkdir(parents=True, exist_ok=True)
    breakdown_path = output_dir / "scenario_simulation_breakdown.csv"
    summary_path = output_dir / "scenario_simulation_summary.json"

    breakdown = cast(pd.DataFrame, simulation["category_breakdown"])
    write_dataframe_artifact(breakdown, breakdown_path)

    summary = {
        "pipeline_version": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "input_dataset": str(input_path),
        "output_breakdown_csv": str(breakdown_path),
        "recovery_rate_default": float(recovery_rate),
        "category_overrides": overrides,
        "baseline_revenue": float(cast(float, simulation["baseline_revenue"])),
        "gross_revenue": float(cast(float, simulation["gross_revenue"])),
        "baseline_nrr": float(cast(float, simulation["baseline_nrr"])),
        "simulated_revenue": float(cast(float, simulation["simulated_revenue"])),
        "simulated_nrr": float(cast(float, simulation["simulated_nrr"])),
        "total_uplift": float(cast(float, simulation["total_uplift"])),
    }
    write_json_artifact(summary, summary_path)

    print("Scenario simulation generated successfully.")
    print(f"- Breakdown: {breakdown_path}")
    print(f"- Summary:   {summary_path}")


def main() -> None:
    args = build_parser().parse_args()
    run(
        input_path=args.input,
        output_dir=args.output_dir,
        recovery_rate=args.recovery_rate,
        category_rates=args.category_rates,
    )
