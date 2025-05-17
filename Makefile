.PHONY: install test clean lint format

install:
	pip install -e .

test:
	pytest

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 gitwise tests
	mypy gitwise tests

format:
	black gitwise tests
	isort gitwise tests

dev-install:
	pip install -e ".[dev]"

# Development dependencies
dev-deps:
	pip install pytest flake8 mypy black isort 