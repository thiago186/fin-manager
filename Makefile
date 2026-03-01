.PHONY: dev backend frontend celery stop help

# Default target - run backend, frontend, and celery in parallel
dev:
	@echo "Starting all services (backend, frontend, celery)..."
	@trap 'kill 0' EXIT; \
	cd backend && uv run python src/manage.py runserver & \
	cd frontend && pnpm run dev & \
	cd backend && PYTHONPATH=src uv run celery -A fin_manager.celery worker --loglevel=info & \
	wait

# Run backend server only
backend:
	@echo "Starting backend server..."
	cd backend && uv run python src/manage.py runserver

# Run frontend server only
frontend:
	@echo "Starting frontend server..."
	cd frontend && pnpm run dev

# Run Celery worker
celery:
	@echo "Starting Celery worker..."
	cd backend && PYTHONPATH=src uv run celery -A fin_manager.celery worker --loglevel=info

# Stop all running servers (kills processes on default ports)
stop:
	@echo "Stopping servers..."
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@echo "Servers stopped"

# Help target
help:
	@echo "Available commands:"
	@echo "  make dev      - Run backend, frontend, and celery in parallel (default)"
	@echo "  make backend  - Run backend server only"
	@echo "  make frontend - Run frontend server only"
	@echo "  make celery   - Run Celery worker only"
	@echo "  make stop     - Stop all running servers"
	@echo "  make help     - Show this help message"
