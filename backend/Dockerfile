FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.6.6 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PYTHON_VERSION=3.11

COPY pyproject.toml pyproject.toml
COPY . .
    
RUN uv sync
RUN chmod +x /app/entrypoint.sh
