from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from src.utils import fetch_secret, fetch_ssm_parameter


def test_fetch_ssm_parameter_returns_an_existing_parameter(
    mock_ssm_client, mock_ssm_parameter
):
    client = mock_ssm_client
    parameter_name = mock_ssm_parameter["param_name"]

    response = fetch_ssm_parameter(parameter_name, client)

    assert response == mock_ssm_parameter["param_value"]


def test_fetch_ssm_parameter_reraises_clienterror_with_non_existant_parameter(
    mock_ssm_client,
):
    client = mock_ssm_client
    parameter_name = "/non_existent/parameter"

    with pytest.raises(ClientError, match=r"ParameterNotFound"):
        fetch_ssm_parameter(parameter_name, client)


def test_fetch_ssm_parameter_reraises_connection_failure(mock_aws_credentials):
    client = Mock()
    client.get_parameter.side_effect = EndpointConnectionError(
        endpoint_url="https://ssm.eu-west-2.amazonaws.com"
    )
    parameter_name = "/non_existent/parameter"

    with pytest.raises(EndpointConnectionError):
        fetch_ssm_parameter(parameter_name, client)


def test_fetch_secret_returns_secret_value(mock_secretsmanager_client, mock_secret):
    client = mock_secretsmanager_client
    secret_id = mock_secret["secret_id"]

    response = fetch_secret(secret_id, client)

    assert response["username"] == "test_user"
    assert response["password"] == "test_password"


def test_fetch_secret_reraises_clienterror_for_non_existent_secret(
    mock_secretsmanager_client,
):
    client = mock_secretsmanager_client

    with pytest.raises(ClientError, match=r"ResourceNotFoundException"):
        fetch_secret("/non-existent/secret", client)


def test_fetch_secret_reraises_connection_failure(mock_aws_credentials):
    client = Mock()
    client.get_secret_value.side_effect = EndpointConnectionError(
        endpoint_url="https://secretsmanager.eu-west-2.amazonaws.com"
    )
    secret_name = "/non-existent/secret"

    with pytest.raises(EndpointConnectionError):
        fetch_secret(secret_name, client)
