from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app, follow_redirects=False) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data_without_caching(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_unknown_activity_does_not_change_data(client):
    original_activities = deepcopy(activities)

    response = client.post(
        "/activities/Unknown/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == original_activities


def test_signup_requires_email(client):
    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422


def test_unregister_removes_only_selected_participant(client):
    original_activities = deepcopy(activities)

    response = client.delete(
        "/activities/Chess%20Club/unregister",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    expected = deepcopy(original_activities)
    expected["Chess Club"]["participants"].remove("michael@mergington.edu")
    assert client.get("/activities").json() == expected


def test_unregister_unknown_activity_does_not_change_data(client):
    original_activities = deepcopy(activities)

    response = client.delete(
        "/activities/Unknown/unregister", params={"email": "michael@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities == original_activities


def test_unregister_nonparticipant_does_not_change_data(client):
    original_activities = deepcopy(activities)

    response = client.delete(
        "/activities/Chess%20Club/unregister", params={"email": "unknown@example.com"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities == original_activities


def test_unregister_requires_email(client):
    response = client.delete("/activities/Chess%20Club/unregister")

    assert response.status_code == 422


def test_signup_unregister_and_signup_again_with_special_characters(client):
    email = "student+art&music@example.com"
    signup_url = "/activities/Art%20Club/signup"
    unregister_url = "/activities/Art%20Club/unregister"

    signup_response = client.post(signup_url, params={"email": email})
    duplicate_signup_response = client.post(signup_url, params={"email": email})
    unregister_response = client.delete(unregister_url, params={"email": email})

    assert signup_response.status_code == 200
    assert signup_response.json() == {"message": f"Signed up {email} for Art Club"}
    assert duplicate_signup_response.status_code == 400
    assert unregister_response.status_code == 200
    assert activities["Art Club"]["participants"] == []
    assert client.delete(unregister_url, params={"email": email}).status_code == 400
    assert client.post(signup_url, params={"email": email}).status_code == 200


def test_signup_is_visible_in_fresh_uncached_activity_list(client):
    email = "newstudent@mergington.edu"

    response = client.post(
        "/activities/Chess%20Club/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    assert response.status_code == 200
    assert activities_response.headers["cache-control"] == "no-store"
    assert email in activities_response.json()["Chess Club"]["participants"]


def test_static_assets_must_be_revalidated(client):
    for path in ("/static/index.html", "/static/app.js", "/static/styles.css"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
