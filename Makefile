PYTHON ?= python

.PHONY: pipeline alerts scenario

pipeline:
	$(PYTHON) scripts/run_pipeline.py

alerts:
	$(PYTHON) scripts/run_alerts.py

scenario:
	$(PYTHON) scripts/run_scenario_simulator.py

