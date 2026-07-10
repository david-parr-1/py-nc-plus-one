from datetime import datetime, timezone


def test_app_handles_invalid_path(client):
    response = client.get(f"/invalid_path")
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


def test_get_api_events_returns_all_rows(client, add_test_data):
    expected_response = [
        {
            "id": 1,
            "title": "event1",
            "starts_at": datetime(2026, 6, 24, 9, 0, 0, tzinfo=timezone.utc),
            "ends_at": datetime(2026, 6, 24, 17, 0, 0, tzinfo=timezone.utc),
            "location": "venue1"
        },
        {
            "id": 2,
            "title": "event2",
            "starts_at": datetime(2026, 6, 25, 9, 0, 0, tzinfo=timezone.utc),
            "ends_at": datetime(2026, 6, 25, 17, 0, 0, tzinfo=timezone.utc),
            "location": "venue2"
        },
        {
            "id": 3,
            "title": "event3",
            "starts_at": datetime(2026, 6, 26, 9, 0, 0, tzinfo=timezone.utc),
            "ends_at": datetime(2026, 6, 26, 17, 0, 0, tzinfo=timezone.utc),
            "location": "venue3"
        }
    ]

    response = client.get("/api/events")
    # The API response returns the date fields in ISO8601 format string so these need to be 
    # converted back to Python-native datetime format to enable proper assertion against the
    # expected values. 
    responses = response.json()["events"]
    cleaned_events = []
    for record in responses:
        cleaned_event = {
            **record,
            "starts_at": datetime.fromisoformat(record["starts_at"].replace("Z", "+00:00")),
            "ends_at": datetime.fromisoformat(record["ends_at"].replace("Z", "+00:00")),
        }
        cleaned_events.append(cleaned_event)
    
    assert cleaned_events == expected_response


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
    expected_response = {
        "id": 1,
        "title": "event1",
        "description": "event_description_1",
        "starts_at": datetime(2026, 6, 24, 9, 0, 0, tzinfo=timezone.utc),
        "ends_at": datetime(2026, 6, 24, 17, 0, 0, tzinfo=timezone.utc),
        "location": "venue1",
        "address": "1, High Street, Somewhere",
        "capacity": 500,
        "created_at": datetime(2026, 6, 22, 9, 0, 0, tzinfo=timezone.utc)
    }
    response = client.get("/api/events/1")
    response_body = response.json()["event"]
    cleaned_response = {
        **response_body,
        "starts_at": datetime.fromisoformat(response_body["starts_at"].replace("Z", "+00:00")),
        "ends_at": datetime.fromisoformat(response_body["ends_at"].replace("Z", "+00:00")),
        "created_at": datetime.fromisoformat(response_body["created_at"].replace("Z", "+00:00"))
    }
    assert cleaned_response == expected_response


def test_user_creation_fixture_inserts_dummy_user(user_with_hashed_password):
    assert user_with_hashed_password == 1


def test_auth_login_returns_400_for_missing_password(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"email": "user1@email.com"})
    assert response.status_code == 400


def test_auth_login_returns_400_for_missing_email(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"password": "userpassword"})
    assert response.status_code == 400


def test_auth_login_returns_400_for_both_fields_missing(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 400


def test_auth_login_returns_401_for_invalid_email(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"email": "user999@email.com", "password": "userpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_auth_login_returns_401_for_incorrect_password(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"email": "user1@email.com", "password": "incorrectpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_auth_login_returns_200_for_valid_credentials(client, user_with_hashed_password):
    response = client.post("/api/auth/login", json={"email": "user1@email.com", "password": "userpassword"})
    assert response.status_code == 200


def test_healthcheck_returns_status_code_200(client):
    response = client.get("/api/healthcheck")
    assert response.status_code == 200


def test_healthcheck_returns_correct_response(client):
    expected_response = {"Healthcheck": "Running"}
    response = client.get("/api/healthcheck")
    assert response.json()["detail"] == expected_response
