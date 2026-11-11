# Auto-discover Python and Flutter (supports Windows and Unix, even if Flutter is not on PATH)
PYTHON ?= python
ifeq ($(OS),Windows_NT)
  FLUTTER ?= $(shell where flutter 2>nul || echo C:/flutter/bin/flutter.bat)
else
  FLUTTER ?= $(shell command -v flutter 2>/dev/null || echo /c/flutter/bin/flutter.bat)
endif

.PHONY: check test seed test-backend test-mobile help

help:
	@echo "Available targets:"
	@echo "  make check        - Run all verification checks (install, seed, backend tests, mobile tests)"
	@echo "  make seed         - Seed the SQLite database with test data"
	@echo "  make test-backend - Run the pytest suite and restart verification"
	@echo "  make test-mobile  - Run flutter analyze and flutter test"

seed:
	$(PYTHON) seed.py

test-backend:
	$(PYTHON) -m pytest
	$(PYTHON) tests/test_fix_4_seed_restart.py

test-mobile:
	cd mobile && $(FLUTTER) analyze && $(FLUTTER) test

check:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) seed.py
	$(PYTHON) -m pytest
	$(PYTHON) tests/test_fix_4_seed_restart.py
	cd mobile && $(FLUTTER) analyze && $(FLUTTER) test
