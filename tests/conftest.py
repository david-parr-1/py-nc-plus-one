import pytest
from db.connection import get_db_connection
from psycopg2 import sql
from psycopg2.extras import execute_values
from datetime import datetime, timezone


@pytest.fixture(scope="session")
def database_with_schema():
    with get_db_connection() as conn:
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


@pytest.fixture(scope="function")
def add_test_data(database_with_schema):
    conn = database_with_schema
    with conn.cursor() as cur:
        # Add dummy data to users
        users_to_insert = [
            ("user1@email.com", "user_password", "user1"),
            ("user2@email.com", "user_password", "user2"),
            ("user3@email.com", "user_password", "user3")
        ]
        user_query = "INSERT INTO users (email, password, name) VALUES %s;"
        execute_values(cur, user_query, users_to_insert)

        # Add dummy data to venues
        venues_to_insert = [
                ('venue1', '1, High Street, Somewhere', 500),
                ('venue2', '2, High Street, Somewhere', 1500),
                ('venue3', '3, High Street, Somewhere', 2500)
        ]
        venue_query = "INSERT INTO venues (name, address, capacity) VALUES %s"
        execute_values(cur, venue_query, venues_to_insert)

        # Add dummy data to events
        events_to_insert = [
                (
                    'event1', 
                    'event_description_1', 
                    datetime(2026, 6, 24, 9, 0, 0, tzinfo=timezone.utc), 
                    datetime(2026, 6, 24, 17, 0, 0, tzinfo=timezone.utc), 
                    1, 
                    1,
                    datetime(2026, 6, 22, 9, 0, 0, tzinfo=timezone.utc), 
                ),
                (
                    'event2', 
                    'event_description_2', 
                    datetime(2026, 6, 25, 9, 0, 0, tzinfo=timezone.utc), 
                    datetime(2026, 6, 25, 17, 0, 0, tzinfo=timezone.utc), 
                    2, 
                    2,
                    datetime(2026, 6, 22, 9, 0, 0, tzinfo=timezone.utc), 
                ),
                (
                    'event3', 
                    'event_description_3', 
                    datetime(2026, 6, 26, 9, 0, 0, tzinfo=timezone.utc), 
                    datetime(2026, 6, 26, 17, 0, 0, tzinfo=timezone.utc), 
                    3, 
                    3,
                    datetime(2026, 6, 22, 9, 0, 0, tzinfo=timezone.utc), 
                )
        ]
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

    yield

    # Teardown
    db_tables = ["rsvps", "events", "users", "venues"]

    with conn.cursor() as cur:
        # Delete all data inserted into tables
        for table in db_tables:
            # TRUNCATE TABLE is used to quickly delete any dummy rows that have been added to
            # the test database's tables. The "RESTART IDENTITY" parameter causes the tables
            # to reset their id serialisation to 1.
            query = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE;").format(sql.Identifier(table))
            cur.execute(query)

