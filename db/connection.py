import psycopg2
from db.credentials import dbname, host, password


def get_db_connection(dbname, host, password):
    """
    Establishes a connection to a database using credentials provided as arguments. The connection
    is returned for use elsewhere.
    """
    conn = psycopg2.connect(dbname=dbname, host=host, password=password)
    return conn
