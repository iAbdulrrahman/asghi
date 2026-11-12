"""Test to ensure scripts/ui_smoke.py enforces real behavioral assertions
without relying on image file sizes.
"""
import inspect
import os
import re

SMOKE_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "ui_smoke.py")


def test_ui_smoke_has_behavioral_assertions_and_no_size_checks():
    assert os.path.exists(SMOKE_PATH), f"Smoke script not found at {SMOKE_PATH}"
    with open(SMOKE_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. No assertions should rest on image size
    assert "assert size > 10000" not in code, "ui_smoke.py must not assert image size > 10000"
    assert not re.search(r"assert\s+size\s*>", code), "No assertion may rest on file size"

    # 2. Learner audio playback assertions
    assert "FileNotFoundException" in code, "ui_smoke.py must check logcat for FileNotFoundException"
    assert "Cleartext" in code, "ui_smoke.py must check logcat for Cleartext errors"
    assert "Source error" in code or "TYPE_SOURCE" in code, "ui_smoke.py must check logcat for Source errors"
    assert "logcat" in code, "ui_smoke.py must inspect logcat"

    # 3. Contributor submissions status chips
    assert "تسجيلاتي" in code, "ui_smoke.py must navigate to contributor submissions tab"

    # 4. Reviewer verification against API
    assert "reviewer" in code, "ui_smoke.py must drive reviewer role"

    # 5. Admin verification
    assert "/api/admin/dashboard" in code or "dashboard" in code, "ui_smoke.py must check admin dashboard"
    assert "resolve" in code, "ui_smoke.py must test flag resolution"

    # 6. Structured PASS/FAIL reporting and non-zero exit on failure
    assert "[PASS]" in code, "ui_smoke.py must output structured [PASS] lines"
    assert "[FAIL]" in code, "ui_smoke.py must output structured [FAIL] lines"
    assert "sys.exit(" in code or "raise SystemExit" in code, "ui_smoke.py must exit non-zero on assertion failure"


def test_assertion_tracker_behavior():
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
    from ui_smoke import AssertionTracker

    tracker = AssertionTracker()
    assert tracker.check(True, "Passing condition") is True
    assert tracker.passed == 1
    assert tracker.failed == 0

    assert tracker.check(False, "Failing condition") is False
    assert tracker.passed == 1
    assert tracker.failed == 1

    # Non-zero exit code when failed > 0
    assert tracker.summary() == 1

    clean_tracker = AssertionTracker()
    clean_tracker.check(True, "All good")
    assert clean_tracker.summary() == 0

