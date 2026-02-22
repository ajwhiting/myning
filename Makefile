play:
	@uv run ./run.sh

dev:
	@uv run ./dev.sh

migrate:
	uv run python migrate.py $(id)

sync:
	uv sync --group dev

lock:
	uv lock

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest
