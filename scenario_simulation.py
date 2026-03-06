from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from amazon_sales_analysis import __version__
from amazon_sales_analysis.config import PROCESSED_DATA_DIR, TABLES_DIR
from amazon_sales_analysis.scenario_simulator import simulate_leakage_recovery


def _parse_category_rates(raw_value: str) -> dict[str, float]:
    rates: dict[str, float] = {}
    if not raw_value.strip():
        return rates
    for part in raw_value.split(","):
        item = part.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(
                "Formato invalido em --category-rates. Use 'Beauty=0.08,Fashion=0.12'."
            )
        category, value = item.split("=", 1)
        rates[category.strip()] = float(value.strip())
    return rates


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scenario simulator de leakage recovery.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DATA_DIR / "amazon_sales_clean.csv",
        help="CSV processado de entrada.",
    )
    parser.add_argument(
        "--recovery-rate",
        type=float,
        default=0.05,
        help="Taxa padrao de recuperacao (0.0 a 1.0).",
    )
    parser.add_argument(
        "--category-rates",
        type=str,
        default="",
        help="Overrides por categoria, ex: 'Beauty=0.08,Fashion=0.12'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=TABLES_DIR,
        help="Diretorio de saida dos artefatos.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if not args.input.exists():
        raise SystemExit(f"Arquivo de entrada nao encontrado: {args.input}")
    if not 0 <= args.recovery_rate <= 1:
        raise SystemExit("--recovery-rate deve estar entre 0.0 e 1.0")

    frame = pd.read_csv(args.input, parse_dates=["order_date"])
    categories = sorted(frame["product_category"].dropna().astype(str).unique())
    overrides = _parse_category_rates(args.category_rates)
    recovery_rates = {category: args.recovery_rate for category in categories}
    recovery_rates.update(overrides)

    simulation = simulate_leakage_recovery(frame, recovery_rates)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    breakdown_path = args.output_dir / "scenario_simulation_breakdown.csv"
    summary_path = args.output_dir / "scenario_simulation_summary.json"

    breakdown = simulation["category_breakdown"]
    assert isinstance(breakdown, pd.DataFrame)
    breakdown.to_csv(breakdown_path, index=False)

    summary = {
        "pipeline_version": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "baseline_revenue": float(simulation["baseline_revenue"]),
        "gross_revenue": float(simulation["gross_revenue"]),
        "simulated_revenue": float(simulation["simulated_revenue"]),
        "baseline_nrr": float(simulation["baseline_nrr"]),
        "simulated_nrr": float(simulation["simulated_nrr"]),
        "total_uplift": float(simulation["total_uplift"]),
        "category_overrides": overrides,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Scenario simulation concluida. Breakdown: {breakdown_path}")
    print(f"Resumo: {summary_path}")


if __name__ == "__main__":
    main()
