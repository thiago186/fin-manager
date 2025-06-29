# About the project

This project contains the code for the backend of a personal finance tracker system. The users can register their bank accounts, credit cards, incomes and expenses and track them into one single and centralized place.

## Project Overview
- **Purpose**: Personal financial control app supporting multi-user accounts, credit cards, categories/subcategories, tagged transactions, and installments.
- **Tech Stack**:  
  - **Language**: Python 3.11  
  - **Web Framework**: Django Rest FrameWork
  - **ORM**: Django ORM
  - **Auth**: Django Rest
  - **DB**: PostgreSQL

## Coding Conventions
- **Python modules**:
  - Always use absolute imports, never use relative impors. For example, use `from apps.users.models import User` instead of `from .models import User`.
  - Never use in-function imports, always import at the top of the file.
- **Package manager**: 
  - Use `uv` for package management.
  - Always use `uv add <package>` to add a package. Don't use `pip` or `pipenv`.
  - Every time that you want to run a command inside the project envirionment, use `uv run <command>`.
- **Language & Style**  
  - Follow **PEP 8** and **PEP 257** (docstrings in google style).  
  - Use `ruff` for formatting. 
  - Type annotations mandatory; enforce via `mypy`.
- **Naming**  
  - Modules & packages: `snake_case`.  
  - Classes: `PascalCase`.  
  - Constants: `UPPER_SNAKE_CASE`.  
  - DB tables mirror model names (e.g., `users`, `accounts`).
- **Running django commands**:
  - For running django commands, use `uv run python src/manage.py <djangocommand>`, like `uv run python src/manage.py makemigrations`.
  - All django apps are inside the `src/apps` folder. If you want to create a new app, create it inside this structure. Also, manually change the `ApiConfig.name` from `name="module"` to `name="apps.module"` inside the `apps.py` file. Also include `apps.module` in the `INSTALLED_APPS` list in `src/fin_manager/settings.py`.

## Testing Requirements
- Create only simple unit tests.
- Use `pytest` for testing.
- Create always functions to test. Don't use class-based tests.
- Use fixtures and monkeypatching always needed.

## Commits convention
- Use conventional commits convention, such as `feat: implemment new feature`

## Project coding standards
- Use python sintax and bultins from python 3.11
- Pefer a pythonic way of doing stuff. Use list comprehension always possible
