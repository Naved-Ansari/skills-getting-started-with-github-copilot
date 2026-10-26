from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


TEST_ACTIVITY = "Soccer Club"
TEST_EMAIL = "test-student@mergington.edu"


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities_returns_activity_details_and_participants(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()[TEST_ACTIVITY]["participants"] == []
    assert response.json()[TEST_ACTIVITY]["max_participants"] == 24


def test_signup_adds_participant(client):
    response = client.post(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": TEST_EMAIL},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {TEST_EMAIL} for {TEST_ACTIVITY}"
    }
    assert activities[TEST_ACTIVITY]["participants"] == [TEST_EMAIL]


def test_get_activities_reflects_signup_and_unregister(client):
    signup_url = f"/activities/{TEST_ACTIVITY}/signup"

    client.post(signup_url, params={"email": TEST_EMAIL})
    signed_up_activities = client.get("/activities").json()
    assert signed_up_activities[TEST_ACTIVITY]["participants"] == [TEST_EMAIL]

    client.delete(signup_url, params={"email": TEST_EMAIL})
    unregistered_activities = client.get("/activities").json()
    assert unregistered_activities[TEST_ACTIVITY]["participants"] == []


def test_signup_rejects_duplicate_participant(client):
    signup_url = f"/activities/{TEST_ACTIVITY}/signup"
    client.post(signup_url, params={"email": TEST_EMAIL})

    response = client.post(signup_url, params={"email": TEST_EMAIL})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[TEST_ACTIVITY]["participants"] == [TEST_EMAIL]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": TEST_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    signup_url = f"/activities/{TEST_ACTIVITY}/signup"
    client.post(signup_url, params={"email": TEST_EMAIL})

    response = client.delete(signup_url, params={"email": TEST_EMAIL})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {TEST_EMAIL} from {TEST_ACTIVITY}"
    }
    assert activities[TEST_ACTIVITY]["participants"] == []


def test_unregister_preserves_other_participants(client):
    signup_url = f"/activities/{TEST_ACTIVITY}/signup"
    other_email = "another-student@mergington.edu"
    client.post(signup_url, params={"email": TEST_EMAIL})
    client.post(signup_url, params={"email": other_email})

    response = client.delete(signup_url, params={"email": TEST_EMAIL})

    assert response.status_code == 200
    assert activities[TEST_ACTIVITY]["participants"] == [other_email]


def test_unregister_rejects_nonparticipant(client):
    response = client.delete(
        f"/activities/{TEST_ACTIVITY}/signup",
        params={"email": TEST_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": TEST_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
