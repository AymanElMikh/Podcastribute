.PHONY: dev down test worker lint migrate shell

COMPOSE = docker compose -f docker/docker-compose.yml

dev:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

test:
	pytest tests/ -v

worker:
	celery -A worker.celery_app worker --loglevel=info

lint:
	ruff check api/ tests/ worker/

migrate:
	alembic upgrade head

shell:
	$(COMPOSE) exec api bash

logs:
	$(COMPOSE) logs -f api worker

ps:
	$(COMPOSE) ps
