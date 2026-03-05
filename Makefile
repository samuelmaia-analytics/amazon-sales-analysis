PYTHON ?= python

.PHONY: pipeline alerts scenario

pipeline:
	$(PYTHON) scripts/run_pipeline.py

alerts:
	$(PYTHON) alerts/discount_spike_alert.py

scenario:
	$(PYTHON) scenario_simulation.py
