# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set workdir and copy dependencies files
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --all-groups --locked

# Update PATH to use uv-created virtual environment
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy application code
COPY . .

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
