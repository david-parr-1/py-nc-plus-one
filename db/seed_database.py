import json
from psycopg2 import sql
from db.connection import get_db_connection
from db.credentials import dbname, host, password


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
            )
            """
        )

        curs.execute(query)


def extract_json_data(filepath):
    """
    Fetches JSON data from a file and returns it in list format
    """
    with open(filepath, "r") as file:
        data = json.load(file)
        return data
    

def make_sql_inserts(extracted_data):
    """
    Takes a list of data rows which have been extracted from the source data json files
    and processes them into a format that allows their concatenation into an SQL string for
    insert into the database
    """
    # An error should be raised if the input is not a list
    if not isinstance(extracted_data, list):
        raise TypeError(f"Expected input type list. Got {type(extracted_data)}.")
    
    # An empty list should be returned if the input list is empty
    if not extracted_data:
        return []

    formatted_rows = []
    for row in extracted_data:
        row_values = [f"'{row[key]}'" if isinstance(row[key], str) else row[key] for key in row]
        # row_values = [row[key] for key in row]
        row_as_string = ", ".join(row_values)
        sql_format_row = f"({row_as_string})"
        formatted_rows.append(sql_format_row)
    
    all_rows_formatted = ", ".join(formatted_rows)
    return all_rows_formatted


def insert_user_data(connection):
    """
    Takes a database connection and a fully formatted SQL query and executes it to insert user data
    into the database
    """
    extracted_data = extract_json_data("db/data/users.json")
    rows_to_insert = make_sql_inserts(extracted_data)
    query = f"INSERT INTO users (name, email, password) VALUES {rows_to_insert}"
    # sql_insert_string = create_insert_sql_string(sql_values)
    with connection.cursor() as curs:
        curs.execute(query)


def seed():
    with get_db_connection(dbname=dbname, host=host, password=password) as conn:
    
        db_tables = ["users", "venues"]
        
        # Drop users and venues tables if they already exists
        for table in db_tables:
            drop_db_table(conn, table)

        # Create users table
        create_user_table(conn)
        create_venues_table(conn)
        
        # Insert the test user data into the users table
        insert_user_data(conn)

if __name__ == "__main__":
    seed()
