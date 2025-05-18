# Contributing to GitWise

Thank you for your interest in contributing to GitWise! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/gitwise.git
   cd gitwise
   ```
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   make install-dev
   ```

## Development Workflow

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests:
   ```bash
   make test
   ```
4. Run linting:
   ```bash
   make lint
   ```
5. Commit your changes using conventional commits:
   ```bash
   gitwise commit "feat: add new feature"
   ```
6. Push your branch and create a pull request

## Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all functions
- Keep functions small and focused
- Write tests for new features

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Maintain or improve test coverage
- Run tests with: `make test`

## Documentation

- Update README.md if needed
- Add docstrings to new functions
- Update CHANGELOG.md for significant changes
- Add examples for new features

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with your changes
3. Ensure all tests pass
4. Ensure linting passes
5. Request review from maintainers

## Development Commands

- `make install`: Install package
- `make install-dev`: Install development dependencies
- `make test`: Run tests
- `make lint`: Run linting
- `make format`: Format code
- `make clean`: Clean build files

## Questions?

Feel free to open an issue for any questions or concerns. 