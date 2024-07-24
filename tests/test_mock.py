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


def test_init_mock_with_kwargs():
    """
    A Mock object should be created with the specified keyword arguments turned
    into attributes on the mock object.
    """
    mock = Mock(foo=1, bar=2)
    assert mock.foo == 1, "Attribute 'foo' not set correctly."
    assert mock.bar == 2, "Attribute 'bar' not set correctly."


def test_reset_mock():
    """
    Resetting the mock clears the call related data.
    """
    m = Mock()
    assert m.call_count == 0
    m()
    assert m.call_count == 1
    m.reset_mock()
    assert m.call_count == 0


def test_call_count():
    """
    The call_count attribute should return the number of times the mock object
    has been called.
    """
    m = Mock()
    assert m.call_count == 0
    m()
    assert m.call_count == 1
    m()
    assert m.call_count == 2


def test_called():
    """
    The called attribute should return True if the mock object has been called
    at least once.
    """
    m = Mock()
    assert not m.called
    m()
    assert m.called


def test_call_args():
    """
    The call_args attribute should return the arguments and keyword arguments
    of the last call to the mock object.
    """
    m = Mock()
    assert m.call_args is None
    m(1, 2, a=3, b=4)
    assert m.call_args == ((1, 2), {"a": 3, "b": 4})


def test_call_args_list():
    """
    The call_args_list attribute should return a list of tuples containing the
    arguments and keyword arguments of each call to the mock object.
    """
    m = Mock()
    assert m.call_args_list == []
    m(1, 2, a=3, b=4)
    m(5, 6, a=7, b=8)
    assert m.call_args_list == [
        ((1, 2), {"a": 3, "b": 4}),
        ((5, 6), {"a": 7, "b": 8}),
    ]


def test_assert_called():
    """
    The assert_called method should raise an AssertionError if the mock object
    has not been called.
    """
    m = Mock()
    with upytest.raises(AssertionError):
        m.assert_called()
    m()
    m.assert_called()


def test_assert_called_once():
    """
    The assert_called_once method should raise an AssertionError if the mock
    object has not been called exactly once.
    """
    m = Mock()
    with upytest.raises(AssertionError):
        m.assert_called_once()
    m()
    m.assert_called_once()
    m()
    with upytest.raises(AssertionError):
        m.assert_called_once()


def test_assert_called_with():
    """
    The assert_called_with method should raise an AssertionError if the mock
    object not last called with the specified arguments.
    """
    m = Mock()
    m(1, 2, a=3, b=4)
    m.assert_called_with(1, 2, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_called_with(1, 3, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_called_with(1, 2, a=3, b=5)


def test_assert_called_once_with():
    """
    The assert_called_once_with method should raise an AssertionError if the
    mock object has not been called exactly once with the specified arguments.
    """
    m = Mock()
    m(1, 2, a=3, b=4)
    m.assert_called_once_with(1, 2, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_called_once_with(1, 3, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_called_once_with(1, 2, a=3, b=5)
    m(1, 2, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_called_once_with(1, 2, a=3, b=4)


def test_assert_any_call():
    """
    The assert_any_call method should raise an AssertionError if the mock
    object has not been called with the specified arguments at least once.
    """
    m = Mock()
    with upytest.raises(AssertionError):
        m.assert_any_call(1, 2, a=3, b=4)
    m(1, 2, a=3, b=4)
    m(5, 6, a=7, b=8)
    m.assert_any_call(1, 2, a=3, b=4)


def test_assert_has_calls():
    """
    The assert_has_calls method should raise an AssertionError if the mock
    object has not been called with the specified arguments at least once.
    """
    m = Mock()
    with upytest.raises(AssertionError):
        # No calls have been made yet.
        m.assert_has_calls([((1, 2), {"a": 3, "b": 4})])
    m(1, 2, a=3, b=4)
    m(5, 6, a=7, b=8)
    # Calls have been made.
    m.assert_has_calls(
        [((1, 2), {"a": 3, "b": 4}), ((5, 6), {"a": 7, "b": 8})]
    )
    with upytest.raises(AssertionError):
        # Calls have been made, but not in the specified order.
        m.assert_has_calls(
            [((5, 6), {"a": 7, "b": 9}), ((1, 2), {"a": 3, "b": 4})]
        )
    with upytest.raises(AssertionError):
        # Calls have been made, but not with the specified arguments.
        m.assert_has_calls(
            [((1, 2), {"a": 3, "b": 4}), ((5, 6), {"a": 7, "b": 9})]
        )


def test_assert_has_calls_any_order():
    """
    The assert_has_calls method should raise an AssertionError if the mock
    object has not been called with the specified arguments at least once.
    """
    m = Mock()
    with upytest.raises(AssertionError):
        # No calls have been made yet.
        m.assert_has_calls([((1, 2), {"a": 3, "b": 4})], any_order=True)
    m(1, 2, a=3, b=4)
    m(5, 6, a=7, b=8)
    # Calls have been made, no matter the order.
    m.assert_has_calls(
        [((5, 6), {"a": 7, "b": 8}), ((1, 2), {"a": 3, "b": 4})],
        any_order=True,
    )
    with upytest.raises(AssertionError):
        # Calls have been made, but not with the specified arguments.
        m.assert_has_calls(
            [((1, 2), {"a": 3, "b": 4}), ((5, 6), {"a": 7, "b": 9})],
            any_order=True,
        )


def test_assert_never_called():
    """
    The assert_never_called method should raise an AssertionError if the mock
    object has been called at least once.
    """
    m = Mock()
    # OK, no calls.
    m.assert_never_called()
    m()
    with upytest.raises(AssertionError):
        # Not OK, a call has been made.
        m.assert_never_called()


def assert_call_returns_same_unique_mock():
    """
    The mock object should return the same unique mock object each time it is
    called.
    """
    m = Mock()
    mock_result = m()
    assert id(m) != id(mock_result), "Returned mock object is not unique."
    assert id(m()) == id(mock_result), "Returned mock object is not the same."


def test_get_attribute_of_unknown_attribute_returns_mock():
    """
    Accessing an unknown attribute on the mock object should return another
    mock object. Each attribute access should return the same unique mock.
    """
    m = Mock()
    assert isinstance(m.foo, Mock), "Returned object is not a Mock."
    assert id(m.foo) == id(m.foo), "Returned object is not the same."
