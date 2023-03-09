SHELL=/usr/bin/env bash

.DEFAULT_GOAL := setup

setup:
	poetry install --only main

dev:
	poetry install --only dev

run:
	poetry run uvicorn napi_server:app --port 8080 --workers $$(nproc) --host ::

docs:
	mkdocs serve --dev-addr localhost:9000

.PHONY: setup run docs
