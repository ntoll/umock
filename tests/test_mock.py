"""
Tests to ensure that the Mock class works as expected (close to, but not
exacty the same as unittest.mock.Mock).
"""

from umock import Mock


def test_init_mock():
    """
    A Mock object should be created with no attributes.
    """
    mock = Mock()
    assert mock.__dict__ == {}, "Not an empty dict."

def test_init_mock_with_spec():
    """
    A Mock object should be created with the specified attributes.
    """
    pass

def test_init_mock_with_spec_and_values():
    """
    A Mock object should be created with the specified attributes and values.
    """
    pass