from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
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
                "Formato invalido em --category-rates. Use: 'Beauty=0.08,Fashion=0.12'."
            )
        category, value = item.split("=", 1)
        category_name = category.strip()
        if not category_name:
            raise ValueError("Categoria vazia em --category-rates.")
        rates[category_name] = float(value.strip())
    return rates


def _build_recovery_rates(
    categories: list[str],
    global_rate: float,
    category_overrides: dict[str, float],
) -> dict[str, float]:
    rates = {category: global_rate for category in categories}
    for category, rate in category_overrides.items():
        rates[category] = rate
    return rates


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa simulacao de recuperacao de leakage por categoria e salva artefatos."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DATA_DIR / "amazon_sales_clean.csv",
        help="Caminho do CSV processado de entrada.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=TABLES_DIR,
        help="Diretorio de saida dos artefatos.",
    )
    parser.add_argument(
        "--recovery-rate",
        type=float,
        default=0.05,
        help="Taxa de recuperacao global (0.0 a 1.0) aplicada as categorias sem override.",
    )
    parser.add_argument(
        "--category-rates",
        type=str,
        default="",
        help="Overrides por categoria no formato 'Beauty=0.08,Fashion=0.12'.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()

    if not args.input.exists():
        raise SystemExit(f"Arquivo de entrada nao encontrado: {args.input}")
    if args.recovery_rate < 0 or args.recovery_rate > 1:
        raise SystemExit("--recovery-rate deve estar entre 0.0 e 1.0.")

    frame = pd.read_csv(args.input, parse_dates=["order_date"])
    categories = sorted(frame["product_category"].dropna().astype(str).unique().tolist())
    overrides = _parse_category_rates(args.category_rates)
    recovery_rates = _build_recovery_rates(categories, args.recovery_rate, overrides)
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
        "input_dataset": str(args.input),
        "output_breakdown_csv": str(breakdown_path),
        "recovery_rate_default": float(args.recovery_rate),
        "category_overrides": overrides,
        "baseline_revenue": float(simulation["baseline_revenue"]),
        "gross_revenue": float(simulation["gross_revenue"]),
        "baseline_nrr": float(simulation["baseline_nrr"]),
        "simulated_revenue": float(simulation["simulated_revenue"]),
        "simulated_nrr": float(simulation["simulated_nrr"]),
        "total_uplift": float(simulation["total_uplift"]),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Scenario simulation generated successfully.")
    print(f"- Breakdown: {breakdown_path}")
    print(f"- Summary:   {summary_path}")


if __name__ == "__main__":
    main()

