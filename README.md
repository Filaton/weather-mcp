# python-template-app

A Python application template with batteries-included tooling: formatting, linting, import sorting, type checking, and pre-commit hooks — all pre-configured and ready to use.

## Prerequisites

| Tool                                                                                    | Version | Notes                                                                 |
| --------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------- |
| Python                                                                                  | 3.13+   | Manage with [pyenv](https://github.com/pyenv/pyenv) or system install |
| [uv](https://docs.astral.sh/uv/)                                                        | latest  | Dependency management & virtualenv                                    |
| VS Code                                                                                 | latest  | Recommended editor                                                    |
| [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) | latest  | VS Code extension for type checking                                   |

## Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd python-template-app

# 2. Create the virtual environment and install all dependencies
uv sync

# 3. Install pre-commit hooks
uv run pre-commit install
```

## Running the App

Once you've populated `app/main.py`, run the application with:

```bash
uv run python -m app.main
```

## Running Tests

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=app
```

## Code Quality

### Format

```bash
uv run ruff format .
```

### Lint (and auto-fix)

```bash
uv run ruff check --fix .
```

### Run all pre-commit hooks manually

```bash
uv run pre-commit run --all-files
```

Pre-commit hooks run automatically on every `git commit`, catching formatting and lint issues before they reach the repository.

## Tooling Overview

| Tool                                                      | Purpose                                          | Config                                              |
| --------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------- |
| [ruff](https://docs.astral.sh/ruff/)                      | Formatter, linter & import sorter                | `pyproject.toml` → `[tool.ruff]`                    |
| [pytest](https://docs.pytest.org/)                        | Test runner                                      | `pyproject.toml` → `[tool.pytest.ini_options]`      |
| [pre-commit](https://pre-commit.com/)                     | Git hook manager                                 | `.pre-commit-config.yaml`                           |
| [Pyright / Pylance](https://github.com/microsoft/pyright) | Static type checker                              | `pyrightconfig.json`                                |

- **Line length**: 88 — set in `[tool.ruff]`, applies to both formatting and linting.
- **Lint rules**: `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort) — configured in `[tool.ruff.lint]`.
- **Type checking mode**: `standard` — enables a broad set of Pyright checks without requiring annotations everywhere.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   └── main.py          # Application entry point
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── .pre-commit-config.yaml
├── .python-version      # Pinned Python version (used by pyenv / uv)
├── .vscode/
│   └── settings.json    # VS Code workspace settings
├── pyrightconfig.json   # Pyright / Pylance type checking config
├── pyproject.toml       # Project metadata, dependencies, tool config
└── main.py              # Standalone entry point (optional)
```
