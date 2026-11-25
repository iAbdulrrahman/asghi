"""Password storage: salted PBKDF2, and the legacy-hash upgrade path.

Would have caught the original defect: hash_password() returned an unsalted
SHA-256 digest, so equal passwords produced equal hashes and any dump was
directly rainbow-tableable.
"""
import hashlib
import os

from fastapi.testclient import TestClient

from asghi.domain.user import (
    HASH_SCHEME,
    User,
    hash_password,
    needs_rehash,
    verify_password,
)
from asghi.repository import Repository

LEGACY = hashlib.sha256(b"123456").hexdigest()


def test_hash_is_salted_pbkdf2_and_differs_per_call():
    first, second = hash_password("123456"), hash_password("123456")
    assert first.startswith(f"{HASH_SCHEME}$210000$")
    assert first != second, "identical passwords must not produce identical hashes"
    assert len(first.split("$")) == 4


def test_verify_password_accepts_correct_and_rejects_wrong():
    stored = hash_password("123456")
    assert verify_password("123456", stored)
    assert not verify_password("1234567", stored)
    assert not verify_password("123456", "not-a-hash")


def test_legacy_digest_verifies_but_is_flagged_for_rehash():
    assert verify_password("123456", LEGACY)
    assert not verify_password("wrong", LEGACY)
    assert needs_rehash(LEGACY)
    assert not needs_rehash(hash_password("123456"))


def test_login_upgrades_a_legacy_hash_and_persists_it(tmp_path):
    db_path = str(tmp_path / "legacy.db")
    repo = Repository(db_path=db_path)
    user = User(email="legacy@asghi.org", displayName="Legacy", passwordHash=LEGACY)
    repo.save_user(user)

    os.environ["ASGHI_DB_PATH"] = db_path
    from asghi.domain.passage import Passage

    User._registry.clear()
    Passage._registry.clear()
    from asghi.api import app

    with TestClient(app) as client:
        first = client.post(
            "/api/auth/login",
            json={"identifier": "legacy@asghi.org", "password": "123456"},
        )
        assert first.status_code == 200, first.text

        second = client.post(
            "/api/auth/login",
            json={"identifier": "legacy@asghi.org", "password": "123456"},
        )
        assert second.status_code == 200, second.text

    stored = Repository(db_path=db_path).get_user_by_identifier("legacy@asghi.org")
    assert stored.passwordHash.startswith(f"{HASH_SCHEME}$"), "hash was not upgraded in storage"
    assert stored.passwordHash != LEGACY
