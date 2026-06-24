import psycopg2
import os
from dotenv import load_dotenv


load_dotenv()


DB_NAME = os.getenv("DB_NAME")
HOST = os.getenv("HOST")
PASSWORD = os.getenv("PASSWORD")


def get_db_connection():
    """
    Establishes a connection to a database using credentials provided as arguments. The connection
    is returned for use elsewhere.
    """
    conn = psycopg2.connect(dbname=DB_NAME, host=HOST, password=PASSWORD)
    return conn
