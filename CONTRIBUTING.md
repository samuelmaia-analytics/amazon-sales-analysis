# Contributing

This repository is structured like a small production analytics platform. Contributions should improve reliability, clarity, testability, or analytical usefulness without introducing unnecessary complexity.

## Languages

- International: [README.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/README.md)
- PT-BR: [docs/README.pt-BR.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-BR.md)
- PT-PT: [docs/README.pt-PT.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-PT.md)

## Principles

- Prefer operationally useful changes over cosmetic refactors
- Preserve clear separation between ingestion, transformation, serving, and documentation
- Keep business logic in reusable modules under `src/amazon_sales_analysis/`
- Add or update tests when behavior changes
- Document non-obvious trade-offs in code, PRs, or docs

## Development Workflow

### 1. Environment

```bash
python -m pip install -e .[dev]
pre-commit install
```

### 2. Branching

- Branch from `main`
- Use short, descriptive branch names
- Keep PRs scoped to a single technical objective when possible

### 3. Implementation

- Update code, tests, and docs together
- Avoid hardcoded paths, silent fallbacks, and hidden side effects
- Keep CLI and API layers thin
- Prefer explicit validation errors over implicit failure modes

## Required Validation

Run before opening a PR:

```bash
make quality
make test
```

Equivalent commands:

```bash
black --check .
isort --check-only .
ruff check .
mypy src scripts app alerts
pytest
```

## Testing Expectations

Add or update tests when you change:

- data contracts or schema expectations
- transformations or KPI logic
- API contracts
- CLI behavior
- runtime orchestration or artifact generation
- warehouse query behavior

For bug fixes, add a regression test whenever practical.

## Documentation Expectations

Update documentation when you change:

- repository structure
- environment variables
- CLI or API surfaces
- operational behavior
- architecture or processing flow

Minimum docs to consider:

- [README.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/README.md)
- [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)
- [docs/README.en.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.en.md)
- [docs/README.pt-BR.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-BR.md)
- [docs/README.pt-PT.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-PT.md)

## Pull Request Standard

A good PR should make it easy to answer:

- what changed
- why it changed
- what risks were introduced
- how it was validated
- what follow-up work remains, if any

Use the PR template and keep evidence concrete.

## Review Standard

Reviews should prioritize:

- correctness
- regression risk
- data quality impact
- operational impact
- maintainability
- documentation drift

## What Not to Do

- Do not commit generated local artifacts unnecessarily
- Do not introduce architecture layers without operational value
- Do not bypass tests for behavior changes
- Do not hide uncertainty behind broad claims of "production-ready"

## Questions and Proposals

For larger changes, prefer opening an issue or draft PR before implementation when:

- the change affects multiple surfaces
- contracts or public behavior will change
- architectural direction is not obvious
