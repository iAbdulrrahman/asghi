"""Tests for configurable seed passwords and non-dev credential warnings.
"""
import logging
import os
import pytest
from asghi.domain.user import User


def test_seed_respects_env_var(tmp_path, monkeypatch):
    from asghi.seed import seed_database
    test_db = str(tmp_path / "test_seed_env.db")
    monkeypatch.setenv("ASGHI_SEED_PASSWORD", "SuperSecureEnvPass123!")

    seed_database(db_path=test_db)

    # All seeded users should authenticate with the env var password
    learner = next((u for u in User._registry if u.email == "learner@asghi.org"), None)
    assert learner is not None
    assert learner.login("learner@asghi.org", "SuperSecureEnvPass123!") is True
    assert learner.login("learner@asghi.org", "LearnerPass123!") is False

    admin = next((u for u in User._registry if u.email == "admin@asghi.org"), None)
    assert admin is not None
    assert admin.login("admin@asghi.org", "SuperSecureEnvPass123!") is True


def test_seed_respects_per_role_overrides(tmp_path, monkeypatch):
    from asghi.seed import seed_database
    test_db = str(tmp_path / "test_seed_overrides.db")
    monkeypatch.delenv("ASGHI_SEED_PASSWORD", raising=False)

    overrides = {
        "admin": "AdminSecret999!",
        "learner@asghi.org": "LearnerSpecialPass888!",
    }
    seed_database(db_path=test_db, password_overrides=overrides)

    admin = next((u for u in User._registry if u.email == "admin@asghi.org"), None)
    assert admin is not None
    assert admin.login("admin@asghi.org", "AdminSecret999!") is True

    learner = next((u for u in User._registry if u.email == "learner@asghi.org"), None)
    assert learner is not None
    assert learner.login("learner@asghi.org", "LearnerSpecialPass888!") is True


def test_seed_warns_on_defaults_in_non_dev(tmp_path, monkeypatch, caplog):
    from asghi.seed import seed_database
    test_db = str(tmp_path / "test_seed_warn.db")
    monkeypatch.delenv("ASGHI_SEED_PASSWORD", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    with caplog.at_level(logging.WARNING):
        seed_database(db_path=test_db)

    assert any(
        "SECURITY WARNING" in record.message or "default credentials" in record.message.lower()
        for record in caplog.records
    ), "A security warning must be logged when defaults are seeded into non-development environment"


def test_seed_alias_and_export():
    import asghi.seed
    assert hasattr(asghi.seed, "seed")
    assert asghi.seed.seed is asghi.seed.seed_database


def test_readme_documents_credential_rotation():

    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()
    assert "ASGHI_SEED_PASSWORD" in readme, "README must document ASGHI_SEED_PASSWORD"
    assert "rotation" in readme.lower() or "rotate" in readme.lower(), "README must document credential rotation"
