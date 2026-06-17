import pytest
from db.seed_database import make_sql_inserts


@pytest.fixture
def default_extracted_data():
    extracted_data = [
        {
            "name": "Alice Rahman",
            "email": "alice@example.com",
            "password": "password123"
        },
        {
            "name": "Bob Nguyen",
            "email": "bob@example.com",
            "password": "password123"
        },
        {
            "name": "Carol Singh",
            "email": "carol@example.com",
            "password": "password123"
        }
    ]

    return extracted_data

def test_make_sql_inserts_returns_empty_list():
    input = []
    result = make_sql_inserts(input)
    assert result == []
    

def test_make_sql_inserts_raises_typeerror_when_input_not_list():
    with pytest.raises(TypeError) as e:
        result = make_sql_inserts("input")

    assert str(e.value) == "Expected input type list. Got <class 'str'>."


def test_make_sql_inserts_surrounds_return_with_parentheses(default_extracted_data):
    result = make_sql_inserts(default_extracted_data)
    assert result[0] == "("
    assert result[-1] == ")"
    