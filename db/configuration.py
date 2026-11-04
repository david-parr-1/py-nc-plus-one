import os

from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

from src.utils import fetch_secret, fetch_ssm_parameter


class DBConfig:
    _instance: "DBConfig | None" = None

    def __init__(self) -> None:
        load_dotenv()
        try:
            self.aws_region = os.getenv("AWS_REGION", "eu-west-2")
            self.db_host = os.getenv("DB_HOST") or fetch_ssm_parameter(
                "/nc-plus-one/DB_HOST"
            )
            self.db_port = os.getenv("DB_PORT") or fetch_ssm_parameter(
                "/nc-plus-one/DB_PORT"
            )
            self.db_name = os.getenv("DB_NAME") or fetch_ssm_parameter(
                "/nc-plus-one/DB_NAME"
            )
            self.db_username = os.getenv("DB_USERNAME") or fetch_ssm_parameter(
                "/nc-plus-one/DB_USERNAME"
            )
            self._db_secret_arn = os.getenv("DB_SECRET_ARN") or fetch_ssm_parameter(
                "/nc-plus-one/DB_SECRET_ARN"
            )
            self.db_password = os.getenv("DB_PASSWORD") or fetch_secret(
                self._db_secret_arn
            ).get("password")
            print("DB Configuration initialised successfully.")

        except (BotoCoreError, ClientError) as err:
            print(f"DB Configuration did not initialise successfully: {err}")
            raise

    @classmethod
    def get_config(cls) -> "DBConfig":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


class JWTConfig:
    _instance: "JWTConfig | None" = None

    def __init__(self) -> None:
        load_dotenv()
        try:
            self.jwt_expiry_minutes = int(
                os.getenv("JWT_EXPIRY_MINUTES", "30")
            ) or fetch_ssm_parameter("/nc-plus-one/JWT_EXPIRY_MINUTES")
            self.jwt_algorithm = os.getenv("JWT_ALGORITHM") or fetch_ssm_parameter(
                "/nc-plus-one/JWT_ALGORITHM"
            )
            self.jwt_secret = os.getenv("JWT_SECRET") or fetch_ssm_parameter(
                "/nc-plus-one/JWT_SECRET"
            )
            print("JWT Configuration initialised successfully.")

        except (BotoCoreError, ClientError) as err:
            print(f"JWT Configuration did not initialise successfully: {err}")
            raise

    @classmethod
    def get_config(cls) -> "JWTConfig":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
