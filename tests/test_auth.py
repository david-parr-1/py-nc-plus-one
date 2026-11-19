import pytest
from fastapi import HTTPException

from auth.auth import get_user_id


def test_get_user_id_rejects_expired_token(mock_expired_token):
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(mock_expired_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"


def test_get_user_id_rejects_invalid_token(mock_invalid_token):
    with pytest.raises(HTTPException) as exc_info:
        get_user_id(mock_invalid_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token is invalid"


def test_get_user_id_returns_int_of_user_id_with_valid_token(mock_valid_token):
    user_id = get_user_id(mock_valid_token)

    assert user_id == 1
