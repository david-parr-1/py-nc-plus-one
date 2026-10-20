import pytest

from db.seed_database import convert_dict_to_tuple_list, extract_json_data


@pytest.fixture()
def dummy_json_extract():
    dummy_data = [
        {
            "name": "Nexus, University of Leeds",
            "address": "Discovery Way, Leeds, LS2 3AA",
            "capacity": 200,
        },
        {
            "name": "Manchester Central Library",
            "address": "St Peter's Square, Manchester, M2 5PD",
            "capacity": 80,
        },
        {"name": "Online – Zoom", "address": None, "capacity": 500},
    ]
    return dummy_data


def test_extract_json_data_raises_filenotfounderror():
    with pytest.raises(FileNotFoundError) as error:
        extract_json_data("/non-existent-file.json")

    assert error.errisinstance(FileNotFoundError) == True


def test_convert_dict_to_tuple_list_returns_list(dummy_json_extract):
    result = convert_dict_to_tuple_list(dummy_json_extract)
    assert isinstance(result, list) == True


def test_convert_dict_to_tuple_list_returns_list_of_tuples(dummy_json_extract):
    result = convert_dict_to_tuple_list(dummy_json_extract)
    list_contains_tuples = [isinstance(item, tuple) for item in result]
    assert all(list_contains_tuples) == True


def test_convert_dict_to_tuple_list_returns_correct_number_of_tuples(
    dummy_json_extract,
):
    result = convert_dict_to_tuple_list(dummy_json_extract)
    expected_result = len(dummy_json_extract)
    assert len(result) == expected_result


def test_convert_dict_to_tuple_list_returns_typeerror_if_input_is_not_list():
    with pytest.raises(TypeError) as error:
        convert_dict_to_tuple_list("test")
    assert str(error.value) == "Input must be type list"
