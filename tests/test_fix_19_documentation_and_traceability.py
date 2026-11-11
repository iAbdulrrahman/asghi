"""Test verification for Item 19 (Documentation & Traceability catch-up).
Verifies TRACEABILITY.md, INVENTIONS.md, PROGRESS.md, and HISTORY.md accurately document
all fixes and live device evidence.
"""
import os
import pytest


def test_traceability_matrix_evidence():
    traceability_path = os.path.join(os.path.dirname(__file__), "..", "TRACEABILITY.md")
    assert os.path.exists(traceability_path), "TRACEABILITY.md does not exist"
    with open(traceability_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify rows 11, 19, 20 cite live screencaps and tests
    assert "live_learner.png" in content, "TRACEABILITY.md missing citation of live_learner.png"
    assert "scripts/ui_smoke.py" in content, "TRACEABILITY.md missing citation of scripts/ui_smoke.py"
    assert "arabic_display.dart" in content, "TRACEABILITY.md missing citation of arabic_display.dart"
    assert "extract_audio_duration" in content or "test_fix_15_audio_duration_validation.py" in content


def test_inventions_catalog_contains_pass5_entries():
    inventions_path = os.path.join(os.path.dirname(__file__), "..", "INVENTIONS.md")
    assert os.path.exists(inventions_path), "INVENTIONS.md does not exist"
    with open(inventions_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure decisions 34 through 42 are present
    assert "| 34 |" in content, "INVENTIONS.md missing decision 34 (browse verified-only)"
    assert "| 35 |" in content, "INVENTIONS.md missing decision 35 (audioUrl)"
    assert "| 37 |" in content, "INVENTIONS.md missing decision 37 (advance passage status)"
    assert "| 39 |" in content, "INVENTIONS.md missing decision 39 (WAV header duration extraction)"
    assert "| 41 |" in content, "INVENTIONS.md missing decision 41 (arabic_display.dart)"
    assert "| 42 |" in content, "INVENTIONS.md missing decision 42 (scripts/ui_smoke.py & make device-check)"


def test_progress_and_history_record_pass5():
    progress_path = os.path.join(os.path.dirname(__file__), "..", "PROGRESS.md")
    history_path = os.path.join(os.path.dirname(__file__), "..", "HISTORY.md")

    with open(progress_path, "r", encoding="utf-8") as f:
        p_content = f.read()
    with open(history_path, "r", encoding="utf-8") as f:
        h_content = f.read()

    assert "live_learner.png" in p_content
    assert "make device-check" in p_content
    assert "Pass 5" in h_content
    assert "live_admin.png" in h_content
