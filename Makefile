.PHONY: install test lint format run dashboard mcp clean

install:
	pip install -e ".[audio,dev]"

test:
	pytest --cov=argus --cov-report=term-missing

test-fast:
	pytest -m "not hardware and not display"

lint:
	ruff check argus tests
	python -m py_compile argus/**/*.py

format:
	ruff check --fix argus tests

run:
	python -m argus

dashboard:
	python -m argus

mcp:
	python -m argus.mcp_server

clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
