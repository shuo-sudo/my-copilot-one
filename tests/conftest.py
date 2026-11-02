from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as backend


@pytest.fixture
def activity_data():
    return {
        "Chess Club": {
            "description": "Practice chess strategies",
            "schedule": "Fridays, 3:30 PM",
            "max_participants": 12,
            "participants": ["first@example.com", "second@example.com"],
        },
        "Art Club": {
            "description": "Explore drawing and painting",
            "schedule": "Wednesdays, 3:30 PM",
            "max_participants": 18,
            "participants": [],
        },
    }


@pytest.fixture(autouse=True)
def isolated_activities(monkeypatch, activity_data):
    monkeypatch.setattr(backend, "activities", deepcopy(activity_data))


@pytest.fixture
def client(isolated_activities):
    with TestClient(backend.app) as test_client:
        yield test_client