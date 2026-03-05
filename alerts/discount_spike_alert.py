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
from amazon_sales_analysis.anomaly_detection import (
    detect_discount_spikes,
    export_discount_spike_alerts,
)
from amazon_sales_analysis.config import METRICS_DIR, PROCESSED_DATA_DIR


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automated discount spike alerts.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DATA_DIR / "amazon_sales_clean.csv",
        help="CSV processado de entrada.",
    )
    parser.add_argument(
        "--z-threshold",
        type=float,
        default=2.5,
        help="Threshold de z-score para disparo de alerta.",
    )
    parser.add_argument(
        "--min-observations",
        type=int,
        default=5,
        help="Minimo de observacoes por categoria.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=METRICS_DIR / "alerts_summary.json",
        help="Resumo JSON de execucao.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if not args.input.exists():
        raise SystemExit(f"Arquivo de entrada nao encontrado: {args.input}")
    if args.z_threshold <= 0:
        raise SystemExit("--z-threshold deve ser maior que 0.")
    if args.min_observations < 2:
        raise SystemExit("--min-observations deve ser maior ou igual a 2.")

    frame = pd.read_csv(args.input, parse_dates=["order_date"])
    alerts = detect_discount_spikes(
        frame,
        z_threshold=args.z_threshold,
        min_observations=args.min_observations,
    )
    alerts_csv_path = export_discount_spike_alerts(alerts)

    summary = {
        "pipeline_version": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "ok" if alerts.empty else "attention",
        "alerts_count": int(len(alerts)),
        "alerts_output_csv": str(alerts_csv_path),
        "parameters": {
            "z_threshold": float(args.z_threshold),
            "min_observations": int(args.min_observations),
        },
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Alerts gerados: {len(alerts)}")
    print(f"CSV: {alerts_csv_path}")
    print(f"Resumo: {args.summary_output}")


if __name__ == "__main__":
    main()
