import json
import os
from typing import Any

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()


REGION_NAME = os.getenv("AWS_REGION", "eu-west-2")


ssm_client = boto3.client(
    "ssm",
    region_name=REGION_NAME,
)
secretsmanager_client = boto3.client(
    "secretsmanager",
    region_name=REGION_NAME,
)


def fetch_ssm_parameter(param_name: str, client: BaseClient = ssm_client) -> Any:
    """
    Fetch a stored parameter from the AWS parameter store.

    Args:
        param_name: Parameter name of the stored parameter.
        client (optional): An SSM client if not using the default `ssm_client`.

    Returns:
        The value of the stored parameter.
    """
    try:
        response = client.get_parameter(
            Name=param_name,
            WithDecryption=True,
        )
        parameter = response["Parameter"]["Value"]
        if parameter is None:
            raise ValueError("Secret not retrieved successfully")
        return parameter

    except (
        BotoCoreError,
        ClientError,
    ) as err:
        print(f"Error retrieving AWS parameters: {err}")
        raise


def fetch_secret(secret_id: str, client: BaseClient = secretsmanager_client) -> dict:
    """
    Fetch a stored secret value from the AWS Secrets Manager.

    Args:
        secret_id: The name of the stored secret.
        client (Optional): A secrets manager client if not using the default
            `secrets_manager_client`.

    Returns:
        The returned secret value(s) parsed into a dictionary.
    """
    try:
        response = client.get_secret_value(SecretId=secret_id)
        secret = json.loads(response.get("SecretString"))
        if secret is None:
            raise ValueError("Secret not retrieved successfully")
        return secret

    except (BotoCoreError, ClientError, ValueError) as err:
        print(f"Error retrieving AWS secrets: {err}")
        raise
