# gitwise

AI-powered git assistant for generating smart commit messages, PR descriptions, and changelogs using open-source LLMs (offline support for privacy).

## Features
- **Smart Commit Message Generator**: Analyzes staged changes and generates concise, conventional commit messages using an LLM.
- **Modular CLI**: Easily extensible Typer-based CLI.
- **Offline LLM Support**: Uses open-source models (e.g., Zephyr-7B-Beta) for privacy.

## Installation
```sh
pip install -r requirements.txt
```

## Usage
From the root of your git repository:
```sh
python -m gitwise.cli commit
```

## Project Structure
```
gitwise/
├── cli.py                # Typer CLI entry point
├── llm.py                # LLM (Zephyr, etc.) inference logic
├── gitutils.py           # Git-related utilities (diff, commit, etc.)
├── features/
│   └── commit.py         # Commit message generation logic
└── README.md
```

## Example
```sh
# Stage your changes
$ git add .
# Generate a commit message
$ python -m gitwise.cli commit
```

## License
MIT 