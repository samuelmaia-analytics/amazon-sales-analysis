# Contributing

This repository is maintained as a compact, production-oriented analytics platform. Contributions should improve correctness, reliability, observability, maintainability, or documentation quality without adding ornamental architecture.

## Read First

- Main overview: [README.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/README.md)
- Structure guide: [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)
- PT-BR overview: [docs/README.pt-BR.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-BR.md)
- PT-PT overview: [docs/README.pt-PT.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-PT.md)

## Contribution Principles

- Favor changes with operational value over cosmetic refactors.
- Keep ingestion, transformation, validation, observability, and serving responsibilities distinct.
- Prefer explicit failure modes over silent fallbacks.
- Keep API, CLI, and dashboard layers thin and backed by reusable package code.
- Update tests and docs whenever public behavior or repository structure changes.

## Local Setup

```bash
python -m pip install -e .[dev]
pre-commit install
cp .env.example .env
```

## Development Workflow

1. Branch from `main` with a focused scope.
2. Change code, tests, and documentation together.
3. Validate locally before opening a PR.
4. Describe technical impact and risk explicitly in the PR.

## Placement Rules

- Put reusable application logic under `src/amazon_sales_analysis/`.
- Put API and Streamlit entry points under `app/`.
- Put wrapper scripts under `scripts/`, not business logic.
- Put warehouse SQL under `sql/`.
- Keep exploratory work in `notebooks/`.
- Treat `data/` and `reports/` as generated runtime locations.

## Compatibility Policy

The package root still contains compatibility modules such as `data_ingestion.py`, `metrics.py`, and `warehouse.py`.

- Use domain packages for new development.
- Touch compatibility modules only when preserving or formally evolving public import paths.
- Keep re-exports explicit.
- If a compatibility path needs deprecation, document it in the PR and in the README before removal.

## Required Validation

Run all of the following before opening a PR:

```bash
make quality
make test
make build-check
```

Equivalent commands:

```bash
black --check .
isort --check-only .
ruff check .
mypy src tests app alerts scripts
pytest -q
python -m build --sdist --wheel
```

## Testing Expectations

Add or update tests when you change:

- schema or contract rules
- transformations or KPI calculations
- runtime artifact generation
- API or CLI behavior
- warehouse logic
- operational summaries or run history
- compatibility shims

Regression fixes should include a reproducing test whenever practical.

## Documentation Expectations

Update documentation when you change:

- repository structure
- CLI or API surfaces
- environment variables
- execution flow or operational behavior
- compatibility policy
- user-facing dashboard behavior

Minimum documentation surfaces to review:

- [README.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/README.md)
- [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)
- [docs/README.en.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.en.md)
- [docs/README.pt-BR.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-BR.md)
- [docs/README.pt-PT.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-PT.md)

## Pull Request Standard

A PR should answer, concretely:

- what changed
- why it changed
- what technical risks exist
- how the change was validated
- what documentation was updated
- what follow-up work remains

Avoid vague statements such as "production-ready" or "improved architecture" without evidence.

## Review Standard

Reviews should focus on:

- correctness
- regression risk
- data quality impact
- operational impact
- maintainability
- documentation drift

## What Not To Do

- Do not commit local runtime artifacts unless they are intentionally versioned examples.
- Do not move logic into notebooks or scripts for convenience.
- Do not add abstractions without a concrete runtime or maintenance benefit.
- Do not hide uncertain behavior behind broad exception handling.
- Do not bypass validation because a change looks small.

## When To Open An Issue First

Prefer an issue or draft PR before implementation when:

- the change affects multiple execution surfaces
- a contract or public API changes
- the package layout is being reorganized
- the proposal introduces new infrastructure or dependencies
