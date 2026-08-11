PYTHON ?= python

.PHONY: setup test audit reproduce-baselines backtest ablation external-data-assessment external-validation-2026q1 final-results reproduce lint

setup:
	$(PYTHON) -m pip install -r requirements.lock
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests scripts

audit:
	$(PYTHON) scripts/audit_core_data.py

reproduce-baselines:
	$(PYTHON) scripts/reproduce_baselines.py

backtest:
	$(PYTHON) scripts/run_backtests.py

ablation:
	$(PYTHON) scripts/run_ablation.py

external-data-assessment:
	$(PYTHON) scripts/assess_external_data.py

external-validation-2026q1:
	$(PYTHON) scripts/validate_2026q1_external.py

final-results:
	$(PYTHON) scripts/build_final_artifacts.py

reproduce:
	$(PYTHON) scripts/reproduce.py
