PYTHON ?= python

.PHONY: setup-dev quality test pipeline alerts scenario warehouse

setup-dev:
	$(PYTHON) -m pip install -e .[dev]

quality:
	black --check .
	isort --check-only .
	ruff check .
	mypy src scripts app alerts

test:
	pytest

pipeline:
	$(PYTHON) -m amazon_sales_analysis.cli.pipeline

alerts:
	$(PYTHON) -m amazon_sales_analysis.cli.alerts

scenario:
	$(PYTHON) -m amazon_sales_analysis.cli.scenario

warehouse:
	$(PYTHON) -m amazon_sales_analysis.cli.warehouse --export-category-revenue
