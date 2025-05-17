# GitWise 🤖

An AI-powered Git assistant that helps you write better commit messages and pull request descriptions.

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

### Installation

#### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gitwise.git
cd gitwise
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your OpenRouter API key:
```bash
export OPENROUTER_API_KEY='your-api-key-here'  # On Windows: set OPENROUTER_API_KEY=your-api-key-here
```

5. Install the package in development mode:
```bash
pip install -e .
```

#### Using PyPI (Coming Soon)

```bash
pip install gitwise
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
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 