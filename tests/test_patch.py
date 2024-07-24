"""
Tests the patch decorator/context manager.
"""

import sys
from umock import patch, Mock


def test_patch_decorator_with_kwargs():
    """
    Tests the patch class functioning as a decorator.

    The target path is a dotted string with a colon, pointing to a function in
    the module. Ensure this is patched with the expected replacement.

    The kwarg arguments passed to the decorator are passed to the
    resulting mock object.
    """

    @patch("tests.a_package.a_module:a_function", return_value=42)
    def test(mock_object):
        from tests.a_package.a_module import a_function

        assert mock_object is a_function, "Wrong object patched."
        assert (
            a_function(1, 2) == 42
        ), "Wrong return value from patched object."

    test()

    # The context manager inside patch should have restored the original
    # object.
    from tests.a_package.a_module import a_function

    assert a_function(1, 2) == 3, "Patched object was not restored."


def test_patch_decorator_with_replacement():
    """
    Tests the patch class functioning as a decorator.

    The target path is a dotted string with a colon, pointing to a function in
    the module. Ensure this is patched with the expected replacement.

    The replacement is the second argument to the decorator.
    """

    mock_function = Mock(return_value=42)

    @patch("tests.a_package.a_module:a_function", mock_function)
    def test(mock_object):
        assert mock_object is mock_function, "Wrong replacement object."
        from tests.a_package.a_module import a_function

        assert (
            a_function(1, 2) == 42
        ), "Wrong return value from patched object."

    test()
    mock_function.assert_called_once_with(1, 2)


def test_patch_context_manager_with_kwargs():
    """
    Tests the patch class functioning as a context manager.

    The target path is a dotted string with a colon, pointing to a function in
    the module. Ensure this is patched with the expected replacement.

    The kwarg arguments passed to the context manager are passed to the
    resulting mock object.
    """

    with patch(
        "tests.a_package.a_module:a_function", return_value=42
    ) as mock_object:
        from tests.a_package.a_module import a_function

        assert mock_object is a_function, "Wrong object patched."
        assert (
            a_function(1, 2) == 42
        ), "Wrong return value from patched object."

    # The context manager should have restored the original object.
    from tests.a_package.a_module import a_function

    assert a_function(1, 2) == 3, "Patched object was not restored."


def test_patch_context_manager_with_replacement():
    """
    Tests the patch class functioning as a context manager.

    The target path is a dotted string with a colon, pointing to a function in
    the module. Ensure this is patched with the expected replacement.

    The replacement is the second argument to the context manager.
    """

    mock_function = Mock(return_value=42)

    with patch(
        "tests.a_package.a_module:a_function", mock_function
    ) as mock_object:
        assert mock_object is mock_function, "Wrong replacement object."
        from tests.a_package.a_module import a_function

        assert (
            a_function(1, 2) == 42
        ), "Wrong return value from patched object."

    mock_function.assert_called_once_with(1, 2)
    # The context manager should have restored the original object.
    from tests.a_package.a_module import a_function

    assert a_function(1, 2) == 3, "Patched object was not restored."
