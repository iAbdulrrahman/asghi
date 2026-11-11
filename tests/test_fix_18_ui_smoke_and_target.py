"""Test verification for Item 18 (UI Smoke Script & make device-check target).
Verifies scripts/ui_smoke.py exists, Makefile defines device-check, and live screencaps exist (>10KB).
"""
import os
import py_compile
import pytest


def test_ui_smoke_script_exists_and_syntax():
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "ui_smoke.py")
    assert os.path.exists(script_path), "scripts/ui_smoke.py does not exist"
    # Ensure syntax is valid Python
    py_compile.compile(script_path, doraise=True)


def test_makefile_contains_device_check_target():
    makefile_path = os.path.join(os.path.dirname(__file__), "..", "Makefile")
    assert os.path.exists(makefile_path), "Makefile does not exist"
    with open(makefile_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "device-check" in content, "device-check not declared in Makefile"
    assert "scripts/ui_smoke.py" in content, "scripts/ui_smoke.py not referenced in Makefile target"


def test_live_screenshots_captured_and_sized():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "mobile", "docs")
    roles = ["learner", "contributor", "reviewer", "admin"]
    for role in roles:
        filename = f"live_{role}.png"
        path = os.path.join(docs_dir, filename)
        assert os.path.exists(path), f"Missing live screenshot: {filename}"
        size = os.path.getsize(path)
        assert size > 10000, f"Screenshot {filename} too small: {size} bytes <= 10000"
