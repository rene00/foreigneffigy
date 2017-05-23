#!/usr/bin/make

VENV ?= $(PWD)/venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

default: build

build:
	virtualenv --python=python3 $(VENV)
	$(PIP) install -r requirements.txt


clean:
	rm -rf $(VENV) __pycache__
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
