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
    parser = argparse.ArgumentParser(
        description="Gera alertas operacionais de discount spikes com saida padronizada."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROCESSED_DATA_DIR / "amazon_sales_clean.csv",
        help="Caminho do CSV processado de entrada.",
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
        help="Minimo de observacoes por categoria para calculo do baseline.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=METRICS_DIR / "alerts_summary.json",
        help="Arquivo JSON de resumo operacional.",
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

    severity_counts = (
        alerts["severity"].value_counts().sort_index().to_dict() if not alerts.empty else {}
    )
    status = "ok" if alerts.empty else "attention"

    summary = {
        "pipeline_version": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "input_dataset": str(args.input),
        "alerts_output_csv": str(alerts_csv_path),
        "parameters": {
            "z_threshold": float(args.z_threshold),
            "min_observations": int(args.min_observations),
        },
        "alerts_count": int(len(alerts)),
        "severity_counts": {str(key): int(value) for key, value in severity_counts.items()},
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Operational alerts generated successfully.")
    print(f"- Alerts CSV:  {alerts_csv_path}")
    print(f"- Summary JSON:{args.summary_output}")
    print(f"- Alerts count:{len(alerts)}")


if __name__ == "__main__":
    main()
