"""Test harness: every run uses a fresh, isolated SQLite database seeded with the synthetic tenants."""
import os
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="acedra-test-")
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_TMP}/acedra_test.db"
os.environ["LLM_PROVIDER"] = "none"
os.environ["EMBEDDING_PROVIDER"] = "lexical"
os.environ["EMAIL_PROVIDER"] = "log"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "database", "seeds"))

import pytest
import seed_all

seed_all.main()

from fastapi.testclient import TestClient

from app.main import app

PASSWORDS = {"admin": "AdminPass123!", "faculty": "FacultyPass123!", "mentor": "MentorPass123!",
             "placement": "PlacementPass123!", "student": "StudentPass123!"}


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


_token_cache = {}


def login(client, email, password=None):
    if email in _token_cache:
        return _token_cache[email]
    if password is None:
        local = email.split("@")[0]
        password = "PlatformPass123!" if email.endswith("acedra.example") else PASSWORDS.get(
            local.rstrip("0123456789"), "StudentPass123!")
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    _token_cache[email] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _token_cache[email]


@pytest.fixture(scope="session")
def auth(client):
    return lambda email, password=None: login(client, email, password)


def legal_versions(client):
    """Versions of the documents a person must accept, as shown on the invitation page."""
    docs = client.get("/api/v1/public/legal").json()
    return {d["doc_type"]: d["version"] for d in docs if d["doc_type"] in ("terms", "privacy")}

