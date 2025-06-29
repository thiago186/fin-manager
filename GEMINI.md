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
- **Language & Style**  
  - Follow **PEP 8** and **PEP 257** (docstrings in google style).  
  - Use `ruff` for formatting. 
  - Type annotations mandatory; enforce via `mypy`.
- **Naming**  
  - Modules & packages: `snake_case`.  
  - Classes: `PascalCase`.  
  - Constants: `UPPER_SNAKE_CASE`.  
  - DB tables mirror model names (e.g., `users`, `accounts`).

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
