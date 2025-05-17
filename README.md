# GitWise 🤖

An AI-powered Git assistant that helps you write better commit messages and pull request descriptions.

## Author

**Payas Pandey**  
- GitHub: [@PayasPandey11](https://github.com/PayasPandey11)
- LinkedIn: [payaspandey](https://www.linkedin.com/in/payaspandey/)
- Email: rpayaspandey@gmail.com

## Features

- 🤖 AI-powered commit message generation
- 📝 Smart pull request descriptions
- 🔄 Seamless Git command integration
- 🎯 Conventional commit format support
- 🚀 Easy to use CLI interface

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

### Installation & Setup (Recommended: Using Makefile)

**All Makefile commands must be run from the project root directory.**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/gitwise.git
   cd gitwise
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies and the package in development mode:**
   ```bash
   make install
   ```

4. **(Recommended) Install development dependencies:**
   ```bash
   make dev-deps
   ```

5. **Set up your OpenRouter API key:**
   ```bash
   export OPENROUTER_API_KEY='your-api-key-here'  # On Windows: set OPENROUTER_API_KEY=your-api-key-here
   ```

### Manual Installation (Alternative)

If you prefer not to use the Makefile:

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Basic Commands

```bash
# Stage changes and generate a commit message
gitwise add .

# Generate a commit message for staged changes
gitwise commit

# Generate a PR description from commit history
gitwise pr

# Pass through to git commands
gitwise status
gitwise log
```

### Examples

1. Stage and commit changes:
   ```bash
   gitwise add .
   # Review the generated commit message
gitwise commit
   ```

2. Generate a PR description:
   ```bash
   gitwise pr
   ```

3. Use standard Git commands:
   ```bash
   gitwise status
   gitwise log
   gitwise branch
   ```

## Makefile Commands

- `make install` — Install the package in editable mode (dev setup)
- `make dev-deps` — Install development dependencies (pytest, flake8, mypy, black, isort)
- `make test` — Run tests (if any are present)
- `make lint` — Run code linters (flake8, mypy)
- `make format` — Format code (black, isort)
- `make clean` — Remove build/test artifacts

**Note:** Always run these commands from the project root (where the Makefile is located).

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `GITWISE_MODEL`: (Optional) Override the default model (default: anthropic/claude-3-opus)

## Development

### Project Structure

```
gitwise/
├── cli.py          # Command-line interface
├── llm.py          # LLM integration
├── git_utils.py    # Git utilities
└── __init__.py
```

### Running Tests

```bash
make test
```

### Linting & Formatting

```bash
make lint
make format
```

### Cleaning Up

```bash
make clean
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

- **Makefile errors:** Ensure you are in the project root directory when running `make` commands.
- **ModuleNotFoundError:** Make sure you have run `make install` or `pip install -e .` in your virtual environment.
- **API Key issues:** Double-check that `OPENROUTER_API_KEY` is set in your environment.

## License

MIT License - see LICENSE file for details 