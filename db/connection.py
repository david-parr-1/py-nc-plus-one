import os
from collections.abc import Generator

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection

from src.utils import fetch_secret, fetch_ssm_parameter

load_dotenv()


DB_NAME = os.getenv("DB_NAME") or fetch_ssm_parameter("/nc-plus-one/DB_NAME")
DB_HOST = os.getenv("DB_HOST") or fetch_ssm_parameter("/nc-plus-one/DB_HOST")
DB_PORT = os.getenv("DB_PORT") or fetch_ssm_parameter("/nc-plus-one/DB_PORT")
DB_USERNAME = os.getenv("DB_USERNAME") or fetch_ssm_parameter(
    "/nc-plus-one/DB_USERNAME"
)
DB_SECRET_ARN = os.getenv("DB_SECRET_ARN") or fetch_ssm_parameter(
    "/nc-plus-one/DB_SECRET_ARN"
)
DB_PASSWORD = os.getenv("DB_PASSWORD") or fetch_secret(DB_SECRET_ARN).get("password")


def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
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
            password=DB_PASSWORD,
        )

        yield conn

    finally:
        if conn:
            conn.close()


def create_db_connection() -> connection:
    return psycopg2.connect(
        dbname=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USERNAME,
        password=DB_PASSWORD,
    )
