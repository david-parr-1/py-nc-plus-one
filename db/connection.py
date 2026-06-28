import psycopg2
import os
from dotenv import load_dotenv
from typing import Generator
from psycopg2.extensions import connection


load_dotenv()


DB_NAME = os.getenv("DB_NAME")
HOST = os.getenv("HOST")
PASSWORD = os.getenv("PASSWORD")


def get_db_connection() -> Generator[psycopg2.extensions.connection]:
    """
    Establishes a connection to a database using credentials provided as arguments. The connection
    is yielded for use elsewhere.
    """
    
    try:
        conn = psycopg2.connect(dbname=DB_NAME, host=HOST, password=PASSWORD)
        yield conn
    finally:
        if conn:
            conn.close()
