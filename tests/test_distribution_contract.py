from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

from amazon_sales_analysis import (
    contracts,
    data_ingestion,
    metrics,
    quality,
    run_history,
    validation,
)
from amazon_sales_analysis.cli import alerts, pipeline, scenario, warehouse


def test_pyproject_console_scripts_reference_existing_callables() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]

    for target in scripts.values():
        module_name, callable_name = target.split(":")
        module = importlib.import_module(module_name)
        assert hasattr(module, callable_name)
        assert callable(getattr(module, callable_name))


def test_compatibility_shims_expose_expected_symbols() -> None:
    assert hasattr(contracts, "enforce_raw_contract")
    assert hasattr(data_ingestion, "download_amazon_sales_dataset")
    assert hasattr(metrics, "collect_product_metrics")
    assert hasattr(quality, "enforce_clean_quality_gates")
    assert hasattr(run_history, "compare_latest_runs")
    assert hasattr(validation, "sales_schema")


def test_cli_modules_expose_build_parser_and_main() -> None:
    for module in [alerts, pipeline, scenario, warehouse]:
        assert hasattr(module, "build_parser")
        assert hasattr(module, "main")
