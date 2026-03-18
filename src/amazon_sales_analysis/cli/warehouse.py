from __future__ import annotations

import argparse

from amazon_sales_analysis.config import get_settings
from amazon_sales_analysis.logging_config import configure_logging
from amazon_sales_analysis.run_history import compare_latest_runs, summarize_run_history
from amazon_sales_analysis.warehouse_service import (
    export_category_revenue_query,
    warehouse_query_metadata,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute warehouse-facing analytical queries against the gold mart."
    )
    parser.add_argument(
        "--export-category-revenue",
        action="store_true",
        help="Export the category revenue query result to reports/tables.",
    )
    parser.add_argument(
        "--show-run-history",
        action="store_true",
        help="Print the latest pipeline runs tracked by execution manifests.",
    )
    parser.add_argument(
        "--compare-latest-runs",
        action="store_true",
        help="Print KPI deltas between the latest run and the previous one.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configure_logging()
    settings = get_settings()
    metadata = warehouse_query_metadata(settings)

    if args.export_category_revenue:
        output = export_category_revenue_query(settings=settings)
        print(f"Category revenue exported to: {output}")
    elif args.show_run_history:
        print("Recent pipeline runs:")
        for run in summarize_run_history(settings=settings):
            print(
                f"- {run['run_id']} | revenue={run['total_revenue']} | "
                f"clean_rows={run['clean_rows']} | alerts={run['alerts']}"
            )
    elif args.compare_latest_runs:
        comparison = compare_latest_runs(settings=settings)
        print(
            f"Comparing {comparison['latest_run_id']} vs {comparison['previous_run_id']} "
            f"(severity={comparison['overall_severity']}):"
        )
        for metric, values in comparison["kpi_deltas"].items():
            print(
                f"- {metric}: latest={values['latest']} previous={values['previous']} "
                f"delta={values['delta']} ratio={values['delta_ratio']:.4f} "
                f"severity={values['severity']}"
            )
    else:
        print("Warehouse metadata:")
        for key, value in metadata.items():
            print(f"- {key}: {value}")
