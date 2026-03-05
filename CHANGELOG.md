# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

## [1.0.0] - 2026-03-05
- Added root-level scenario simulator script (`scenario_simulation.py`) for leakage recovery analysis.
- Added automated alerts script at `alerts/discount_spike_alert.py`.
- Added versioned API endpoint `GET /api/v1/revenue_metrics`.
- Added `pandera` schema validation in preprocessing pipeline.
- Promoted project release to `v1.0.0`.

## [0.2.0] - 2026-03-05
- Added executable scenario simulator script (`scripts/run_scenario_simulator.py`) with report exports to `reports/tables/`.
- Added operational alerts runner (`scripts/run_alerts.py`) with standardized summary output in `reports/metrics/alerts_summary.json`.
- Added `Makefile` targets for `pipeline`, `alerts` and `scenario`.
- Added `pipeline_version` field to product metrics output to lock artifact provenance by release version.

## [0.1.0] - 2026-03-04
- Initial public version of the Amazon Sales Analytics project.
- Added data preprocessing pipeline, executive tables and Streamlit dashboard.
