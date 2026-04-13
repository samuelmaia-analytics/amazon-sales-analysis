# Amazon Sales Analytics Platform (International Guide)

This guide provides a concise operational and architectural overview for international readers.

Canonical standards:

- Main overview: [../README.md](../README.md)
- Contribution workflow: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- Repository topology: [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)

## Scope

The repository demonstrates a production-oriented analytics workflow:

- reproducible batch execution
- contract/schema/quality validation
- KPI regression controls across runs
- run-scoped operational evidence
- API, CLI, and dashboard serving surfaces

## Runtime Flow

```mermaid
flowchart LR
    A[Raw Ingestion] --> B[Contract + Schema Validation]
    B --> C[Bronze Snapshot]
    C --> D[Cleaning + Quality Gates]
    D --> E[Silver Snapshot]
    E --> F[Gold + Warehouse]
    F --> G[Metrics + Regression]
    G --> H[Manifest + Run Status]
    H --> I[Latest Snapshots]
```

## Key Commands

```bash
PYTHONPATH=src python -m amazon_sales_analysis.cli.pipeline --retention-runs 60
PYTHONPATH=src python -m amazon_sales_analysis.cli.warehouse --show-operational-summary
uvicorn app.api:app --reload
streamlit run app/streamlit_app.py
```

## Reliability Semantics

- immutable artifacts in `reports/runs/<run_id>/`
- stable `latest` snapshots for consumption
- explicit run retention control
- operational status persisted even on failed runs
- deterministic and auditable execution metadata

## Quality Gates

```bash
make quality
make test
make build-check
```

Includes:

- `black --check .`
- `isort --check-only .`
- `ruff check .`
- `mypy src tests app alerts scripts`
- `pytest -q`
- `python -m build --sdist --wheel`

## Governance

- synthetic test fixtures by default
- environment-driven configuration
- explicit run lineage through status and manifests
- local-first architecture with clear trade-offs

## Language Switch

- International: [../README.md](../README.md)
- PT-BR: [README.pt-BR.md](README.pt-BR.md)
- PT-PT: [README.pt-PT.md](README.pt-PT.md)

