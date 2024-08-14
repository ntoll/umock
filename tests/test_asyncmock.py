"""
Tests to ensure that the AsyncMock class works as expected (close to, but not
exacty the same as unittest.mock.AsyncMock).
"""

import sys
import upytest
from umock import AsyncMock


#: A flag to show if MicroPython is the current Python interpreter.
is_micropython = "micropython" in sys.version.lower()


def test_init_async_mock():
    """
    A plain AsyncMock object can be created with no arguments. Accessing
    arbitrary attributes on such an object (without a spec) should return
    another AsyncMock object.
    """
    mock = AsyncMock()
    assert (
        mock.await_count == 0
    ), "Non zero await count with new AsyncMock object."
    assert isinstance(
        mock.foo, AsyncMock
    ), "Attribute access did not return an AsyncMock."


def test_init_async_mock_with_spec_from_list():
    """
    An AsyncMock object should be created with the specified list of
    attributes. Accessing arbitrary attributes not in the list should raise an
    AttributeError.

    If an arbitrary attribute is subqeuently added to the mock object, it
    should be accessible as per normal Python behaviour.
    """
    mock = AsyncMock(spec=["foo", "bar"])
    assert hasattr(mock, "foo"), "AsyncMock object missing 'foo' attribute."
    assert hasattr(mock, "bar"), "AsyncMock object missing 'bar' attribute."
    assert not hasattr(
        mock, "baz"
    ), "AsyncMock object has unexpected 'baz' attribute."
    mock.baz = "test"
    assert (
        mock.baz == "test"
    ), "AsyncMock object attribute 'baz' not set correctly."


def test_init_async_mock_with_spec_from_object():
    """
    An AsyncMock object should be created with the specified attributes derived
    from the referenced instance. Accessing arbitrary attributes not on the
    object should raise an AttributeError.

    If an arbitrary attribute is subqeuently added to the mock object, it
    should be accessible as per normal Python behaviour.
    """

    class TestClass:
        x = 1
        y = 2

    obj = TestClass()
    mock = AsyncMock(spec=obj)
    assert hasattr(mock, "x"), "AsyncMock object missing 'x' attribute."
    assert hasattr(mock, "y"), "AsyncMock object missing 'y' attribute."
    assert not hasattr(
        mock, "z"
    ), "AsyncMock object has unexpected 'z' attribute."
    assert (
        mock.__class__ == AsyncMock
    ), "AsyncMock object has unexpected class."
    mock.z = "test"
    assert (
        mock.z == "test"
    ), "AsyncMock object attribute 'z' not set correctly."


def test_init_async_mock_with_spec_from_class():
    """
    An AsyncMock object should be created with the specified attributes derived
    from the referenced class. Since this is a class spec, the AsyncMock's
    __class__ remains as AsyncMock. Accessing arbitrary attributes not on the
    class should raise an AttributeError.

    If an arbitrary attribute is subqeuently added to the mock object, it
    should be accessible as per normal Python behaviour.
    """

    class TestClass:
        x = 1
        y = 2

    mock = AsyncMock(spec=TestClass)
    assert hasattr(mock, "x"), "AsyncMock object missing 'x' attribute."
    assert hasattr(mock, "y"), "AsyncMock object missing 'y' attribute."
    assert not hasattr(
        mock, "z"
    ), "AsyncMock object has unexpected 'z' attribute."
    assert (
        mock.__class__ == AsyncMock
    ), "AsyncMock object has unexpected class."
    mock.z = "test"
    assert (
        mock.z == "test"
    ), "AsyncMock object attribute 'z' not set correctly."


async def test_init_async_mock_with_awaitable_side_effect():
    """
    An AsyncMock object should be created with the specified callable side
    effect that computes the result of an await on the mock object.
    """

    def side_effect(a, b):
        return a + b

    mock = AsyncMock(side_effect=side_effect)
    assert (
        await mock(1, 2) == 3
    ), "AsyncMock object side effect did not compute correctly."


async def test_init_async_mock_with_exception_class_side_effect():
    """
    An AsyncMock object should be created with the specified exception class
    side effect that raises the exception when the mock object is called.
    """

    class TestException(Exception):
        pass

    mock = AsyncMock(side_effect=TestException)
    with upytest.raises(TestException):
        await mock()


async def test_init_async_mock_with_exception_instance_side_effect():
    """
    An AsyncMock object should be created with the specified exception instance
    side effect that is raised when the mock object is called.
    """

    ex = ValueError("test")
    mock = AsyncMock(side_effect=ex)
    with upytest.raises(ValueError) as expected:
        await mock()
    assert (
        str(expected.exception) == "test"
    ), "Exception message not as expected."


async def test_init_async_mock_with_iterable_side_effect():
    """
    An AsyncMock object should be created with the specified iterable side
    effect that returns the next item in the iterable each time the mock object
    is called.
    """

    mock = AsyncMock(side_effect=[1, 2, 3])
    assert await mock() == 1, "First call did not return 1."
    assert await mock() == 2, "Second call did not return 2."
    assert await mock() == 3, "Third call did not return 3."
    with upytest.raises(RuntimeError) as expected:
        await mock()
    if is_micropython:
        assert str(expected.exception) == "generator raised StopIteration"
    else:
        assert str(expected.exception) == "coroutine raised StopIteration"


async def test_init_async_mock_with_invalid_side_effect():
    """
    If an invalid side effect is specified, a TypeError should be raised.
    """
    mock = AsyncMock(side_effect=1)
    with upytest.raises(TypeError):
        await mock()


async def test_init_async_mock_with_return_value():
    """
    An AsyncMock object should be created with the specified return value that
    is returned each time the mock object is called.
    """
    mock = AsyncMock(return_value=42)
    assert await mock() == 42, "Return value not as expected."


def test_init_async_mock_with_kwargs():
    """
    An AsyncMock object should be created with the specified keyword arguments
    turned into attributes on the mock object.
    """
    mock = AsyncMock(foo=1, bar=2)
    assert mock.foo == 1, "Attribute 'foo' not set correctly."
    assert mock.bar == 2, "Attribute 'bar' not set correctly."


async def test_reset_async_mock():
    """
    Resetting the mock clears the call related data.
    """
    m = AsyncMock()
    assert m.await_count == 0
    await m()
    assert m.await_count == 1
    m.reset_mock()
    assert m.await_count == 0


async def test_await_count():
    """
    The await_count attribute should return the number of times the mock object
    has been awaited.
    """
    m = AsyncMock()
    assert m.await_count == 0
    await m()
    assert m.await_count == 1
    await m()
    assert m.await_count == 2


async def test_awaited():
    """
    The called attribute should return True if the mock object has been awaited
    at least once.
    """
    m = AsyncMock()
    assert not m.awaited
    await m()
    assert m.awaited


async def test_await_args():
    """
    The await_args attribute should return the arguments and keyword arguments
    of the last await to the mock object.
    """
    m = AsyncMock()
    assert m.await_args is None
    await m(1, 2, a=3, b=4)
    assert m.await_args == ((1, 2), {"a": 3, "b": 4})


async def test_await_args_list():
    """
    The await_args_list attribute should return a list of tuples containing the
    arguments and keyword arguments of each await to the mock object.
    """
    m = AsyncMock()
    assert m.await_args_list == []
    await m(1, 2, a=3, b=4)
    await m(5, 6, a=7, b=8)
    assert m.await_args_list == [
        ((1, 2), {"a": 3, "b": 4}),
        ((5, 6), {"a": 7, "b": 8}),
    ]


async def test_assert_awaited():
    """
    The assert_awaited method should raise an AssertionError if the mock object
    has not been awaited.
    """
    m = AsyncMock()
    with upytest.raises(AssertionError):
        m.assert_awaited()
    await m()
    m.assert_awaited()


async def test_assert_awaited_once():
    """
    The assert_awaited_once method should raise an AssertionError if the mock
    object has not been awaited exactly once.
    """
    m = AsyncMock()
    with upytest.raises(AssertionError):
        m.assert_awaited_once()
    await m()
    m.assert_awaited_once()
    await m()
    with upytest.raises(AssertionError):
        m.assert_awaited_once()


async def test_assert_awaited_with():
    """
    The assert_awaited_with method should raise an AssertionError if the mock
    object not last awaited with the specified arguments.
    """
    m = AsyncMock()
    await m(1, 2, a=3, b=4)
    m.assert_awaited_with(1, 2, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_awaited_with(1, 3, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_awaited_with(1, 2, a=3, b=5)


async def test_assert_awaited_once_with():
    """
    The assert_awaited_once_with method should raise an AssertionError if the
    mock object has not been awaited exactly once with the specified arguments.
    """
    m = AsyncMock()
    await m(1, 2, a=3, b=4)
    m.assert_awaited_once_with(1, 2, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_awaited_once_with(1, 3, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_awaited_once_with(1, 2, a=3, b=5)
    await m(1, 2, a=3, b=4)
    with upytest.raises(AssertionError):
        m.assert_awaited_once_with(1, 2, a=3, b=4)


async def test_assert_any_await():
    """
    The assert_any_await method should raise an AssertionError if the mock
    object has not been awaited with the specified arguments at least once.
    """
    m = AsyncMock()
    with upytest.raises(AssertionError):
        m.assert_any_await(1, 2, a=3, b=4)
    await m(1, 2, a=3, b=4)
    await m(5, 6, a=7, b=8)
    m.assert_any_await(1, 2, a=3, b=4)


async def test_assert_has_awaits():
    """
    The assert_has_awaits method should raise an AssertionError if the mock
    object has not been awaited with the specified arguments at least once.
    """
    m = AsyncMock()
    with upytest.raises(AssertionError):
        # No awaits have been made yet.
        m.assert_has_awaits([((1, 2), {"a": 3, "b": 4})])
    await m(1, 2, a=3, b=4)
    await m(5, 6, a=7, b=8)
    # Awaits have been made.
    m.assert_has_awaits(
        [((1, 2), {"a": 3, "b": 4}), ((5, 6), {"a": 7, "b": 8})]
    )
    with upytest.raises(AssertionError):
        # Awaits have been made, but not in the specified order.
        m.assert_has_awaits(
            [((5, 6), {"a": 7, "b": 9}), ((1, 2), {"a": 3, "b": 4})]
        )
    with upytest.raises(AssertionError):
        # Awaits have been made, but not with the specified arguments.
        m.assert_has_awaits(
            [((1, 2), {"a": 3, "b": 4}), ((5, 6), {"a": 7, "b": 9})]
        )


async def test_assert_has_awaits_any_order():
    """
    The assert_has_awaits method should raise an AssertionError if the mock
    object has not been awaited with the specified arguments at least once.
    """
    m = AsyncMock()
    with upytest.raises(AssertionError):
        # No awaits have been made yet.
        m.assert_has_awaits([((1, 2), {"a": 3, "b": 4})], any_order=True)
    await m(1, 2, a=3, b=4)
    await m(5, 6, a=7, b=8)
    # Awaits have been made, no matter the order.
    m.assert_has_awaits(
        [((5, 6), {"a": 7, "b": 8}), ((1, 2), {"a": 3, "b": 4})],
        any_order=True,
    )
    with upytest.raises(AssertionError):
        # Awaits have been made, but not with the specified arguments.
        m.assert_has_awaits(
            [((1, 2), {"a": 3, "b": 4}), ((5, 6), {"a": 7, "b": 9})],
            any_order=True,
        )


async def test_assert_not_awaited():
    """
    The assert_not_awaited method should raise an AssertionError if the mock
    object has been awaited at least once.
    """
    m = AsyncMock()
    # OK, no awaits.
    m.assert_not_awaited()
    await m()
    with upytest.raises(AssertionError):
        # Not OK, an await has been made.
        m.assert_not_awaited()


async def assert_await_returns_same_unique_mock():
    """
    The mock object should return the same unique mock object each time it is
    awaited.
    """
    m = AsyncMock()
    mock_result = await m()
    assert id(m) != id(mock_result), "Returned mock object is not unique."
    assert id(await m()) == id(
        mock_result
    ), "Returned mock object is not the same."


async def test_get_attribute_of_unknown_attribute_returns_mock():
    """
    Accessing an unknown attribute on the async mock object should return
    another async mock object. Each attribute access should return the same
    unique mock.
    """
    m = AsyncMock()
    assert isinstance(m.foo, AsyncMock), "Returned object is not an AsyncMock."
    assert id(m.foo) == id(m.foo), "Returned object is not the same."
    assert await m.foo() is await m.foo(), "Returned object is not the same."
    assert isinstance(await m.foo(), AsyncMock), "Returned object is not a Mock."
