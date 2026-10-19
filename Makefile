PYTHON ?= python3.11
VENV ?= .venv
BIN := $(VENV)/bin
TEST_PYTHON := $(shell if test -x "$(BIN)/python"; then printf '%s' "$(BIN)/python"; else printf '%s' "$(PYTHON)"; fi)

.PHONY: install test run docker-build docker-run demo

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install -r requirements.txt

test:
	$(TEST_PYTHON) scripts/test.py

run:
	$(TEST_PYTHON) -m uvicorn agentguard.api:app --app-dir backend --host $${HOST:-127.0.0.1} --port $${PORT:-8000}

docker-build:
	docker build -t agentguard:latest .

docker-run:
	docker compose up --build

demo:
	$(TEST_PYTHON) attack_agent.py --url http://$${HOST:-127.0.0.1}:$${PORT:-8000}
