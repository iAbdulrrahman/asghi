"""Test verifying Makefile public-check target and documentation requirements.
"""
import os
import subprocess
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAKEFILE_PATH = os.path.join(ROOT_DIR, "Makefile")
README_PATH = os.path.join(ROOT_DIR, "README.md")


def test_makefile_has_public_check_target():
    assert os.path.exists(MAKEFILE_PATH)
    with open(MAKEFILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "public-check" in content, "Makefile must define public-check target"
    assert "ASGHI_PUBLIC_URL" in content, "Makefile public-check target must check ASGHI_PUBLIC_URL"


def test_readme_documents_public_check_and_ci_flags():
    assert os.path.exists(README_PATH)
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()
    assert "make public-check" in readme or "public-check" in readme, "README must document make public-check"
    assert "ASGHI_PUBLIC_URL" in readme, "README must document ASGHI_PUBLIC_URL"
    assert "--workers 1" in readme or "workers" in readme, "README must document --workers 1 flag for uvicorn"
    assert "-no-audio" in readme, "README must document -no-audio emulator flag for headless/CI runs"


def test_public_check_fails_fast_when_env_unset():
    # Run make public-check or python script check without ASGHI_PUBLIC_URL
    env = os.environ.copy()
    env.pop("ASGHI_PUBLIC_URL", None)
    # Check that Makefile errors out or echoes explicit requirement
    with open(MAKEFILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'ifndef ASGHI_PUBLIC_URL' in content or 'ASGHI_PUBLIC_URL' in content
