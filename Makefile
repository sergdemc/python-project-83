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

publish:
		poetry publish --dry-run

package-install:
		python3 -m pip install --force-reinstall --user dist/*.whl

lint:
		poetry run flake8 page_analyzer

selfcheck:
		poetry check

check: selfcheck test lint

build: check
		poetry build

.PHONY: install test lint selfcheck check build
