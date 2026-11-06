.PHONY: install dev test lint fmt typecheck migrate revision seed docker-up docker-down

install:
	uv sync

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest -q

lint:
	uv run ruff check . && uv run ruff format --check .

fmt:
	uv run ruff check --fix . && uv run ruff format .

typecheck:
	uv run mypy src

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"

seed:
	uv run python -m app.cli seed

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v
