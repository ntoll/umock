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

#: Attributes of the Mock class that should be handled as "normal" attributes
#: rather than treated as mocked attributes.
_RESERVED_MOCK_ATTRIBUTES = ("side_effect", "return_value")


class Mock:
    """
    A simple class for creating mock objects. Inspired by (but not the same as)
    Python's own unittest.mock.Mock class.

    Differences between this Mock class and Python's unittest.mock.Mock class:

    * Instantiation of the object only allows use of the spec, side_effect and
      return_value keyword arguments (no name, spec_set, wraps or unsafe
      arguments). However, arbitrary keyword arguments can be passed to be set
      as attributes on the mock object.
    * Calls are recorded in a list of tuples in the form (args, kwargs) rather
      than a list of special Call objects.
    * Mock objects do NOT record nor reveal call information relating to thier
      child mock objects (i.e. calls are not propagated to parent mocks).
    * None of the following methods exist in this implementation:
      mock_add_spec, attach_mock, configure_mock, _get_child_mock,
      method_calls, mock_calls.
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
                if type(spec) is not type:
                    # Set the mock object's class to that of the spec object.
                    self.__class__ = type(spec)
            for name in self._spec:
                # Create a new mock object for each attribute in the spec.
                setattr(self, name, Mock())
        if return_value:
            self.return_value = return_value
        if side_effect:
            if type(side_effect) in (str, list, tuple, set, dict):
                # If side_effect is an iterable then make it an iterator.
                self.side_effect = iter(side_effect)
            else:
                self.side_effect = side_effect
        self.reset_mock()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reset_mock(self):
        """
        Reset the mock object (self._calls) to a clean state.

        This is useful for when you want to reuse a mock object.

        The self._calls is a list of tuples, each of which represents a
        call to the mock object. Each tuple is in the form:

        (method_name, args, kwargs)
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

    @property
    def call_args(self):
        """
        Return the arguments of the last call to the mock object.
        """
        if self.call_count:
            return self._calls[-1]

    @property
    def call_args_list(self):
        """
        Return a list of the arguments of each call to the mock object.
        """
        return self._calls

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
        assert (args, kwargs) == self._calls[
            -1
        ], f"Expected {args} and {kwargs}, got {self._calls[-1]}."

    def assert_called_once_with(self, *args, **kwargs):
        """
        Assert that the mock object was called once with the given arguments.
        """
        self.assert_called_once()
        self.assert_called_with(*args, **kwargs)

    def assert_any_call(self, *args, **kwargs):
        """
        Assert that the mock object was called at least once with the given
        arguments.
        """
        assert (
            args,
            kwargs,
        ) in self._calls, (
            f"Expected at least one call with {args} and {kwargs}."
        )

    def assert_has_calls(self, calls, any_order=False):
        """
        Assert the mock has been called with the specified calls. The mock_
        calls list is checked for the calls.

        If any_order is false then the calls must be sequential. There can be
        extra calls before or after the specified calls.

        If any_order is true then the calls can be in any order, but they must
        all appear in mock_calls.
        """
        assert len(calls) <= len(
            self._calls
        ), f"Expected {len(calls)} call[s], got {len(self._calls)}."
        if any_order:
            for call in calls:
                assert (
                    call in self._calls
                ), f"Expected {call} in {self._calls}."
        else:
            for i, call in enumerate(calls):
                assert (
                    self._calls[i] == call
                ), f"Expected {call} at index {i}, got {self._calls[i]}."

    def assert_never_called(self):
        """
        Assert that the mock object was never called.
        """
        assert (
            self.call_count == 0
        ), f"Expected no calls, got {self.call_count}."

    def __call__(self, *args, **kwargs):
        """
        Record the call and return the specified result. Calls to the mock
        object are recorded in the self._calls list. Each call is a tuple in
        the form: (method_name, args, kwargs).

        In order of precedence, the return value is determined as follows:

        If a side_effect is specified then that is used to determine the
        return value. If a return_value is specified then that is used. If
        neither are specified then the same Mock object is returned each time.
        """
        self._calls.append((args, kwargs))
        if hasattr(self, "side_effect"):
            if type(self.side_effect) is type and issubclass(
                self.side_effect, BaseException
            ):
                raise self.side_effect()
            elif isinstance(self.side_effect, BaseException):
                raise self.side_effect
            elif hasattr(self.side_effect, "__next__"):
                return next(self.side_effect)
            elif callable(self.side_effect):
                return self.side_effect(*args, **kwargs)
            raise TypeError("The mock object has an invalid side_effect.")
        if hasattr(self, "return_value"):
            return self.return_value
        else:
            # Return a mock object (ensuring it's the same one each time).
            if hasattr(self, "_mock_value"):
                return self._mock_value
            else:
                new_mock = Mock()
                self._mock_value = new_mock
                return new_mock

    def __getattr__(self, name):
        """
        Retrieve the value of the attribute `name` if it exists in the
        instance's dictionary. If the attribute does not exist, a new `Mock`
        object is created, assigned to the attribute, and returned.

        Raises an AttributeError if the attribute does not exist and the
        instance has a `_spec` attribute that does not contain the attribute
        name.
        """
        if name.startswith("_") or name in _RESERVED_MOCK_ATTRIBUTES:
            return super().__getattr__(name)
        elif name in self.__dict__:
            return self.__dict__[name]
        elif hasattr(self, "_spec") and name not in self._spec:
            raise AttributeError(f"Mock object has no attribute '{name}'.")
        else:
            new_mock = Mock()
            setattr(self, name, new_mock)
            return new_mock


class AsyncMock(Mock):
    """
    A simple class for creating asynchronous mock objects. Inspired by (but not
    the same as) Python's own unittest.mock.AsyncMock class.

    TODO: Finish this class.
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
