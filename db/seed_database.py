import json
from psycopg2 import sql
from psycopg2.extras import execute_values
from db.connection import get_db_connection
from db.credentials import dbname, host, password
from auth.auth import hash_password


def drop_db_table(connection, table_name):
    """
    Drops the specified table_name from the specified connection (to a database)
    """
    with connection.cursor() as curs:
        query = sql.SQL("DROP TABLE IF EXISTS {table};").format(table=sql.Identifier(table_name))
        curs.execute(query)


def create_user_table(connection):
    """
    Uses the provided connection to create the users table within the database
    """
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


def create_venues_table(connection):
    """
    Uses the provided connection to create the venues table within the database
    """
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


def create_events_table(connection):
    """
    Uses the provided connection to create the events table within the database
    """
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


def create_rsvps_table(connection):
    """
    Uses the provided connection to create the events table within the database
    """
    with connection.cursor() as curs:
        query =sql.SQL(
            """
            CREATE TABLE rsvps (
                id SERIAL PRIMARY KEY,
                attendee_id INTEGER REFERENCES users(id),
                event_id INTEGER REFERENCES events(id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        curs.execute(query)    


def extract_json_data(filepath):
    """
    Fetches JSON data from a file and returns it as a list of tuples. Each tuple represents one
    row from the source JSON data.
    """

    with open(filepath, "r") as file:
        data = json.load(file)

        return data
    

def format_json_as_values(json_data):
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
    hashed_passwords = [{**user, "password": hash_password(user["password"])} for user in source_data]
    seed_rows = format_json_as_values(hashed_passwords)
    query = "INSERT INTO users (name, email, password) VALUES %s;"
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)


def insert_venues_data(connection):
    """
    Takes a database connection and uses it to insert extracted venues data from venues.json into 
    the users table.
    """
    source_data = extract_json_data("db/data/venues.json")
    seed_rows = format_json_as_values(source_data)
    query = "INSERT INTO venues (name, address, capacity) VALUES %s;"
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)


def insert_events_data(connection):
    """
    Takes a database connection and uses it to insert extracted events data from events.json into 
    the users table.
    """
    source_data = extract_json_data("db/data/events.json")
    seed_rows = format_json_as_values(source_data)
    query = "INSERT INTO events (title, description, starts_at, ends_at, organiser_id, venue_id) VALUES %s;"
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)


def insert_rsvps_data(connection):
    """
    Takes a database connection and uses it to insert extracted rsvps data from rsvps.json into 
    the users table.
    """
    source_data = extract_json_data("db/data/rsvps.json")
    seed_rows = format_json_as_values(source_data)
    query = "INSERT INTO rsvps (attendee_id, event_id) VALUES %s;"
    with connection.cursor() as curs:
        execute_values(curs, query, seed_rows)


def seed():
    with get_db_connection() as conn:
    
        # Dependendent tables (rsvps, events) need to be dropped first as they have foreign keys
        # from the users and venues tables.
        db_tables = ["rsvps", "events", "users", "venues"]
        
        # Drop users and venues tables if they already exists
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

if __name__ == "__main__":
    seed()
