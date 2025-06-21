#!/bin/sh
exec uv run uvicorn config.asgi:application --host 0.0.0.0 --port ${PORT:-8000} --reload
