"""
Tests to ensure that the Mock class works as expected (close to, but not
exacty the same as unittest.mock.Mock).
"""

import upytest
from umock import Mock


def test_init_mock():
    """
    A plain Mock object can be created with no arguments. Accessing arbitrary
    attributes on such an object (without a spec) should return another Mock
    object.
    """
    mock = Mock()
    assert mock.call_count == 0, "Non zero call count with new Mock object."
    assert isinstance(
        mock.foo, Mock
    ), "Attribute access did not return a Mock."


def test_init_mock_with_spec_from_list():
    """
    A Mock object should be created with the specified list of attributes.
    Accessing arbitrary attributes not in the list should raise an
    AttributeError.

    If an arbitrary attribute is subqeuently added to the mock object, it
    should be accessible as per normal Python behaviour.
    """
    mock = Mock(spec=["foo", "bar"])
    assert hasattr(mock, "foo"), "Mock object missing 'foo' attribute."
    assert hasattr(mock, "bar"), "Mock object missing 'bar' attribute."
    assert not hasattr(
        mock, "baz"
    ), "Mock object has unexpected 'baz' attribute."
    mock.baz = "test"
    assert mock.baz == "test", "Mock object attribute 'baz' not set correctly."


def test_init_mock_with_spec_from_object():
    """
    A Mock object should be created with the specified attributes derived from
    the referenced instance. The Mock's __class__ should be set to that of the
    spec object's. Accessing arbitrary attributes not on the class should raise
    an AttributeError.

    If an arbitrary attribute is subqeuently added to the mock object, it
    should be accessible as per normal Python behaviour.
    """

    class TestClass:
        x = 1
        y = 2

    obj = TestClass()
    mock = Mock(spec=obj)
    assert hasattr(mock, "x"), "Mock object missing 'x' attribute."
    assert hasattr(mock, "y"), "Mock object missing 'y' attribute."
    assert not hasattr(mock, "z"), "Mock object has unexpected 'z' attribute."
    assert mock.__class__ == TestClass, "Mock object has unexpected class."
    mock.z = "test"
    assert mock.z == "test", "Mock object attribute 'z' not set correctly."


def test_init_mock_with_spec_from_class():
    """
    A Mock object should be created with the specified attributes derived from
    the referenced class. Since this is a class spec, the Mock's __class__
    remains as Mock. Accessing arbitrary attributes not on the class should
    raise an AttributeError.

    If an arbitrary attribute is subqeuently added to the mock object, it
    should be accessible as per normal Python behaviour.
    """

    class TestClass:
        x = 1
        y = 2

    mock = Mock(spec=TestClass)
    assert hasattr(mock, "x"), "Mock object missing 'x' attribute."
    assert hasattr(mock, "y"), "Mock object missing 'y' attribute."
    assert not hasattr(mock, "z"), "Mock object has unexpected 'z' attribute."
    assert mock.__class__ == Mock, "Mock object has unexpected class."
    mock.z = "test"
    assert mock.z == "test", "Mock object attribute 'z' not set correctly."


def test_init_mock_with_callable_side_effect():
    """
    A Mock object should be created with the specified callable side effect
    that computes the result of a call on the mock object.
    """

    def side_effect(a, b):
        return a + b

    mock = Mock(side_effect=side_effect)
    assert (
        mock(1, 2) == 3
    ), "Mock object side effect did not compute correctly."


def test_init_mock_with_exception_class_side_effect():
    """
    A Mock object should be created with the specified exception class side
    effect that raises the exception when the mock object is called.
    """

    class TestException(Exception):
        pass

    mock = Mock(side_effect=TestException)
    with upytest.raises(TestException):
        mock()


def test_init_mock_with_exception_instance_side_effect():
    """
    A Mock object should be created with the specified exception instance side
    effect that is raised when the mock object is called.
    """

    ex = ValueError("test")
    mock = Mock(side_effect=ex)
    with upytest.raises(ValueError) as expected:
        mock()
    assert (
        str(expected.exception.value) == "test"
    ), "Exception message not as expected."


def test_init_mock_with_iterable_side_effect():
    """
    A Mock object should be created with the specified iterable side effect
    that returns the next item in the iterable each time the mock object is
    called.
    """
    
    mock = Mock(side_effect=[1, 2, 3])
    assert mock() == 1, "First call did not return 1."
    assert mock() == 2, "Second call did not return 2."
    assert mock() == 3, "Third call did not return 3."
    with upytest.raises(StopIteration):
        mock()

def test_init_mock_with_invalid_side_effect():
    """
    If an invalid side effect is specified, a TypeError should be raised.
    """
    mock = Mock(side_effect=1)
    with upytest.raises(TypeError):
        mock()

def test_init_mock_with_return_value():
    """
    A Mock object should be created with the specified return value that is
    returned each time the mock object is called.
    """
    mock = Mock(return_value=42)
    assert mock() == 42, "Return value not as expected."