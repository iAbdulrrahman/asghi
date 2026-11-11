# Auto-discover Python, Virtualenv, and Flutter (supports Windows and Unix)
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

.PHONY: setup check test seed test-backend test-mobile test-live device-check public-check help

help:
	@echo "Available targets:"
	@echo "  make setup        - Create virtualenv (.venv), install backend dependencies, and resolve mobile packages"
	@echo "  make check        - Run hermetic verification checks (setup, seed, live e2e, backend tests, mobile tests)"
	@echo "  make seed         - Seed the SQLite database with test data"
	@echo "  make test-backend - Run the pytest suite and restart verification using .venv"
	@echo "  make test-live    - Run live end-to-end multi-role server integration tests using .venv"
	@echo "  make test-mobile  - Run flutter analyze and flutter test"
	@echo "  make device-check - Run live multi-role UI smoke walkthrough on connected Android device/emulator"
	@echo "  make public-check - Run live UI smoke walkthrough over public HTTPS tunnel (requires ASGHI_PUBLIC_URL)"

$(VENV_PY):
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PY) -m pip install -r requirements.txt

setup: $(VENV_PY)
	$(VENV_PY) -m pip install -r requirements.txt
	cd mobile && $(FLUTTER) pub get

seed: setup
	$(VENV_PY) seed.py

test-live: setup
	$(VENV_PY) scripts/e2e.py

test-backend: setup
	$(VENV_PY) -m pytest
	$(VENV_PY) -m pytest tests/test_fix_4_seed_restart.py

test-mobile:
	cd mobile && $(FLUTTER) analyze && $(FLUTTER) test

device-check: seed
	$(VENV_PY) scripts/ui_smoke.py

ifndef ASGHI_PUBLIC_URL
public-check:
	$(error ASGHI_PUBLIC_URL is not set. Please provide ASGHI_PUBLIC_URL=https://<domain> to run public verification)
else
public-check: setup
	@echo "Running public verification against $(ASGHI_PUBLIC_URL)..."
	$(VENV_PY) scripts/ui_smoke.py
endif

check: setup
	$(VENV_PY) seed.py
	$(VENV_PY) scripts/e2e.py
	$(VENV_PY) -m pytest
	$(VENV_PY) -m pytest tests/test_fix_4_seed_restart.py
	cd mobile && $(FLUTTER) analyze && $(FLUTTER) test
