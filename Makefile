dev:
		poetry run flask --app page_analyzer:app run

PORT ?= 8000
start:
		poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

install:
		poetry install

test:
		poetry run pytest

test-coverage:
		poetry run pytest --cov=page_analyzer --cov-report xml

lint:
		poetry run flake8 page_analyzer

selfcheck:
		poetry check

check: selfcheck test lint

all: db-create schema-load

db-create:
	createdb project83 || echo 'skip'

schema-load:
	psql project83 < database.sql

db-reset:
	dropdb project83 || true
	createdb project83

.PHONY: install test lint selfcheck check build
