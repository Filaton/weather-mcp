# Copilot Instructions

## Project Overview

A Python application template with pre-configured tooling. Application logic lives in `app/`; `main.py` at the repo root is an optional standalone entry point that is separate from the `app` package.

## Key Structure

```
app/          # Application package — all feature code goes here
  __init__.py
  main.py     # Primary entry point; run via `uv run python -m app.main`
tests/        # Pytest test suite; mirrors app/ structure
main.py       # Standalone root entry point (optional, separate from app/)
pyproject.toml  # Project metadata, dependencies, and all tool config
pyrightconfig.json  # Pyright/Pylance type checking settings
```

## Dependency Management — always use `uv`, never `pip`

```bash
uv sync                        # Install/sync all dependencies (including dev)
uv add <package>               # Add a runtime dependency
uv add --dev <package>         # Add a dev dependency
```

Dev dependencies (`pre-commit`, `pytest`, `ruff`) are declared under `[dependency-groups] dev` in [pyproject.toml](../pyproject.toml).

## Essential Commands

```bash
uv run python -m app.main       # Run the application
uv run pytest                   # Run tests
uv run pytest --cov=app         # Run tests with coverage
uv run ruff format .            # Format code
uv run ruff check --fix .       # Lint and auto-fix
uv run pre-commit run --all-files  # Run all pre-commit hooks manually
```

Pre-commit hooks fire automatically on `git commit`, running ruff lint + format on staged Python files.

## Code Style & Conventions

- **Formatter / linter / import sorter**: ruff (replaces black, flake8, isort)
- **Line length**: 88 (configured in `[tool.ruff]` in [pyproject.toml](../pyproject.toml))
- **Active lint rule sets**: `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort)
- **Python version**: 3.13+ — use modern syntax (e.g., `X | Y` unions, `match` statements)
- VS Code auto-formats and organizes imports on save via the Ruff extension ([.vscode/settings.json](../.vscode/settings.json))

## Type Checking

Pyright runs in `standard` mode (see [pyrightconfig.json](../pyrightconfig.json)), using the `.venv` virtualenv. Annotations are encouraged but not required everywhere. Pylance in VS Code reflects the same configuration.

## Adding Tests

Place test files under `tests/`. Pytest discovers them automatically (`testpaths = ["tests"]` in [pyproject.toml](../pyproject.toml)). No custom fixtures or conftest exist yet — add `tests/conftest.py` when shared fixtures are needed.
