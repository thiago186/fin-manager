# Fin Manager

This project provides a backend for a personal finance tracker.

## Development Setup

Dependencies are managed using [uv](https://github.com/astral-sh/uv). After
creating a virtual environment with `uv venv .venv`, new packages can be added
with `uv add <package>`.

Run programmatic checks with:

```bash
ruff .
mypy .
alembic history --verbose
```
