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
    client, user_with_hashed_password, test_jwt_config
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


def test_add_rsvp_returns_created_rsvp(client, mock_valid_token, rsvp_table_clean):
    conn = rsvp_table_clean["conn"]
    attendee_id = rsvp_table_clean["attendee_id"]
    event_id = rsvp_table_clean["event_id"]

    try:
        response = client.post(
            f"/api/events/{event_id}/rsvp",
            headers={"Authorization": f"Bearer {mock_valid_token}"},
        )

        assert response.status_code == 201

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, created_at
                FROM rsvps
                WHERE attendee_id = %s AND event_id = %s;
                """,
                (attendee_id, event_id),
            )
            created_rsvp = cur.fetchone()

        assert created_rsvp is not None

        expected_response = {
            "rsvp": {
                "id": created_rsvp[0],
                "attendee_id": attendee_id,
                "event_id": event_id,
                "created_at": created_rsvp[1],
            }
        }

        response_body = response.json()

        # Timestamp in response_body is converted to datetime object
        # for cleaner comparison with created_rsvp[1] which is returned
        # from the database as a datetime object.
        response_body["rsvp"]["created_at"] = datetime.fromisoformat(
            response_body["rsvp"]["created_at"]
        )

        assert response_body == expected_response

    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM rsvps WHERE attendee_id = %s AND event_id = %s;",
                (attendee_id, event_id),
            )
        conn.commit()


def test_add_rsvp_rejects_duplicated_rsvp(
    client, mock_valid_token, rsvp_table_with_dupe
):
    try:
        conn = rsvp_table_with_dupe["conn"]
        attendee_id = rsvp_table_with_dupe["attendee_id"]
        event_id = rsvp_table_with_dupe["event_id"]

        response = client.post(
            f"/api/events/{event_id}/rsvp",
            headers={"Authorization": f"Bearer {mock_valid_token}"},
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "RSVP already registered"

    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM rsvps WHERE attendee_id = %s AND event_id = %s;",
                (attendee_id, event_id),
            )
        conn.commit()


def test_add_rsvp_returns_error_401_for_invalid_token(
    client, mock_invalid_token, rsvp_table_with_dupe
):
    event_id = rsvp_table_with_dupe["event_id"]
    response = client.post(
        f"/api/events/{event_id}/rsvp",
        headers={"Authorization": f"Bearer {mock_invalid_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token is invalid"


def test_add_rsvp_returns_error_401_for_expired_token(
    client, mock_expired_token, rsvp_table_with_dupe
):
    event_id = rsvp_table_with_dupe["event_id"]
    response = client.post(
        f"/api/events/{event_id}/rsvp",
        headers={"Authorization": f"Bearer {mock_expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_add_rsvp_returns_error_404_for_non_existent_event(client, mock_valid_token):
    response = client.post(
        "/api/events/9999/rsvp",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_delete_rsvp_returns_status_code_204_for_successful_deletion(
    client, mock_valid_token, rsvp_table_with_dupe
):
    attendee_id = rsvp_table_with_dupe["attendee_id"]
    event_id = rsvp_table_with_dupe["event_id"]
    conn = rsvp_table_with_dupe["conn"]

    response = client.delete(
        f"/api/events/{event_id}/rsvp/me",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
    )

    assert response.status_code == 204

    with conn.cursor() as cur:
        query = """
        SELECT id
        FROM rsvps
        WHERE attendee_id = %s AND event_id = %s;
        """

        cur.execute(query, (attendee_id, event_id))

        assert cur.fetchone() is None


def test_delete_rsvp_returns_error_404_for_non_existent_event(
    client, mock_valid_token, rsvp_table_clean
):
    event_id = rsvp_table_clean["event_id"]

    response = client.delete(
        f"/api/events/{event_id}/rsvp/me",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == ("RSVP not found")


def test_delete_rsvp_returns_error_401_for_invalid_token(
    client, mock_invalid_token, rsvp_table_with_dupe
):
    event_id = rsvp_table_with_dupe["event_id"]
    response = client.delete(
        f"/api/events/{event_id}/rsvp/me",
        headers={"Authorization": f"Bearer {mock_invalid_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token is invalid"


def test_delete_rsvp_returns_error_401_for_expired_token(
    client, mock_expired_token, rsvp_table_with_dupe
):
    event_id = rsvp_table_with_dupe["event_id"]
    response = client.delete(
        f"/api/events/{event_id}/rsvp/me",
        headers={"Authorization": f"Bearer {mock_expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_create_event_returns_status_code_201_for_successful_creation(
    client, mock_valid_token, mock_new_event, add_test_data
):
    response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
        json=mock_new_event,
    )

    assert response.status_code == 201

    with add_test_data.cursor() as cur:
        cur.execute(
            """
            SELECT
                id,
                created_at
            FROM events
            WHERE title = %s
            AND description = %s;
            """,
            (mock_new_event["title"], mock_new_event["description"]),
        )

        result = cur.fetchone()

    expected_response = {
        "event": {
            "id": result[0],
            "title": mock_new_event["title"],
            "description": mock_new_event["description"],
            "starts_at": mock_new_event["starts_at"],
            "ends_at": mock_new_event["ends_at"],
            "venue_id": mock_new_event["venue_id"],
            "organiser_id": 1,  # id 1 Maps to user_id in `mock_valid_token`,
            "created_at": result[1].isoformat(),
        }
    }

    assert response.json() == expected_response


@pytest.mark.parametrize(
    "missing_field", ["title", "description", "starts_at", "ends_at", "venue_id"]
)
def test_create_event_rejects_missing_field_in_payload(
    missing_field, client, mock_valid_token, mock_new_event
):
    payload = mock_new_event
    payload.pop(missing_field)
    expected_response = {
        "error": [
            {"type": "missing", "loc": ["body", missing_field], "msg": "Field required"}
        ]
    }
    response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
        json=payload,
    )

    assert response.status_code == 400
    assert response.json() == expected_response


def test_create_event_rejects_invalid_formats(client, mock_valid_token):
    payload = {
        "title": 12345,
        "description": 67890,
        "starts_at": "2026-11-23",
        "ends_at": 12345,
        "venue_id": "test",
    }

    expected_response = {
        "error": [
            {
                "type": "string_type",
                "loc": ["body", "title"],
                "msg": "Input should be a valid string",
            },
            {
                "type": "string_type",
                "loc": ["body", "description"],
                "msg": "Input should be a valid string",
            },
            {
                "type": "value_error",
                "loc": ["body", "starts_at"],
                "msg": "Value error, must be an ISO 8601 datetime string",
            },
            {
                "type": "value_error",
                "loc": ["body", "ends_at"],
                "msg": "Value error, must be an ISO 8601 datetime string",
            },
            {
                "type": "int_type",
                "loc": ["body", "venue_id"],
                "msg": "Input should be a valid integer",
            },
        ]
    }

    response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
        json=payload,
    )

    assert response.status_code == 400
    assert response.json() == expected_response


def test_create_event_returns_error_401_for_invalid_token(
    client, mock_invalid_token, mock_new_event
):
    response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {mock_invalid_token}"},
        json=mock_new_event,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token is invalid"


def test_create_event_returns_error_401_for_expired_token(
    client, mock_expired_token, mock_new_event
):
    response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {mock_expired_token}"},
        json=mock_new_event,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_update_event_succeeds_with_full_payload(
    client, mock_valid_token, mock_pre_existing_event, mock_new_event
):
    event_id = mock_pre_existing_event["id"]
    created_at = mock_pre_existing_event["created_at"]
    payload = mock_new_event.copy()
    # The fixture `mock_new_event` which is used to update the pre-existing record
    # in the `events` table does not contain the `id`, `organiser_id` or `created_at`
    # fields. They need to be added manually to `payload` here to enable comparison
    # with the payload returned by `update_event()` since they are included in the
    # return of `update_event()`. `organiser_id` value is set to 1 since this aligns
    # with the `organiser_id` used to spin up `mock_valid_token.
    expected_response = {
        **payload,
        "id": event_id,
        "organiser_id": 1,
        "created_at": created_at,
    }

    response = client.patch(
        f"/api/events/{event_id}",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["event"] == expected_response


@pytest.mark.parametrize(
    "omitted_field", ["title", "description", "starts_at", "ends_at", "venue_id"]
)
def test_update_event_succeeds_with_omitted_optional_fields_in_payload(
    omitted_field, client, mock_valid_token, mock_pre_existing_event, mock_new_event
):
    event_id = mock_pre_existing_event["id"]
    created_at = mock_pre_existing_event["created_at"]
    payload = mock_new_event.copy()
    payload.pop(omitted_field)
    # The fixture `mock_new_event` which is used to update the pre-existing record
    # in the `events` table does not contain the `id`, `organiser_id` or `created_at`
    # fields. They need to be added manually to `payload` here to enable comparison
    # with the payload returned by `update_event()` since they are included in the
    # return of `update_event()`. `organiser_id` value is set to 1 since this aligns
    # with the `organiser_id` used to spin up `mock_valid_token. The `omitted_field`
    # also needs to be added to the expected response since the endpoint will return
    # this with the existing unmodified value.
    expected_response = {
        **payload,
        "id": event_id,
        "organiser_id": 1,
        "created_at": created_at,
        omitted_field: mock_pre_existing_event[omitted_field],
    }

    response = client.patch(
        f"/api/events/{event_id}",
        headers={"Authorization": f"Bearer {mock_valid_token}"},
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["event"] == expected_response
