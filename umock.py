"""
uMock (MicroMock)

A very simple, small and limited module for mocking objects in MicroPython with
PyScript.

Copyright (c) 2024 Nicholas H.Tollervey

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


class Mock:
    """
    A simple class for creating mock objects. Inspired by (but not the same as)
    Python's own unittest.mock.Mock class.
    """

    def __init__(
        self,
        spec=None,
        side_effect=None,
        return_value=None,
        **kwargs,
    ):
        """
        Create a new Mock object. Mock takes several optional arguments that
        specify the behaviour of the Mock object:

        * spec: This can be either a list of strings or an existing object (a
          class or instance) that acts as the specification for the mock
          object. If you pass in an object then a list of strings is formed by
          calling dir on the object (excluding unsupported magic attributes and
          methods). Accessing any attribute not in this list will raise an
          AttributeError.

          If spec is an object (rather than a list of strings) then __class__
          returns the class of the spec object. This allows mocks to pass
          isinstance() tests.
        * side_effect: A function to be called whenever the Mock is called.
          Useful for raising exceptions or dynamically changing return values.
          The function is called with the same arguments as the mock, and the
          return value of this function is used as the mock's return value.

          Alternatively side_effect can be an exception class or instance. In
          this case the exception will be raised when the mock is called.

          If side_effect is an iterable then each call to the mock will return
          the next value from the iterable.

          A side_effect can be cleared by setting it to None.
        * return_value: The value returned when the mock is called. By default
          this is a new Mock (created on first access).
        """
        if spec:
            if isinstance(spec, list):
                self._spec = spec
            else:
                self._spec = [
                    name
                    for name in dir(spec)
                    if not name.startswith("_")
                    and not callable(getattr(spec, name))
                ]
                self.__class__ = spec.__class__
        if return_value:
            self.return_value = return_value
        if side_effect:
            self.side_effect = side_effect
        self.reset_mock()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reset_mock(self):
        """
        Reset the mock object (self._calls) to a clean state.

        This is useful for when you want to reuse a mock object.

        The self._calls contains a list of tuples, each of which represents a
        call to the mock object. The tuple is in the form: (method_name, args,
        kwargs).
        """
        self._calls = []

    @property
    def call_count(self):
        """
        Return the number of calls made to the mock object.
        """
        return len(self._calls)

    @property
    def called(self):
        """
        Return True if the mock object was called at least once.
        """
        return self.call_count > 0

    def assert_called(self):
        """
        Assert that the mock object was called at least once.
        """
        assert self.call_count > 0, "Expected at least one call."

    def assert_called_once(self):
        """
        Assert that the mock object was called once.
        """
        assert self.call_count == 1, f"Expected 1 call, got {self.call_count}."

    def assert_called_with(self, *args, **kwargs):
        """
        Assert that the mock object was last called in a particular way.
        """
        self.assert_called()
        assert (
            self._calls[-1][1] == args
        ), f"Expected {args}, got {self._calls[-1][1]}."
        assert (
            self._calls[-1][2] == kwargs
        ), f"Expected {kwargs}, got {self._calls[-1][2]}."

    def assert_called_once_with(self, *args, **kwargs):
        """
        Assert that the mock object was called once with the given arguments.
        """
        self.assert_called_once()
        assert (
            self._calls[0][1] == args
        ), f"Expected {args}, got {self._calls[0][1]}."
        assert (
            self._calls[0][2] == kwargs
        ), f"Expected {kwargs}, got {self._calls[0][2]}."

    def assert_any_call(self, *args, **kwargs):
        """
        Assert that the mock object was called at least once with the given
        arguments.
        """
        for call in self._calls:
            if call[1] == args and call[2] == kwargs:
                return
        assert False, f"Expected at least one call with {args} and {kwargs}."

    def assert_has_calls(self, calls, any_order=False):
        """
        Assert the mock has been called with the specified calls. The mock_
        calls list is checked for the calls.

        If any_order is false then the calls must be sequential. There can be
        extra calls before or after the specified calls.

        If any_order is true then the calls can be in any order, but they must
        all appear in mock_calls.
        """
        if not any_order:
            assert len(self._calls) >= len(
                calls
            ), f"Expected at least {len(calls)} calls, got {len(self._calls)}."
            for i, call in enumerate(calls):
                assert (
                    self._calls[i][1] == call[0]
                ), f"Expected {call[0]}, got {self._calls[i][1]}."
                assert (
                    self._calls[i][2] == call[1]
                ), f"Expected {call[1]}, got {self._calls[i][2]}."
        else:
            for call in calls:
                assert (
                    call in self._calls
                ), f"Expected {call} in {self._calls}."

    def assert_never_called(self):
        """
        Assert that the mock object was never called.
        """
        assert (
            self.call_count == 0
        ), f"Expected no calls, got {self.call_count}."

    def __call__(self, *args, **kwargs):
        """
        Record the call.
        """
        self._calls.append(("__call__", args, kwargs))
        if hasattr(self, "side_effect"):
            if callable(self.side_effect):
                return self.side_effect(*args, **kwargs)
            elif isinstance(self.side_effect, Exception):
                raise self.side_effect
            elif hasattr(self.side_effect, "__iter__"):
                return self.side_effect.pop(0)
        if hasattr(self, "return_value"):
            return self.return_value
        else:
            return Mock()

    def __getattr__(self, name):
        """
        Return a callable that records the call.
        """
        if hasattr(self, "return_value"):
            return self.return_value
        else:
            return Mock()

    def __setattr__(self, name, value):
        """
        Set an attribute on the mock object.
        """
        if hasattr(self, "_spec") and name not in self._spec:
            raise AttributeError(f"{name} is not in the mock's spec.")
        setattr(self, name, value)

    def __delattr__(self, name):
        """
        Delete an attribute on the mock object.
        """
        if hasattr(self, "_spec") and name not in self._spec:
            raise AttributeError(f"{name} is not in the mock's spec.")
        delattr(self, name)


class AsyncMock(Mock):
    """
    A simple class for creating asynchronous mock objects. Inspired by (but not
    the same as) Python's own unittest.mock.AsyncMock class.
    """

    ...


class patch:
    """
    patch() acts as a function decorator, class decorator or a context manager.
    Inside the body of the function or with statement, the target is patched
    with a new object. When the function/with statement exits the patch is
    undone.
    """

    def __init__(self, target, new):
        """
        Create a new patch object that will replace the target with new.
        """
        self.target = target
        self.new = new

    def __enter__(self):
        """
        Replace the target with new.
        """
        self._old = getattr(self.target, self.new.__name__, None)
        setattr(self.target, self.new.__name__, self.new)
        return self.new

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Restore the target to its original state.
        """
        setattr(self.target, self.new.__name__, self._old)
        return False
