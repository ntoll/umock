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

import sys
import inspect

__all__ = ["Mock", "AsyncMock", "patch"]


#: A flag to show if MicroPython is the current Python interpreter.
is_micropython = "micropython" in sys.version.lower()


#: Attributes of the Mock class that should be handled as "normal" attributes
#: rather than treated as mocked attributes.
_RESERVED_MOCK_ATTRIBUTES = ("side_effect", "return_value")


def is_awaitable(obj):
    """
    Returns a boolean indication if the passed in obj is an awaitable
    function. (MicroPython treats awaitables as generator functions.)
    """
    if is_micropython:
        return inspect.isgeneratorfunction(obj)
    return inspect.iscoroutinefunction(obj)


def import_module(module_path):
    """
    Import the referenced module in a way that works with both MicroPython and
    Pyodide. The module_path should be a dotted string representing the module
    to import.
    """
    if is_micropython:
        file_path = module_path.replace(".", "/")
        module = __import__(file_path)
        return module
    else:
        module_name = module_path.split(".")[-1]
        module = __import__(
            module_path,
            fromlist=[
                module_name,
            ],
        )
    return module


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
                    and not (
                        callable(getattr(spec, name))  # no methods
                        or is_awaitable(getattr(spec, name))  # no awaitables
                    )
                ]
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
        call to the mock object. Each tuple is in the form: (args, kwargs)
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
        Assert that the mock object was last called with the specified
        arguments.
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
        Assert the mock has been called with the specified calls.

        If any_order is false then the calls must be sequential.

        If any_order is true then the calls can be in any order, but they must
        all appear in call_args_list.
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
        the form: (args, kwargs).

        In order of precedence, the return value is determined as follows:

        If a side_effect is specified then that is used to determine the
        return value. If a return_value is specified then that is used. If
        neither are specified then the same Mock object is returned each time.
        """
        self._calls.append((args, kwargs))
        if "side_effect" in self.__dict__:
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
            # Special attributes are handled as normal attributes.
            return self.__dict__.get(name)
        elif name in self.__dict__:
            # Existing attributes are returned as is.
            return self.__dict__[name]
        elif "_spec" in self.__dict__ and name not in self._spec:
            # If the attribute is not in the spec then raise an AttributeError.
            raise AttributeError(f"Mock object has no attribute '{name}'.")
        else:
            # Otherwise, create a new mock object for the attribute.
            new_mock = Mock()
            setattr(self, name, new_mock)
            return new_mock


class AsyncMock:
    """
    A simple class for creating async (awaitable) mock objects. Inspired by
    (but not the same as) Python's own unittest.mock.AsyncMock class.

    Differences between this Mock class and Python's unittest.mock.AsyncMock
    class:

    * Instantiation of the object only allows use of the spec, side_effect and
      return_value keyword arguments (no name, spec_set, wraps or unsafe
      arguments). However, arbitrary keyword arguments can be passed to be set
      as attributes on the mock object.
    * Awaits are recorded in a list of tuples in the form (args, kwargs) rather
      than a list of special awaited Call objects.
    * Mock objects do NOT record nor reveal await related information relating
      to thier child mock objects (i.e. awaits are not propagated to parent
      mocks).
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
        Create a new AsyncMock object. It takes several optional arguments that
        specify the behaviour of the asynchronous Mock object:

        * spec: This can be either a list of strings or an existing object (a
          class or instance) that acts as the specification for the mock
          object. If you pass in an object then a list of strings is formed by
          calling dir on the object (excluding unsupported magic attributes and
          methods). Accessing any attribute not in this list will raise an
          AttributeError.

          If spec is an object (rather than a list of strings) then __class__
          returns the class of the spec object. This allows mocks to pass
          isinstance() tests.
        * side_effect: A function to be called whenever the Mock is awaited.
          Useful for raising exceptions or dynamically changing return values.
          The function is called with the same arguments as the mock, and the
          return value of this function is used as the awaited mock's return
          value.

          Alternatively side_effect can be an exception class or instance. In
          this case the exception will be raised when the mock is awaited.

          If side_effect is an iterable then each await to the mock will yield
          the next value from the iterable.

          A side_effect can be cleared by setting it to None.
        * return_value: The value returned when the mock is awaited. By default
          this is a new AsyncMock (created on first access).
        """
        if spec:
            if isinstance(spec, list):
                self._spec = spec
            else:
                self._spec = [
                    name
                    for name in dir(spec)
                    if not name.startswith("_")
                    and not (
                        callable(getattr(spec, name))  # no methods
                        or is_awaitable(getattr(spec, name))  # no awaitables
                    )
                ]
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
        Reset the mock object (self._awaits) to a clean state.

        This is useful for when you want to reuse a mock object.

        The self._awaits is a list of tuples, each of which represents an
        await to the mock object. Each tuple is in the form: (args, kwargs)
        """
        self._awaits = []

    @property
    def await_count(self):
        """
        Return the number of times the mock object has been awaited.
        """
        return len(self._awaits)

    @property
    def awaited(self):
        """
        Return True if the mock object was awaited at least once.
        """
        return self.await_count > 0

    @property
    def await_args(self):
        """
        Return the arguments of the last await on the mock object.
        """
        if self.await_count:
            return self._awaits[-1]

    @property
    def await_args_list(self):
        """
        Return a list of the arguments of each await on the mock object.
        """
        return self._awaits

    def assert_awaited(self):
        """
        Assert that the mock object was awaited at least once.
        """
        assert self.await_count > 0, "Expected at least one await."

    def assert_awaited_once(self):
        """
        Assert that the mock object was awaited once.
        """
        assert (
            self.await_count == 1
        ), f"Expected 1 await, got {self.await_count}."

    def assert_awaited_with(self, *args, **kwargs):
        """
        Assert that the mock object was last awaited with the specified
        arguments.
        """
        self.assert_awaited()
        assert (args, kwargs) == self._awaits[
            -1
        ], f"Expected {args} and {kwargs}, got {self._awaits[-1]}."

    def assert_awaited_once_with(self, *args, **kwargs):
        """
        Assert that the mock object was awaited once with the given arguments.
        """
        self.assert_awaited_once()
        self.assert_awaited_with(*args, **kwargs)

    def assert_any_await(self, *args, **kwargs):
        """
        Assert that the mock object was awaited at least once with the given
        arguments.
        """
        assert (
            args,
            kwargs,
        ) in self._awaits, (
            f"Expected at least one await with {args} and {kwargs}."
        )

    def assert_has_awaits(self, awaits, any_order=False):
        """
        Assert the mock has been awaited with the specified awaits.

        If any_order is false then the awaits must be sequential.

        If any_order is true then the awaits can be in any order, but they must
        all appear in await_args_list.
        """
        assert len(awaits) <= len(
            self._awaits
        ), f"Expected {len(awaits)} await[s], got {len(self._awaits)}."
        if any_order:
            for awaited in awaits:
                assert (
                    awaited in self._awaits
                ), f"Expected {awaited} in {self._awaits}."
        else:
            for i, awaited in enumerate(awaits):
                assert (
                    self._awaits[i] == awaited
                ), f"Expected {awaited} at index {i}, got {self._awaits[i]}."

    def assert_not_awaited(self):
        """
        Assert that the mock object was never awaited.
        """
        assert (
            self.await_count == 0
        ), f"Expected no awaits, got {self.await_count}."

    async def __call__(self, *args, **kwargs):
        """
        Record the await and return the specified result. Awaits on the mock
        object are recorded in the self._awaits list. Each await is a tuple in
        the form: (args, kwargs).

        In order of precedence, the return value is determined as follows:

        If a side_effect is specified then that is used to determine the
        return value. If a return_value is specified then that is used. If
        neither are specified then the same AsyncMock object is returned each
        time.
        """
        self._awaits.append((args, kwargs))
        if "side_effect" in self.__dict__:
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
                new_mock = AsyncMock()
                self._mock_value = new_mock
                return new_mock

    def __getattr__(self, name):
        """
        Retrieve the value of the attribute `name` if it exists in the
        instance's dictionary. If the attribute does not exist, a new
        `AsyncMock` object is created, assigned to the attribute, and returned.

        Raises an AttributeError if the attribute does not exist and the
        instance has a `_spec` attribute that does not contain the attribute
        name.
        """
        if name.startswith("_") or name in _RESERVED_MOCK_ATTRIBUTES:
            # Special attributes are handled as normal attributes.
            return self.__dict__.get(name)
        elif name in self.__dict__:
            # Existing attributes are returned as is.
            return self.__dict__[name]
        elif "_spec" in self.__dict__ and name not in self._spec:
            # If the attribute is not in the spec then raise an AttributeError.
            raise AttributeError(
                f"AsyncMock object has no attribute '{name}'."
            )
        else:
            # Otherwise, create a new mock object for the attribute.
            new_mock = AsyncMock()
            setattr(self, name, new_mock)
            return new_mock


class patch:
    """
    patch() acts as a function decorator or a context manager. Inside the body
    of the function or with statement, the target is patched with a new object.
    When the function/with statement exits the patch is undone.
    """

    def __init__(self, target, new=None, **kwargs):
        """
        Create a new patch object that will replace the target with new.

        The target should be in the form (note the colon ":"):

        "module.submodule:object_name.method_name"

        If no new object is provided, a new Mock object is created with the
        supplied kwargs.
        """
        self.target = target
        self.new = new
        self.kwargs = kwargs

    def __call__(self, func, *args, **kwargs):
        """
        Decorate a function with the patch class, and calling the wrapped
        function with the resulting mock object.
        """

        def wrapper(*args, **kwargs):
            with patch(self.target, self.new, **self.kwargs) as new:
                # Ensure the resulting mock object is passed to the function.
                args = args + (new,)
                return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        """
        Replace the target attribute with self.new.

        If self.new is None, a new Mock object is created with the supplied
        kwargs and bound to self.new before the target is replaced.
        """
        self.new = self.new or Mock(**self.kwargs)
        self._old = patch_target(self.target, self.new)
        return self.new

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Restore the target attribute to its original state.
        """
        patch_target(self.target, self._old)
        return False


def patch_target(target, replacement):
    """
    Patch the referenced target path, with the given replacement. Return
    the original object that was replaced.

    The target should be in the form (note the colon ":"):

    "module.submodule:object_name.method_name"
    """
    if ":" not in target:
        # No colon in the target, so assume the target is just a module.
        if target in sys.modules:
            old_module = sys.modules[target]
        else:
            old_module = import_module(target)
        sys.modules[target] = replacement
        return old_module
    # There IS a colon in the target, so split the target into module and
    # attribute parts.
    module_name, attributes = target.split(":")
    # The target_name is the attribute we eventually want to replace.
    target_name = attributes.rsplit(".", 1)[-1]
    # Get the parent module of the target.
    parent = sys.modules.get(module_name)
    if not parent:
        parent = import_module(module_name)
    # Traverse the module path to get the parent object of the target.
    parts = attributes.split(".")
    for part in parts[:-1]:
        parent = getattr(parent, part)
    # Get the original target object that we're going to replace (so we can
    # return it).
    old_object = getattr(parent, target_name)
    # Replace the target with the replacement.
    setattr(parent, target_name, replacement)
    return old_object
