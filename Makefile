SHELL=/usr/bin/env bash

.DEFAULT_GOAL := setup

setup:
	poetry install

run:
	poetry run uvicorn napi_server:app --port 8080 --workers $$(nproc) --host ::

.PHONY: setup run
