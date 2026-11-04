from collections.abc import Generator

import psycopg2
from psycopg2.extensions import connection

from db.configuration import Config


def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Establishes a connection to a database using credentials provided as arguments. The connection
    is yielded for use elsewhere.
    """

    try:
        config = Config.get_config()
        conn = psycopg2.connect(
            dbname=config.db_name,
            host=config.db_host,
            port=config.db_port,
            user=config.db_username,
            password=config.db_password,
        )

        yield conn

    finally:
        if conn:
            conn.close()


def create_db_connection() -> connection:
    config = Config.get_config()
    return psycopg2.connect(
        dbname=config.db_name,
        host=config.db_host,
        port=config.db_port,
        user=config.db_username,
        password=config.db_password,
    )
