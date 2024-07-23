# uMock (MicroMock) 🔬🥸

MicroMock is a very simple and small module for mocking objects in MicroPython
with PyScript.

It currently only implements relatively naive versions of the following
features inspired by the `unittest.mock` module in the CPython standard
library.

* A simplified `Mock` class to replace synchronous objects in Python.
* A simplified `AsyncMock` class to replace `await`-able objects in Python.
* A `patch` decorator / context manager to replace a target for the lifetime
  of the decorated function / context manager.

## Usage

**This module is for use with MicroPython within PyScript.**

### Setup

1. Ensure the `umock.py` file is in your Python path. You may need to copy this
   over using the 
   [files settings](https://docs.pyscript.net/2024.7.1/user-guide/configuration/#files).
   You should probably ensure use of [uPyTest](https://github.com/ntoll/upytest)
   by copying over the `upytest.py` file into your Python path.
   (See the `config.json` file in this repository for an example of this in
   action.)
2. Create your tests that use mocks / patching, as described below.
3. Ensure you have your tests setup properly as per the instruction in the
   [upytest README](https://github.com/ntoll/upytest?tab=readme-ov-file#setup).
4. In your `index.html` make sure you use the `async` and `terminal` attributes
   referencing your MicroPython script (as in the `index.html` file in this
   repository):

   ```
   <script type="mpy" src="./main.py" config="./config.json" terminal async></script>
   ```

Now point your browser at the `index.html` and you should see the test suite,
including your mocks and patches, run.

### Mocking

In code, a mock is simply something that imitates something else. Furthermore,
mock objects often record their interactions with other aspects of the code so
you're able to observe and "spy" on the behaviour of your code, and perhaps
even check expected behaviours are occuring.

Such objects are used in test situations when necessary objects are perhaps
very complicated to set up, or you only wish to test isolated code in a highly
constrained context without having to configure a complicated test setting.

For example, you may wish to mock away a database connection so the mock
emulates a real database connection without the need for an expensive or
complicated to configure database. All other aspects of the code under test
remain the same.

However, when using mocks, there is a danger you may mock away the universe and
the resulting context in which your test code is run doesn't accurately bear
any resemblance to the real world.

With this context in mind, the `Mock` class provided by uMock is inspired by
(but not the same as) Python's own unittest.mock.Mock class.

The main differences between this `Mock` class and Python's `unittest.mock.Mock`
class include:

* Instantiation of the object only allows use of the `spec`, `side_effect` and
  `return_value` keyword arguments (no `name`, `spec_set`, `wraps` or `unsafe`
  arguments). However, arbitrary keyword arguments can be passed to become
  attributes on the resulting mock object.
* Calls are recorded in a list of tuples in the form `(args, kwargs)` rather
  than a list of special `Call` instance objects.
* Mock objects do NOT record nor reveal call information relating to thier
  child mock objects (i.e. calls are not propagated to parent mocks).
* None of the following methods exist in this implementation:
  `mock_add_spec`, `attach_mock`, `configure_mock`, `_get_child_mock`,
  `method_calls`, `mock_calls`.

The `Mock` class takes several optional arguments that specify the behaviour of
the Mock object:

* `spec`: This can be either a list of strings or an existing object (a
  class or instance) that acts as the specification for the mock
  object. If you pass in an object then a list of strings is formed by
  calling dir on the object (excluding unsupported magic attributes and
  methods). Accessing any attribute not in this list will raise an
  `AttributeError`.

  If `spec` is an object (rather than a list of strings) then `__class__`
  returns the class of the `spec` object. This allows mocks to pass
  `isinstance()` tests.
* `side_effect`: A function to be called whenever the Mock is called.
  Useful for raising exceptions or dynamically changing return values.
  The function is called with the same arguments as the mock, and the
  return value of this function is used as the mock's return value.

  Alternatively `side_effect` can be an exception class or instance. In
  this case the exception will be raised when the mock is called.

  If `side_effect` is an iterable then each call to the mock will return
  the next value from the iterable.

  A `side_effect` can be cleared by setting it to `None`.
* `return_value`: The value returned when the mock is called. By default
  this is a new Mock (created on first access).

The resulting mock object has the following properties:

* `call_count`: the number of calls made to the mock object.
* `called`: `True` if the mock object was called at least once.
* `call_args`: the arguments of the last call to the mock object.
* `call_args_list`: a list of the arguments of each call to the mock object.

The mock object also has the following methods:

* `reset_mock()`: reset the mock object to a clean state. This is useful for when
  you want to reuse a mock object.
* `assert_called()`: assert that the mock object was called at least once.
* `assert_called_once()`: assert that the mock object was called once.
* `assert_called_with(*args, **kwargs)`: assert that the mock object was last
  called in a particular way.
* `assert_called_once_with(*args, **kwargs)`: assert that the mock object was 
  called once with the given arguments.
* `assert_any_call(*args, **kwargs)`: assert that the mock object was called at 
  least once with the given arguments.
* `assert_has_calls(calls, any_order=False)`: assert the mock has been called
  with the specified `calls`. If any_order is `False` then the calls must be 
  sequential. If any_order is `False`` then the calls can be in any order, but
  they must all appear in mock_calls.
* `assert_never_called()`: assert that the mock object was never called.

As a result, given a mock object it is possible to call it, have it behave in
a specified manner, and interrogate it about how it has been used:

```python
from umock import Mock


m = Mock(return_value=42)

meaning_of_life = m()

assert meaning_of_life == 42, "Meaning of life is not H2G2 compliant."
m.assert_called_once()
```

### Patching

The `patch` class acts as a function decorator or a context manager. Inside the
body of the function or `with` statement, the target is patched with a new
object. When the function/with statement exits the patch is undone.

The `patch` must always have a target argument that identifies the Python
object to replace. This string much be of the form:

`"module.submodule:object_name.method_name"`

(Note the colon ":"!)

If no `new` object is provided as the optional second argument, then a new Mock
object is created with the supplied `kwargs`.

If the `patch` class is being used as a decorator for a function, it will pass
in the resulting Mock object as the function's argument.

```python
from umock import patch


@patch("tests.a_package.a_module:a_function", return_value=42)
def test(mock_object):
    from tests.a_package.a_module import a_function

    assert mock_object is a_function, "Wrong object patched."
    assert (
        a_function(1, 2) == 42
    ), "Wrong return value from patched object."
```

Alternatively, if the `patch` class can used as a context manager.

```python
from umock import patch, Mock


mock_function = Mock(return_value=42)

with patch("tests.a_package.a_module:a_function", mock_function) as mock_object:
    assert mock_object is mock_function, "Wrong replacement object."
    from tests.a_package.a_module import a_function

    assert (
        a_function(1, 2) == 42
    ), "Wrong return value from patched object."

mock_function.assert_called_once_with(1, 2)
```

## Developer setup

This is easy:

1. Clone the project.
2. Start a local web server: `python -m http.server`
3. Point your browser at http://localhost:8000/
4. Change code and refresh your browser to check your changes.
5. **DO NOT CREATE A NEW FEATURE WITHOUT FIRST CREATING AN ISSUE FOR IT IN WHICH
   YOU PROPOSE YOUR CHANGE**. (We want to avoid a situation where you work hard
   on something that is ultimately rejected by the maintainers.)
6. Given all the above, pull requests are welcome and greatly appreciated.

We expect all contributors to abide by the spirit of our
[code of conduct](./CODE_OF_CONDUCT.md).

## Testing uMock

See the content of the `tests` directory in this repository. To run the test
suite, just follow steps 1, 2 and 3 in the developer setup section.

We use the [uPyTest](https://github.com/ntoll/upytest) to run our test suite.

## License

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