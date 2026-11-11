import os
import pytest
from importlib import reload


def test_secret_key_reads_from_env(monkeypatch):
    """Item 10: SECRET_KEY must be read from environment variable."""
    import asghi.security as sec

    monkeypatch.setenv("SECRET_KEY", "super-secret-from-environment-test-1234")
    monkeypatch.setenv("ENVIRONMENT", "development")
    # Verify get_secret_key or reloaded module picks up env var
    assert sec.get_secret_key() == "super-secret-from-environment-test-1234"


def test_production_mode_fails_fast_without_secret_key(monkeypatch):
    """Item 10: In production mode, application must fail fast if SECRET_KEY is not set."""
    import asghi.security as sec

    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        sec.get_secret_key()
