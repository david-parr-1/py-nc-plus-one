import json

from psycopg2 import sql
from psycopg2.extensions import connection
from psycopg2.extras import execute_values

from auth.auth import hash_password
from db.connection import create_db_connection
from src.logging_config import get_logger

logger = get_logger(__name__)


def drop_db_table(connection, table_name):
    """
    Drops the specified table_name from the specified connection (to a database)
    """
    logger.info(f"Attempting to drop table '{table_name}'...")
    with connection.cursor() as curs:
        query = sql.SQL("DROP TABLE IF EXISTS {table};").format(
            table=sql.Identifier(table_name)
        )
        curs.execute(query)

    logger.info(f"Table '{table_name}' dropped successfully.")


def create_user_table(connection):
    """
    Uses the provided connection to create the users table within the database
    """
    logger.info("Attempting to create table 'users'...")
    with connection.cursor() as curs:
        query = sql.SQL(
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
        curs.execute(query)

    logger.info("Successfully created table 'users'.")


def create_venues_table(connection):
    """
    Uses the provided connection to create the venues table within the database
    """
    logger.info("Attempting to create table 'venues'...")
    with connection.cursor() as curs:
        query = sql.SQL(
            """
            CREATE TABLE venues (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                capacity INT
            );
            """
        )

        curs.execute(query)

    logger.info("Successfully created table 'venues'.")


def create_events_table(connection):
    """
    Uses the provided connection to create the events table within the database
    """
    logger.info("Attempting to create table 'events'...")
    with connection.cursor() as curs:
        query = sql.SQL(
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
        curs.execute(query)

    logger.info("Successfully created table 'events'.")


def create_rsvps_table(connection):
    """
    Uses the provided connection to create the events table within the database
    """
    logger.info("Attempting to create table 'rsvps'...")
    with connection.cursor() as curs:
        query = sql.SQL(
            """
            CREATE TABLE rsvps (
                id SERIAL PRIMARY KEY,
                attendee_id INTEGER REFERENCES users(id),
                event_id INTEGER REFERENCES events(id),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT rsvps_attendee_event_unique
                    UNIQUE (attendee_id, event_id)
            );
            """
        )
        curs.execute(query)

    logger.info("Successfully created table 'rsvps'.")


def extract_json_data(filepath):
    """
    Fetches JSON data from a file and returns it as a list of tuples. Each tuple represents one
    row from the source JSON data.
    """
    logger.info(f"Attempting to read data from '{filepath}'...")
    with open(filepath, "r") as file:
        data = json.load(file)
        logger.info(f"Successfully read data from '{filepath}'.")

        return data


def convert_dict_to_tuple_list(json_data):
    if not isinstance(json_data, list):
        raise TypeError("Input must be type list")
    values = []
    for item in json_data:
        row_tuple = tuple(item.get(key, None) for key in item)
        values.append(row_tuple)

    return values


def insert_user_data(connection):
    """
    Takes a database connection and uses it to insert extracted user data from users.json into
    the users table.
    """

    source_data = extract_json_data("db/data/users.json")
    hashed_passwords = [
        {**user, "password": hash_password(user["password"])} for user in source_data
    ]
    seed_rows = convert_dict_to_tuple_list(hashed_passwords)
    query = "INSERT INTO users (name, email, password) VALUES %s;"
    logger.info("Attempting to seed data into table 'users'...")
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)

    logger.info("Successfully seeded data into table 'users'.")


def insert_venues_data(connection):
    """
    Takes a database connection and uses it to insert extracted venues data from venues.json into
    the users table.
    """
    source_data = extract_json_data("db/data/venues.json")
    seed_rows = convert_dict_to_tuple_list(source_data)
    query = "INSERT INTO venues (name, address, capacity) VALUES %s;"
    logger.info("Attempting to seed data into table 'venues'...")
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)

    logger.info("Successfully seeded data into table 'venues'.")


def insert_events_data(connection):
    """
    Takes a database connection and uses it to insert extracted events data from events.json into
    the users table.
    """
    source_data = extract_json_data("db/data/events.json")
    seed_rows = convert_dict_to_tuple_list(source_data)
    query = "INSERT INTO events (title, description, starts_at, ends_at, organiser_id, venue_id) VALUES %s;"
    logger.info("Attempting to seed data into table 'events'...")
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)

    logger.info("Successfully seeded data into table 'events'.")


def insert_rsvps_data(connection):
    """
    Takes a database connection and uses it to insert extracted rsvps data from rsvps.json into
    the users table.
    """
    source_data = extract_json_data("db/data/rsvps.json")
    seed_rows = convert_dict_to_tuple_list(source_data)
    query = "INSERT INTO rsvps (attendee_id, event_id) VALUES %s;"
    logger.info("Attempting to seed data into table 'rsvps'...")
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)

    logger.info("Successfully seeded data into table 'rsvps'.")


def seed(conn: connection) -> None:
    logger.info("Beginning data seed script...")
    # Dependendent tables (rsvps, events) need to be dropped first as they have foreign keys
    # from the users and venues tables.
    db_tables = ["rsvps", "events", "users", "venues"]

    # Drop users and venues tables if they already exists
    with conn:
        for table in db_tables:
            drop_db_table(conn, table)

        # Create users table
        create_user_table(conn)
        create_venues_table(conn)
        create_events_table(conn)
        create_rsvps_table(conn)

        # Insert the test user data into the users table
        insert_user_data(conn)
        insert_venues_data(conn)
        insert_events_data(conn)
        insert_rsvps_data(conn)

    logger.info("Data seeded successfully to database.")


if __name__ == "__main__":
    conn = create_db_connection()
    seed(conn)
