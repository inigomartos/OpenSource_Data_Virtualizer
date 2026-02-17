.PHONY: dev test test-unit test-integration test-e2e lint build seed migrate

dev:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build

test: test-unit test-integration
	@echo "All tests passed."

test-unit:
	cd backend && pytest tests/unit tests/ai -v --cov=app --cov-report=term-missing

test-integration:
	docker compose -f docker/docker-compose.test.yml up -d --wait
	cd backend && pytest tests/integration -v
	docker compose -f docker/docker-compose.test.yml down

test-e2e:
	cd frontend && npx playwright test

lint:
	cd backend && ruff check . && mypy app/
	cd frontend && npm run lint

build:
	docker compose -f docker/docker-compose.yml build

seed:
	cd backend && python scripts/seed_demo_data.py

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(msg)"
