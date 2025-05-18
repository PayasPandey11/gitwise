.PHONY: install install-dev test lint format clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ --cov=gitwise --cov-report=term-missing

lint:
	flake8 gitwise tests
	black --check gitwise tests
	isort --check-only gitwise tests
	mypy gitwise tests

format:
	black gitwise tests
	isort gitwise tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} + 