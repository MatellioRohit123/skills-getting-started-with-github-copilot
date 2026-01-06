import copy
import os
import sys
import pytest

# Ensure src is importable (app.py lives in src/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import app as app_module

from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def restore_activities():
    """Backup and restore the in-memory activities state for each test."""
    orig = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(orig)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Basketball" in data
    assert isinstance(data["Basketball"]["participants"], list)


def test_signup_and_unregister_flow(client):
    email = "pytest-user@example.com"
    activity = "Chess Club"

    # Ensure initial state does not contain the test email
    assert email not in app_module.activities[activity]["participants"]

    # Sign up
    r = client.post(f"/activities/{activity}/signup?email={email}")
    assert r.status_code == 200
    assert email in app_module.activities[activity]["participants"]

    # Duplicate signup should fail
    r2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert r2.status_code == 400

    # Unregister
    r3 = client.delete(f"/activities/{activity}/participants?email={email}")
    assert r3.status_code == 200
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_missing_participant(client):
    email = "notfound@example.com"
    r = client.delete(f"/activities/Chess Club/participants?email={email}")
    assert r.status_code == 404
