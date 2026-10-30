import json
import os
from datetime import UTC, datetime

import boto3
import psycopg2
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from moto import mock_aws
from psycopg2.extras import execute_values
from testcontainers.community.postgres import PostgresContainer

from auth.auth import hash_password
from db.connection import get_db_connection
from main import app

load_dotenv()


@pytest.fixture(scope="session")
def postgres_container():
    """
    Spins up an ephemeral Postgres container for the duration of the test session.
    """
    with PostgresContainer(image="postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def postgres_connection(postgres_container):
    conn = psycopg2.connect(
        host=postgres_container.get_container_host_ip(),
        port=postgres_container.get_exposed_port(5432),
        user=postgres_container.username,
        password=postgres_container.password,
        dbname=postgres_container.dbname,
    )
    conn.autocommit = False

    yield conn

    if conn:
        conn.close()


@pytest.fixture(scope="module", autouse=True)
def create_db_schema(postgres_connection):
    conn = postgres_connection
    with conn.cursor() as cur:
        # Drop tables if they exist
        cur.execute("DROP TABLE IF EXISTS rsvps CASCADE;")
        cur.execute("DROP TABLE IF EXISTS events CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("DROP TABLE IF EXISTS venues CASCADE;")

        # Create users table
        cur.execute(
            """
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        # Create venues table
        cur.execute(
            """
            CREATE TABLE venues (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                capacity INT
            );
            """
        )

        # Creates events table
        cur.execute(
            """
            CREATE TABLE events (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description VARCHAR(255),
                starts_at TIMESTAMPTZ NOT NULL,
                ends_at TIMESTAMPTZ NOT NULL,
                organiser_id INT NOT NULL REFERENCES users(id),
                venue_id INT NOT NULL REFERENCES venues(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

        # Create rsvps table
        cur.execute(
            """
            CREATE TABLE rsvps (
                id SERIAL PRIMARY KEY,
                attendee_id INTEGER REFERENCES users(id),
                event_id INTEGER REFERENCES events(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        conn.commit()

    yield conn

    # Teardown
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS rsvps CASCADE;")
        cur.execute("DROP TABLE IF EXISTS events CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("DROP TABLE IF EXISTS venues CASCADE;")
    conn.commit()


@pytest.fixture(scope="session")
def mock_events():
    return [
        {
            "title": "event1",
            "description": "event_description_1",
            "starts_at": datetime(2026, 1, 1, 9, 0, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 1, 1, 17, 0, 0, tzinfo=UTC).isoformat(),
            "organiser_id": 1,
            "venue_id": 1,
            "created_at": datetime(2025, 12, 31, 12, 0, 0, tzinfo=UTC).isoformat(),
        },
        {
            "title": "event2",
            "description": "event_description_2",
            "starts_at": datetime(2026, 1, 2, 9, 0, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 1, 2, 17, 0, 0, tzinfo=UTC).isoformat(),
            "organiser_id": 2,
            "venue_id": 2,
            "created_at": datetime(2025, 12, 31, 12, 0, 0, tzinfo=UTC).isoformat(),
        },
        {
            "title": "event3",
            "description": "event_description_3",
            "starts_at": datetime(2026, 1, 3, 9, 0, 0, tzinfo=UTC).isoformat(),
            "ends_at": datetime(2026, 1, 3, 17, 0, 0, tzinfo=UTC).isoformat(),
            "organiser_id": 3,
            "venue_id": 3,
            "created_at": datetime(2025, 12, 31, 12, 0, 0, tzinfo=UTC).isoformat(),
        },
    ]


@pytest.fixture(scope="module")
def mock_event_tuples(mock_events):
    return [tuple(value for value in event.values()) for event in mock_events]


@pytest.fixture(scope="module")
def add_test_data(create_db_schema, mock_event_tuples):
    conn = create_db_schema
    with conn.cursor() as cur:
        # Add dummy data to users
        users_to_insert = [
            ("user1@email.com", "user_password", "user1"),
            ("user2@email.com", "user_password", "user2"),
            ("user3@email.com", "user_password", "user3"),
        ]
        user_query = "INSERT INTO users (email, password, name) VALUES %s;"
        execute_values(cur, user_query, users_to_insert)

        # Add dummy data to venues
        venues_to_insert = [
            ("venue1", "1, High Street, Somewhere", 500),
            ("venue2", "2, High Street, Somewhere", 1500),
            ("venue3", "3, High Street, Somewhere", 2500),
        ]
        venue_query = "INSERT INTO venues (name, address, capacity) VALUES %s"
        execute_values(cur, venue_query, venues_to_insert)

        # Add dummy data to events
        events_to_insert = mock_event_tuples
        events_query = """
            INSERT INTO events (
                title, 
                description, 
                starts_at, 
                ends_at, 
                organiser_id, 
                venue_id,
                created_at
            ) 
            VALUES %s
            """
        execute_values(cur, events_query, events_to_insert)
    conn.commit()

    yield conn


@pytest.fixture(scope="module")
def client(add_test_data):
    """
    Creates a FastAPI TestClient but overrides the database connection dependencies so that the
    main app uses the same connection as the test suite, thus enabling rollback of any database
    transactions that are executed during the test suite.
    """
    add_test_data.rollback()

    def _override_get_db():
        try:
            yield add_test_data
        finally:
            pass

    app.dependency_overrides[get_db_connection] = _override_get_db

    with TestClient(app) as c:
        yield c

    add_test_data.rollback()

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user_with_hashed_password(add_test_data):
    """
    Creates a dummy user in the database with a hashed password that can be used for testing
    auth functionality.
    """
    conn = add_test_data
    with conn.cursor() as cur:
        # Define a dummy user with a hashed password using the hash_password function.
        user = {
            "name": "dummy user",
            "email": "dummy_user@email.com",
            "password": hash_password("dummypassword"),
        }
        # Convert to tuple so values can be inserted into database
        values_to_insert = (user["name"], user["email"], user["password"])
        # Insert dummy user
        cur.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            values_to_insert,
        )
        # cur.fetchone() returns a tuple but we want just the id of the newly-created user
        # (which is index [0]) so it can be deleted again in teardown
        created_user_id = cur.fetchone()[0]
        conn.commit()

    yield created_user_id

    # Teardown
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
    conn.commit()


@pytest.fixture(scope="module")
def mock_aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def mock_ssm_client(mock_aws_credentials):
    with mock_aws():
        client = boto3.client("ssm", region_name="eu-west-2")
        yield client


@pytest.fixture(scope="function")
def mock_ssm_parameter(mock_ssm_client):
    param_name = "/mock/parameter"
    param_value = "mock_value"

    mock_ssm_client.put_parameter(
        Name=param_name,
        Value=param_value,
        Type="String",
        Description="Mock parameter for testing",
        Overwrite=True,
    )

    yield {"param_name": param_name, "param_value": param_value}


@pytest.fixture(scope="function")
def mock_secretsmanager_client(mock_aws_credentials):
    with mock_aws():
        client = boto3.client("secretsmanager", region_name="eu-west-2")
        yield client


@pytest.fixture(scope="function")
def mock_secret(mock_secretsmanager_client):
    secret_name = "mock_secret"
    secret_value = json.dumps({"username": "test_user", "password": "test_password"})

    client = mock_secretsmanager_client
    client.create_secret(Name=secret_name, SecretString=secret_value)

    yield {"secret_id": secret_name, "secret_value": secret_value}
