# Auto-discover Python and Flutter (supports Windows and Unix, even if Flutter is not on PATH)
PYTHON ?= python

ifeq ($(OS),Windows_NT)
  VENV_DIR := .venv
  VENV_PY := $(VENV_DIR)/Scripts/python.exe
  FLUTTER ?= $(shell where flutter 2>nul || echo C:/flutter/bin/flutter.bat)
else
  VENV_DIR := .venv
  VENV_PY := $(VENV_DIR)/bin/python
  FLUTTER ?= $(shell command -v flutter 2>/dev/null || echo /c/flutter/bin/flutter.bat)
endif

.PHONY: setup check test seed test-backend test-mobile test-live help

help:
	@echo "Available targets:"
	@echo "  make setup        - Install backend dependencies and resolve mobile packages"
	@echo "  make check        - Run all verification checks (install, seed, live e2e, backend tests, mobile tests)"
	@echo "  make seed         - Seed the SQLite database with test data"
	@echo "  make test-backend - Run the pytest suite and restart verification"
	@echo "  make test-live    - Run live end-to-end multi-role server integration tests"
	@echo "  make test-mobile  - Run flutter analyze and flutter test"

setup:
	$(PYTHON) -m pip install -r requirements.txt
	cd mobile && $(FLUTTER) pub get

seed:
	$(PYTHON) seed.py

test-live:
	$(PYTHON) scripts/e2e.py

test-backend:
	$(PYTHON) -m pytest
	$(PYTHON) tests/test_fix_4_seed_restart.py

test-mobile:
	cd mobile && $(FLUTTER) analyze && $(FLUTTER) test

check:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) seed.py
	$(PYTHON) scripts/e2e.py
	$(PYTHON) -m pytest
	$(PYTHON) tests/test_fix_4_seed_restart.py
	cd mobile && $(FLUTTER) analyze && $(FLUTTER) test
