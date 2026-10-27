# make up | run | evidence | verify | report | test | test-integration | test-e2e | lint | audit | check | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CLI := $(VENV)/bin/controls-evidence
POSTGRES_USER ?= postgres
POSTGRES_DB ?= notes
PSQL := docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q

-include .env
export

.PHONY: help install env up db queries reset-db run evidence scan verify report serve api-up smoke test test-integration \
        test-e2e lint format audit check docker-build down clean

help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the hash-pinned lock file

env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }

up: env $(STAMP) ## start PostgreSQL and apply sql/001_schema.sql and sql/002_seed.sql
	docker compose up -d --wait --wait-timeout 900 db
	$(MAKE) --no-print-directory db

db: ## apply the schema (roles, tables, append-only audit log, grants) and the seed
	$(PSQL) -v app_rw_password='$(APP_RW_PASSWORD)' -v migrator_password='$(MIGRATOR_PASSWORD)' \
	  -v retention_password='$(RETENTION_PASSWORD)' < sql/001_schema.sql
	$(PSQL) < sql/002_seed.sql

queries: ## run sql/003_queries.sql
	docker compose exec -T db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql

reset-db: ## drop the public schema and rebuild it from the SQL scripts
	$(PSQL) < sql/reset.sql
	$(MAKE) --no-print-directory db

# A clean run: empty database, the cloud account back as the fixture has it, the pack rebuilt from scratch.
run: up ## the lesson's scenario: use the service, collect the six artifacts, review access, index, verify
	$(MAKE) --no-print-directory reset-db
	rm -rf state $(EVIDENCE_DIR)
	$(CLI) collect

evidence: $(STAMP) ## collect every artifact into evidence/ (needs make up)
	$(CLI) collect

scan: env $(STAMP) ## C5 only: scan the locked dependencies and write the dated report (no database needed)
	$(CLI) scan

verify: $(STAMP) ## check every control maps to evidence and every file exists and says what it should
	$(CLI) verify

report: $(STAMP) ## write build/report.md: controls, evidence, findings, framework overlap
	$(CLI) report

serve: $(STAMP) ## run the notes API with gunicorn on localhost (needs make up)
	$(VENV)/bin/gunicorn --bind 127.0.0.1:$(HTTP_PORT) --workers 2 notes_evidence.interfaces.wsgi:app

api-up: ## build the image and start the API container beside the database
	docker compose --profile api up -d --build --wait api

smoke: ## the API container answers /healthz
	curl -fsS http://127.0.0.1:$(HTTP_PORT)/healthz

test: $(STAMP) ## unit tests with coverage (no services needed)
	$(PY) -m pytest tests/unit --cov=notes_evidence --cov-report=term
	$(PY) -m coverage report --include='src/notes_evidence/domain/*,src/notes_evidence/application/*' --fail-under=95

test-integration: $(STAMP) ## adapters and the HTTP app against PostgreSQL (make up first)
	$(PY) -m pytest tests/integration -m integration

test-e2e: $(STAMP) ## the whole scenario into a temporary folder (make up first)
	$(PY) -m pytest tests/e2e -m e2e

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

check: lint test ## everything that needs no services

docker-build: ## build the API image
	docker build -t compliance-controls-and-evidence:dev .

down: ## stop PostgreSQL and delete its data and the generated state
	docker compose --profile api down -v
	rm -rf state build

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
