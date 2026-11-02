from copy import deepcopy

import pytest


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_list_activities(client, activity_data):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activity_data


@pytest.mark.parametrize("activity_name", ["Chess Club", "Art Club"])
def test_signup_updates_only_selected_activity(client, activity_data, activity_name):
    email = "new+student@example.com"
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    expected = deepcopy(activity_data)
    expected[activity_name]["participants"].append(email)
    assert client.get("/activities").json() == expected


def test_signup_rejects_existing_participant(client, activity_data):
    response = client.post(
        "/activities/Chess Club/signup", params={"email": "first@example.com"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json() == activity_data


def test_signup_rejects_unknown_activity(client, activity_data):
    response = client.post(
        "/activities/Missing Club/signup", params={"email": "new@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == activity_data


def test_unregister_updates_only_selected_participant(client, activity_data):
    email = "first@example.com"
    response = client.delete(
        "/activities/Chess Club/unregister", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    expected = deepcopy(activity_data)
    expected["Chess Club"]["participants"].remove(email)
    assert client.get("/activities").json() == expected


@pytest.mark.parametrize(
    ("activity_name", "email", "detail"),
    [
        ("Missing Club", "first@example.com", "Activity not found"),
        ("Chess Club", "missing@example.com", "Student is not signed up for this activity"),
        ("Art Club", "missing@example.com", "Student is not signed up for this activity"),
    ],
)
def test_unregister_rejects_missing_signup(
    client, activity_data, activity_name, email, detail
):
    response = client.delete(
        f"/activities/{activity_name}/unregister", params={"email": email}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": detail}
    assert client.get("/activities").json() == activity_data


@pytest.mark.parametrize(
    ("method", "action"), [("POST", "signup"), ("DELETE", "unregister")]
)
def test_email_is_required(client, activity_data, method, action):
    response = client.request(method, f"/activities/Chess Club/{action}")

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == activity_data


def test_signup_unregister_and_signup_again(client, activity_data):
    email = "returning+student@example.com"
    signup_url = "/activities/Chess Club/signup"
    unregister_url = "/activities/Chess Club/unregister"
    params = {"email": email}
    expected = deepcopy(activity_data)
    expected["Chess Club"]["participants"].append(email)

    assert client.post(signup_url, params=params).status_code == 200
    assert client.get("/activities").json() == expected

    duplicate = client.post(signup_url, params=params)
    assert duplicate.status_code == 400
    assert duplicate.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json() == expected

    assert client.delete(unregister_url, params=params).status_code == 200
    assert client.get("/activities").json() == activity_data
    assert client.delete(unregister_url, params=params).status_code == 404
    assert client.get("/activities").json() == activity_data

    assert client.post(signup_url, params=params).status_code == 200
    assert client.get("/activities").json() == expected