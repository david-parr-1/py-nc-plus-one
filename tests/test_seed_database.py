import pytest
import json
from db.seed_database import extract_json_data, format_json_as_values


@pytest.fixture()
def dummy_json_extract():
    dummy_data = [
        {
            "name": "Nexus, University of Leeds",
            "address": "Discovery Way, Leeds, LS2 3AA",
            "capacity": 200
        },
        {
            "name": "Manchester Central Library",
            "address": "St Peter's Square, Manchester, M2 5PD",
            "capacity": 80
        },
        {
            "name": "Online – Zoom",
            "address": None,
            "capacity": 500
        }
    ]
    return dummy_data


def test_extract_json_data_raises_filenotfounderror():
    with pytest.raises(FileNotFoundError) as error:
        result = extract_json_data("/non-existent-file.json")

    assert error.errisinstance(FileNotFoundError) == True


def test_format_json_as_values_returns_list(dummy_json_extract):
    result = format_json_as_values(dummy_json_extract)
    assert isinstance(result, list) == True


def test_format_json_as_values_returns_list_of_dicts(dummy_json_extract):
    result = format_json_as_values(dummy_json_extract)
    list_contains_types = [True if isinstance(item, tuple) else False for item in result]
    assert all(list_contains_types) == True


def test_format_json_returns_correct_number_of_tuples(dummy_json_extract):
    result = format_json_as_values(dummy_json_extract)
    expected_result = len(dummy_json_extract)
    assert len(result) == expected_result


def test_format_json_returns_typeerror_if_input_is_not_list():
    with pytest.raises(TypeError) as error:
        result = format_json_as_values("test")
    assert str(error.value) == "Input must be type list"
