import psycopg2
import os
from dotenv import load_dotenv
from typing import Generator
from psycopg2.extensions import connection


load_dotenv()


DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_db_connection() -> Generator[psycopg2.extensions.connection]:
    """
    Establishes a connection to a database using credentials provided as arguments. The connection
    is yielded for use elsewhere.
    """
    
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, 
            host=DB_HOST, 
            port=DB_PORT, 
            user=DB_USERNAME, 
            password=DB_PASSWORD
        )

        yield conn

    finally:
        if conn:
            conn.close()
