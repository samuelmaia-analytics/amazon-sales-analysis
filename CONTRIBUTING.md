# Contributing Guide

This repository follows production-minded engineering standards. Contributions are expected to improve reliability, correctness, maintainability, or operational clarity.

## Before You Start

Read:

- [README.md](README.md)
- [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md)

## Contribution Principles

- prioritize business and operational impact over cosmetic edits
- keep ingestion, transformation, validation, observability, and serving boundaries clear
- preserve deterministic and reprocessable pipeline behavior
- prefer explicit failures to silent fallback behavior
- update tests and docs in the same change set as code

## Local Setup

```bash
python -m pip install -e .[dev]
pre-commit install
cp .env.example .env
```

## Branch and PR Workflow

1. Create a focused branch from `main`.
2. Implement the smallest complete change that solves the target problem.
3. Run full validation locally.
4. Open a PR using the repository template.
5. Include risk, rollback, and evidence sections.

## Mandatory Validation

```bash
make quality
make test
make build-check
```

Equivalent:

```bash
black --check .
isort --check-only .
ruff check .
mypy src tests app alerts scripts
pytest -q
python -m build --sdist --wheel
```

## Testing Expectations

You must add or update tests when changing:

- data contracts, schema validation, or quality gates
- transformation logic or KPI calculations
- manifest/run-status/runtime behavior
- API, CLI, or Streamlit behavior
- warehouse and run-history behavior
- compatibility shims

## Documentation Expectations

Update docs when changing:

- execution flow
- config and env vars
- repository topology
- CLI/API behavior
- quality and reliability semantics

Minimum surfaces:

- [README.md](README.md)
- [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md)

## Structure Rules

- reusable logic belongs in `src/amazon_sales_analysis/`
- wrappers/entry points belong in `app/` and `scripts/`
- warehouse SQL belongs in `sql/`
- runtime artifacts belong in `data/` and `reports/`
- notebooks are exploratory, not source of truth

## Compatibility and Public Surface

Compatibility modules at package root are intentionally preserved.

Rules:

- prefer domain package imports in new code
- do not remove compatibility paths without explicit deprecation
- keep re-exports explicit and tested

## Review Criteria

Reviewers prioritize:

- correctness and edge-case behavior
- regression and rollback risk
- data quality impact
- operational observability
- documentation drift

## PR Acceptance Checklist

- change scope is explicit and bounded
- local validation passed
- tests cover modified behavior
- docs updated
- risk and rollback described
- no unrelated refactors mixed in

