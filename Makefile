.PHONY: install install-dev test lint format clean build test-release release

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

build: clean
	pip install --upgrade build twine
	python -m build
	twine check dist/*

test-release: build
	@echo "Uploading to TestPyPI..."
	@echo "Make sure TEST_PYPI_API_TOKEN is set!"
	twine upload --repository testpypi dist/*
	@echo "Test installation with:"
	@echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ gitwise"

release: build
	@echo "Uploading to PyPI..."
	@echo "Make sure PYPI_API_TOKEN is set!"
	twine upload dist/* 