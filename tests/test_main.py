from datetime import UTC, datetime
from unittest.mock import patch

import pytest


def test_app_handles_invalid_path(client):
    response = client.get("/invalid_path")
    assert response.status_code == 404


def test_get_api_events_returns_status_200_when_successful(client, add_test_data):
    response = client.get("/api/events")
    assert response.status_code == 200


def test_get_api_events_returns_dict_with_events_key(client, add_test_data):
    response = client.get("/api/events")
    response_body = response.json()
    assert type(response_body) == dict
    assert response_body.get("events", None) != None


def test_get_api_events_key_contains_list_of_events(client, add_test_data):
    response = client.get("/api/events")
    response_body = response.json()
    assert type(response_body.get("events", None)) == list


def test_get_api_events_returns_expected_number_of_rows(client, add_test_data):
    response = client.get("/api/events")
    response_body = response.json()
    assert len(response_body.get("events", None)) == 3


def test_get_api_events_returns_all_rows(client, mock_events, add_test_data):
    expected_payload = [
        {
            "id": 1,
            "title": "event1",
            "starts_at": datetime(2026, 1, 1, 9, 0, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 1, 1, 17, 0, 0, tzinfo=UTC).isoformat(),
            "location": "venue1",
        },
        {
            "id": 2,
            "title": "event2",
            "starts_at": datetime(2026, 1, 2, 9, 0, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 1, 2, 17, 0, 0, tzinfo=UTC).isoformat(),
            "location": "venue2",
        },
        {
            "id": 3,
            "title": "event3",
            "starts_at": datetime(2026, 1, 3, 9, 0, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 1, 3, 17, 0, 0, tzinfo=UTC).isoformat(),
            "location": "venue3",
        },
    ]

    response = client.get("/api/events")
    response_payload = response.json()["events"]

    assert response_payload == expected_payload


def test_get_api_event_returns_404_for_non_existent_id(client, add_test_data):
    response = client.get("/api/events/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_get_api_event_returns_400_for_invalid_id(client, add_test_data):
    response = client.get("/api/events/abc")
    assert response.status_code == 400


def test_get_api_event_returns_200_for_valid_id(client, add_test_data):
    response = client.get("/api/events/1")
    assert response.status_code == 200


def test_get_api_event_returns_dict_with_event_key(client, add_test_data):
    response = client.get("/api/events/1")
    response_body = response.json()
    assert type(response_body) == dict
    assert response_body.get("event", None) != None


def test_get_api_event_returns_correct_data_for_valid_id(client, add_test_data):
    expected_payload = {
        "id": 1,
        "title": "event1",
        "description": "event_description_1",
        "starts_at": datetime(2026, 1, 1, 9, 0, 0, tzinfo=UTC).isoformat(),
        "ends_at": datetime(2026, 1, 1, 17, 0, 0, tzinfo=UTC).isoformat(),
        "location": "venue1",
        "address": "1, High Street, Somewhere",
        "capacity": 500,
        "created_at": datetime(2025, 12, 31, 12, 0, 0, tzinfo=UTC).isoformat(),
    }
    response = client.get("/api/events/1")
    response_payload = response.json()["event"]

    assert response_payload == expected_payload


def test_auth_login_returns_400_for_missing_password(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"email": "dummy_user@email.com"})
    assert response.status_code == 400


def test_auth_login_returns_400_for_missing_email(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"password": "dummypassword"})
    assert response.status_code == 400


def test_auth_login_returns_400_for_both_fields_missing(
    client, user_with_hashed_password
):
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 400


def test_auth_login_returns_401_for_invalid_email(client, user_with_hashed_password):
    response = client.post(
        "/api/auth/login",
        json={"email": "user999@email.com", "password": "dummypassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_auth_login_returns_401_for_incorrect_password(
    client, user_with_hashed_password
):
    response = client.post(
        "/api/auth/login",
        json={"email": "dummy_user@email.com", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_auth_login_returns_200_for_valid_credentials(
    client, user_with_hashed_password
):
    response = client.post(
        "/api/auth/login",
        json={"email": "dummy_user@email.com", "password": "dummypassword"},
    )
    assert response.status_code == 200


def test_healthcheck_returns_status_code_200(client):
    response = client.get("/api/healthcheck")
    assert response.status_code == 200


def test_healthcheck_returns_correct_response(client):
    expected_response = {"Healthcheck": "Running"}
    response = client.get("/api/healthcheck")
    assert response.json()["detail"] == expected_response


@pytest.mark.parametrize(
    "incomplete_input",
    [
        {"email": "dummy@email.com", "password": "dummypassword"},
        {"name": "Dummy Name", "password": "dummypassword"},
        {"name": "Dummy Name", "email": "dummy@email.com"},
    ],
)
def test_register_user_returns_status_400_for_incomplete_request(
    client, incomplete_input
):
    response = client.post("/api/auth/register", json=incomplete_input)

    assert response.status_code == 400
    assert "error" in response.json()


def test_register_user_returns_status_409_for_existing_user(
    client, user_with_hashed_password
):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "dummy user",
            "email": "dummy_user@email.com",
            "password": "dummypassword",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


@patch("main.datetime")
def test_register_user_returns_status_201_for_successful_registration(
    mock_datetime, client, user_with_hashed_password
):
    fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

    mock_datetime.now.return_value = fixed_timestamp

    response = client.post(
        "/api/auth/register",
        json={
            "name": "New User",
            "email": "new_user@email.com",
            "password": "newpassword",
            "created_at": fixed_timestamp.isoformat(),
        },
    )

    expected_user_id = user_with_hashed_password + 1
    expected_response = {
        "user": {
            "id": expected_user_id,
            "name": "New User",
            "email": "new_user@email.com",
            "created_at": fixed_timestamp.isoformat(),
        }
    }

    assert response.status_code == 201
    assert response.json() == expected_response
