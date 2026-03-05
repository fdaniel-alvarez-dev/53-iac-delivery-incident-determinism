.PHONY: setup demo test lint clean

VENV := .venv
PY := $(VENV)/bin/python

setup:
	python3 -m venv $(VENV)
	$(PY) -c "import sys; assert sys.version_info >= (3,11)"
	$(PY) -m compileall -q src

demo: setup
	PYTHONPATH=src $(PY) -m portfolio_proof report --inputs examples/good --repo-root . --also-scan examples/bad --output artifacts/report.md
	@echo "Wrote artifacts/report.md"

lint: setup
	$(PY) -m compileall -q src
	$(PY) -m compileall -q tests
	PYTHONPATH=src $(PY) -m portfolio_proof validate --inputs examples/good --repo-root .

test: setup
	PYTHONPATH=src $(PY) -m unittest discover -s tests -p "test_*.py" -q

clean:
	rm -rf $(VENV) artifacts
