# Fin Manager

This project provides a backend for a personal finance tracker built with
Django and the Django REST Framework (DRF).

## Development Setup

Dependencies are managed using [uv](https://github.com/astral-sh/uv). After
creating a virtual environment with `uv venv .venv`, new packages can be added
with `uv add <package>`.

Code quality is enforced using [Ruff](https://docs.astral.sh/ruff/) and
[Mypy](https://mypy-lang.org/). Configuration for Ruff lives in
`pyproject.toml` and type checking options are defined in `mypy.ini`.

Run programmatic checks with:

```bash
ruff .
mypy .
alembic history --verbose
```
